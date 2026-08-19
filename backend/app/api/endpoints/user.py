import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_async
from app.api.req_util import resolve_client_ip
from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.oauth_client import OAuthClient
from app.models.oauth_token import OAuthToken
from app.models.user import User
from app.models.channel import Channel
from app.models.product import Product
from app.schemas.channel import ChannelBindRequest, ChannelBindResponse
from app.schemas.loan import LoanResponse
from app.schemas.user import (
    ApplicationSubmitRequest,
    ChangePasswordRequest,
    UserLocationUpsertRequest,
    UserResponse,
)
from app.services.audit import log_user_event_async
from app.services.blacklist_service import refresh_user_blacklist_status
from app.services.channel_service import bind_user_source_channel_async, get_channel_by_name_async
from app.services.esign_identity import ESignIdentityError, esign_identity_client
from app.services.ghana_identity import GhanaIdentityError, ghana_card_identity_provider
from app.services.login_location_risk import apply_login_location
from app.services.loan_amounts import DEFAULT_FEE_RATE, serialize_loan_snapshot, round_money
from app.services.loan_flow import (
    create_init_loan_async,
    get_latest_loan_async,
    get_or_create_loan_async,
    resolve_borrower_type,
)
from app.services.loan_ws_notify import notify_loan_snapshot_changed
from app.services.admin_service import notify_admin_stats_changed
from app.services.loan_assignment import assign_review_admin_if_needed_async
from app.services.phone_binding import build_released_phone, close_active_phone_bindings, record_phone_binding
from app.services.risk_list_service import refresh_user_risk_list_status
from app.services.upload_storage import build_upload_url, save_user_image

router = APIRouter()


def apply_auto_review_product(loan, user: User, product: Product) -> float:
    """将自动审核选中的现金贷产品固化到授信订单。

    :param loan: 待审核贷款订单
    :param user: 借款用户
    :param product: 自动审核选中的现金贷产品
    :return: 固化后的名义授信额度
    """
    approved_amount = round_money(product.nominal_loan_amount or product.payment_amount or 0)
    if approved_amount <= 0:
        return 0
    upfront_fee_rate = float(product.upfront_fee_rate or 0)
    upfront_fee_amount = round_money(approved_amount * upfront_fee_rate)
    loan.status = "APPROVED"
    loan.approved_credit_limit = approved_amount
    loan.credit_limit = approved_amount
    loan.nominal_loan_amount = approved_amount
    loan.upfront_fee_amount = upfront_fee_amount
    loan.actual_disbursement_amount = round_money(max(approved_amount - upfront_fee_amount, 0))
    loan.total_repayment_amount_snapshot = approved_amount
    loan.fee_rate = upfront_fee_rate
    loan.fee_amount = upfront_fee_amount
    loan.term_days = product.term_days
    loan.product_term_days = product.term_days
    loan.interest_start_day = int(product.interest_start_day or 1)
    loan.repayment_due_day = int(product.repayment_due_day or product.term_days or 7)
    loan.installment_count = int(product.installment_count or 1)
    loan.installment_ratios_json = product.installment_ratios_json
    loan.fee_components_json = product.fee_components_json
    loan.daily_overdue_fee_snapshot = round_money(product.daily_overdue_fee)
    loan.product_id = product.id
    loan.product_type = product.product_type
    loan.product_name = product.name
    loan.product_total_price = approved_amount
    # 现金贷金额只使用现金贷专属字段，E卡字段仅为历史订单读取保留。
    loan.rights_price = 0
    loan.ecard_face_value = 0
    loan.approved_at = datetime.now()
    loan.review_note = "Automatic review passed by channel policy"
    user.approved_limit = int(approved_amount)
    user.available_credit_limit = approved_amount
    return approved_amount


async def _upsert_oauth_client(db: AsyncSession, client_id: str) -> None:
    client = (await db.execute(select(OAuthClient).where(OAuthClient.client_id == client_id))).scalar_one_or_none()
    if client is None:
        db.add(OAuthClient(client_id=client_id, client_name=client_id, is_active=True))
        return
    client.is_active = True
    client.updated_at = datetime.now()


async def _issue_takeover_token_pair(db: AsyncSession, *, user: User, client_id: str, now: datetime) -> dict:
    await db.execute(
        update(OAuthToken)
        .where(
            OAuthToken.phone == user.phone,
            OAuthToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    access_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_expires_at = now + access_delta
    refresh_expires_at = now + refresh_delta
    access_jti = uuid4().hex
    refresh_jti = uuid4().hex
    access_token = create_access_token(
        subject=user.phone,
        expires_delta=access_delta,
        jti=access_jti,
        client_id=client_id,
    )
    refresh_token = create_refresh_token(
        subject=user.phone,
        expires_delta=refresh_delta,
        jti=refresh_jti,
        client_id=client_id,
    )
    await _upsert_oauth_client(db, client_id)
    db.add(
        OAuthToken(
            user_id=user.id,
            phone=user.phone,
            client_id=client_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_token_expires_at": access_expires_at,
        "refresh_token_expires_at": refresh_expires_at,
    }


def _build_user_response(user: User, **extra) -> dict:
    return {
        "id": user.id,
        "phone": user.phone,
        "name": user.name,
        "id_card_num": user.id_card_num,
        "id_address": user.id_address,
        "id_expiry": user.id_expiry,
        "id_card_front_image_url": build_upload_url(getattr(user, "id_card_front_image", None)),
        "id_card_back_image_url": build_upload_url(getattr(user, "id_card_back_image", None)),
        "face_image_url": build_upload_url(getattr(user, "face_image", None)),
        "approved_limit": user.approved_limit,
        "available_credit_limit": getattr(user, "available_credit_limit", 0) or 0,
        "overdue_credit_locked": bool(getattr(user, "overdue_credit_locked", False)),
        "emergency_contact1_name": user.emergency_contact1_name,
        "emergency_contact1_relation": user.emergency_contact1_relation,
        "emergency_contact1_phone": user.emergency_contact1_phone,
        "emergency_contact2_name": user.emergency_contact2_name,
        "emergency_contact2_relation": user.emergency_contact2_relation,
        "emergency_contact2_phone": user.emergency_contact2_phone,
        "location_latitude": user.location_latitude,
        "location_longitude": user.location_longitude,
        "location_accuracy": user.location_accuracy,
        "location_address": user.location_address,
        "location_province": user.location_province,
        "location_city": user.location_city,
        "location_district": user.location_district,
        "location_street": user.location_street,
        "location_source": user.location_source,
        "location_updated_at": user.location_updated_at,
        "location_risk_blocked": bool(getattr(user, "location_risk_blocked", False)),
        "location_risk_reason": getattr(user, "location_risk_reason", None),
        "location_risk_at": getattr(user, "location_risk_at", None),
        "risk_list_hit": bool(getattr(user, "risk_list_hit", False)),
        "risk_list_source": getattr(user, "risk_list_source", None),
        "risk_list_reason": getattr(user, "risk_list_reason", None),
        "risk_list_checked_at": getattr(user, "risk_list_checked_at", None),
        "face_auth_status": user.face_auth_status,
        "real_name_status": user.real_name_status,
        "face_auth_at": user.face_auth_at,
        "last_login_at": user.last_login_at,
        "ocr_submitted_at": user.ocr_submitted_at,
        "application_submitted_at": user.application_submitted_at,
        "source_channel_name": getattr(getattr(user, "source_channel", None), "channel_name", None),
        "source_channel_sales_name": getattr(getattr(user, "source_channel", None), "sales_name", None),
        "channel_bound_at": user.channel_bound_at,
        "last_channel_visit_at": user.last_channel_visit_at,
        "created_at": user.created_at,
        **extra,
    }


@router.get("/info", response_model=UserResponse)
async def get_user_info(current_user: User = Depends(get_current_user_async)):
    return current_user


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """修改当前登录用户密码。

    :param req: 修改密码请求体
    :param current_user: 当前登录用户
    :param db: 异步数据库会话
    :return: 修改结果
    """
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")

    if not current_user.password_hash or not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")

    # 修改密码后立即更新哈希，避免明文在内存中长时间停留。
    current_user.password_hash = get_password_hash(req.new_password)
    await db.commit()
    return {"msg": "密码修改成功"}


@router.post("/channel-bind", response_model=ChannelBindResponse)
async def bind_channel(
    req: ChannelBindRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    channel = await get_channel_by_name_async(db, req.channel_name, active_only=True)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道链接不存在或已停用")

    loan = await get_or_create_loan_async(db, current_user.id)
    attribution_status = await bind_user_source_channel_async(db, user=db_user, channel=channel, loan=loan)
    await db.commit()
    await db.refresh(db_user)

    bound_channel = db_user.source_channel
    if attribution_status == "BOUND":
        msg = f"已绑定专属渠道 {channel.sales_name}"
    elif attribution_status == "REFRESHED":
        msg = f"已识别专属渠道 {channel.sales_name}"
    else:
        msg = (
            f"当前账号已归属 {bound_channel.sales_name}（{bound_channel.channel_name}），"
            "本次不覆盖原渠道。"
        )
    return {
        "msg": msg,
        "source_channel_name": bound_channel.channel_name if bound_channel else None,
        "source_channel_sales_name": bound_channel.sales_name if bound_channel else None,
    }


@router.post("/ocr", response_model=UserResponse)
async def mock_ocr(
    request: Request,
    front_image: UploadFile = File(None),
    back_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    if not front_image:
        raise HTTPException(status_code=400, detail="请上传身份证人像面。")

    front_bytes = await front_image.read()
    back_bytes = await back_image.read() if back_image else None

    if settings.GHANA_IDENTITY_ENABLED or settings.GHANA_IDENTITY_MOCK_ENABLED:
        try:
            ocr_result = await ghana_card_identity_provider.ocr(front_bytes, back_bytes)
        except GhanaIdentityError as exc:
            raise HTTPException(status_code=400, detail=f"Ghana Card verification failed: {exc}") from exc
        ocr_name = (ocr_result.get("name") or "").strip()
        ocr_id_card_num = (ocr_result.get("id_card_num") or "").strip()
        ocr_id_address = (ocr_result.get("id_address") or "").strip()
        ocr_id_expiry = (ocr_result.get("id_expiry") or "").strip()
    elif settings.ESIGN_IDENTITY_ENABLED:
        try:
            ocr_result = await esign_identity_client.id_card_ocr(front_bytes, back_bytes)
        except ESignIdentityError as exc:
            raise HTTPException(status_code=400, detail=f"身份证识别失败：{exc}") from exc
        ocr_name = (ocr_result.get("name") or "").strip()
        ocr_id_card_num = (ocr_result.get("id_card_num") or "").strip()
        ocr_id_address = (ocr_result.get("id_address") or "").strip()
        ocr_id_expiry = (ocr_result.get("id_expiry") or "").strip()
    elif settings.ESIGN_IDENTITY_MOCK_ENABLED:
        await asyncio.sleep(0.8)
        id_suffix = current_user.phone[-4:] if current_user.phone else "1234"
        ocr_name = "Ama Mensah"
        ocr_id_card_num = f"GHA-000000{id_suffix}-0"
        ocr_id_address = "Accra, Ghana"
        ocr_id_expiry = "2025.01.01-2035.01.01"
    else:
        raise HTTPException(status_code=503, detail="实名识别服务未启用，请联系管理员。")

    now = datetime.now()
    active_user = current_user
    token_payload = None
    previous_user_id = None
    phone_reclaimed = False
    login_phone = current_user.phone
    normalized_current_id = (current_user.id_card_num or "").strip()
    normalized_ocr_id = (ocr_id_card_num or "").strip()

    target_user = None
    if normalized_ocr_id:
        target_user = (
            await db.execute(select(User).where(User.id_card_num == normalized_ocr_id))
        ).scalar_one_or_none()

    should_takeover_by_realname = (
        target_user is not None
        and target_user.id != current_user.id
        and normalized_current_id != normalized_ocr_id
    )
    should_split_current_identity = (
        target_user is None
        and normalized_current_id
        and normalized_ocr_id
        and normalized_current_id != normalized_ocr_id
    )

    if should_takeover_by_realname or should_split_current_identity:
        previous_user_id = current_user.id
        if target_user is None:
            target_user = User(
                phone=await build_released_phone(db, phone=login_phone, user_id=current_user.id),
                created_at=now,
            )
            db.add(target_user)
            await db.flush()

        released_phone = await build_released_phone(db, phone=login_phone, user_id=current_user.id)
        await close_active_phone_bindings(
            db,
            phone=login_phone,
            note=f"手机号由用户#{current_user.id}释放给实名用户#{target_user.id}",
        )
        current_user.phone = released_phone
        await db.flush()
        if target_user.phone and target_user.phone != login_phone:
            await close_active_phone_bindings(
                db,
                phone=target_user.phone,
                note=f"用户#{target_user.id}切换绑定手机号 {login_phone}",
            )
        target_user.phone = login_phone
        target_user.password_hash = None
        target_user.last_login_at = now
        await record_phone_binding(
            db,
            user=target_user,
            phone=login_phone,
            bind_type="REALNAME_RECLAIM",
            note=f"手机号实名接管；原用户#{current_user.id}",
        )
        active_user = target_user
        phone_reclaimed = True

        await log_user_event_async(
            db,
            user=current_user,
            loan=None,
            actor_type="SYSTEM",
            event_type="PHONE_RELEASED",
            title="手机号已被实名本人接管",
            detail=f"手机号 {login_phone} 已由新实名用户#{target_user.id}接管，历史业务保留在当前档案。",
        )

    active_user.name = ocr_name
    active_user.id_card_num = ocr_id_card_num
    active_user.id_address = ocr_id_address
    active_user.id_expiry = ocr_id_expiry
    active_user.id_card_front_image = save_user_image(active_user.id, front_bytes, prefix="id-front", content_type=front_image.content_type)
    if back_bytes:
        active_user.id_card_back_image = save_user_image(active_user.id, back_bytes, prefix="id-back", content_type=back_image.content_type if back_image else None)
    active_user.ocr_submitted_at = now

    hit = await refresh_user_blacklist_status(db, active_user)
    await refresh_user_risk_list_status(db, active_user)
    if hit:
        await db.commit()
        raise HTTPException(status_code=400, detail="抱歉 您当前无法申请信用购物额度")

    loan = await get_or_create_loan_async(db, active_user.id)
    loan.identity_ocr_submitted_at = now
    await log_user_event_async(
        db,
        user=active_user,
        loan=loan,
        event_type="OCR_SUBMIT",
        title="Submit Ghana Card verification",
        detail={
            "Ghana Card front": "uploaded" if front_image else "missing",
            "Ghana Card back": "uploaded" if back_image else "not provided",
            "Recognized name": active_user.name,
            "Ghana Card number": active_user.id_card_num,
            "Residential address": active_user.id_address,
            "Expiry date": active_user.id_expiry,
            "Recognition method": "Ghana Card provider" if (settings.GHANA_IDENTITY_ENABLED or settings.GHANA_IDENTITY_MOCK_ENABLED) else "Legacy eSign provider",
            "Phone takeover": "yes" if phone_reclaimed else "no",
        },
    )

    try:
        if phone_reclaimed:
            token_payload = await _issue_takeover_token_pair(
                db,
                user=active_user,
                client_id=request.headers.get("client-id", "h5-web").strip() or "h5-web",
                now=now,
            )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        message = str(getattr(exc.orig, "args", [""])[-1] or exc)
        if "Duplicate entry" in message and "users.id_card_num" in message:
            raise HTTPException(status_code=400, detail="该身份证号已被其他账号使用，请核对后重试。") from exc
        raise HTTPException(status_code=500, detail="实名信息保存失败，请稍后重试。") from exc

    await db.refresh(active_user)
    return _build_user_response(
        active_user,
        phone_reclaimed=phone_reclaimed,
        previous_user_id=previous_user_id,
        **(token_payload or {}),
    )


@router.post("/face-auth")
async def mock_face_auth(
    face_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    if not current_user.name or not current_user.id_card_num:
        raise HTTPException(status_code=400, detail="请先完成身份证识别并确认实名信息。")

    score = None
    if settings.GHANA_IDENTITY_ENABLED or settings.GHANA_IDENTITY_MOCK_ENABLED:
        if not face_image:
            raise HTTPException(status_code=400, detail="Please upload a face photo.")

        face_image_bytes = await face_image.read()
        try:
            compare_result = await ghana_card_identity_provider.face_compare(
                name=current_user.name,
                ghana_card_number=current_user.id_card_num,
                face_image_bytes=face_image_bytes,
            )
            score = compare_result.get("score")
        except GhanaIdentityError as exc:
            fail_detail = str(exc).strip()
            loan = await get_or_create_loan_async(db, current_user.id)
            await log_user_event_async(
                db,
                user=current_user,
                loan=loan,
                event_type="FACE_AUTH_FAIL",
                title="Ghana Card face comparison failed",
                detail={
                    "verification_method": "Ghana Card face comparison",
                    "failure_reason": fail_detail,
                },
            )
            await db.commit()
            raise HTTPException(status_code=400, detail=fail_detail) from exc
    elif settings.ESIGN_IDENTITY_ENABLED:
        if not face_image:
            raise HTTPException(status_code=400, detail="请上传人脸照片。")

        face_image_bytes = await face_image.read()
        try:
            compare_result = await esign_identity_client.face_compare(
                name=current_user.name,
                id_card_num=current_user.id_card_num,
                face_image_bytes=face_image_bytes,
            )
            score = compare_result.get("score")
        except ESignIdentityError as exc:
            fail_detail = str(exc).strip()
            mismatch_message = "人脸识别信息与身份证信息不符，请重新尝试认证。"
            if "不符" in fail_detail or "不匹配" in fail_detail or "未通过" in fail_detail:
                fail_detail = mismatch_message
            loan = await get_or_create_loan_async(db, current_user.id)
            await log_user_event_async(
                db,
                user=current_user,
                loan=loan,
                event_type="FACE_AUTH_FAIL",
                title="人脸识别未通过",
                detail={
                    "verification_method": "Legacy eSign face comparison",
                    "failure_reason": fail_detail,
                },
            )
            await db.commit()
            raise HTTPException(status_code=400, detail=fail_detail) from exc
    elif settings.ESIGN_IDENTITY_MOCK_ENABLED:
        await asyncio.sleep(1.0)
        face_image_bytes = await face_image.read() if face_image else b""
        score = 0.99
    else:
        raise HTTPException(status_code=503, detail="人脸核验服务未启用，请联系管理员。")

    if face_image_bytes:
        current_user.face_image = save_user_image(current_user.id, face_image_bytes, prefix="face", content_type=face_image.content_type if face_image else None)
    current_user.face_auth_status = "PASSED"
    current_user.real_name_status = "AUTHED"
    current_user.face_auth_at = datetime.now()

    loan = await get_or_create_loan_async(db, current_user.id)
    loan.identity_face_auth_at = current_user.face_auth_at
    await log_user_event_async(
        db,
        user=current_user,
        loan=loan,
        event_type="FACE_AUTH_PASS",
        title="完成人脸识别",
        detail={
            "verification_method": "Ghana Card face comparison" if (settings.GHANA_IDENTITY_ENABLED or settings.GHANA_IDENTITY_MOCK_ENABLED) else "Legacy eSign face comparison",
            "verification_result": "passed",
            "verification_score": score,
        },
    )

    await db.commit()
    return {"msg": "人脸认证及三要素校验成功", "score": score}


@router.post("/application", response_model=LoanResponse)
async def submit_application(
    req: ApplicationSubmitRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    hit = await refresh_user_blacklist_status(db, db_user)
    await refresh_user_risk_list_status(db, db_user)
    if hit:
        await db.commit()
        raise HTTPException(status_code=400, detail="抱歉 您当前无法申请信用购物额度")
    is_resubmitting = False
    contacts = req.emergency_contacts
    if len(contacts) != 2:
        raise HTTPException(status_code=400, detail="请完整填写两位紧急联系人")
    if contacts[0].phone == contacts[1].phone:
        raise HTTPException(status_code=400, detail="两位紧急联系人手机号不能相同")

    loan = await get_latest_loan_async(db, current_user.id)
    if loan is None or loan.status == "SETTLED":
        loan = await create_init_loan_async(db, current_user.id)
    elif loan.status == "REVIEWING":
        is_resubmitting = True
    elif loan.status == "REJECTED":
        raise HTTPException(status_code=400, detail="很遗憾，您当前未通过审核")
    elif loan.status in {"APPROVED", "WITHDRAWING", "DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="当前订单流程进行中，暂不能重复提交资料")

    if not getattr(loan, "identity_ocr_submitted_at", None):
        raise HTTPException(status_code=400, detail="请先重新提交身份证正反面照片。")
    if not getattr(loan, "identity_face_auth_at", None):
        raise HTTPException(status_code=400, detail="请先重新完成人脸识别。")

    db_user.emergency_contact1_name = contacts[0].name.strip()
    db_user.emergency_contact1_relation = contacts[0].relation.strip()
    db_user.emergency_contact1_phone = contacts[0].phone.strip()
    db_user.emergency_contact2_name = contacts[1].name.strip()
    db_user.emergency_contact2_relation = contacts[1].relation.strip()
    db_user.emergency_contact2_phone = contacts[1].phone.strip()
    db_user.application_submitted_at = datetime.now()
    db_user.approved_limit = 0
    db_user.available_credit_limit = 0

    loan.status = "REVIEWING"
    loan.credit_limit = 0
    loan.approved_credit_limit = 0
    loan.fee_rate = DEFAULT_FEE_RATE
    loan.fee_amount = 0
    loan.term_days = None
    loan.due_date = None
    loan.penalty_amount = 0
    loan.repaid_amount = 0
    loan.reduction_amount = 0
    loan.other_fee_amount = 0
    loan.paid_penalty_amount = 0
    loan.reduced_penalty_amount = 0
    loan.actual_repayment_date = None
    loan.review_note = None
    loan.approved_at = None
    loan.reminder_count = 0
    loan.last_reminded_at = None
    loan.collection_count = 0
    loan.last_collection_at = None
    loan.collection_note = None
    loan.collection_admin_id = None
    loan.collection_transferred_at = None
    loan.repay_attempt_count = 0
    loan.disbursed_at = None
    loan.product_id = None
    loan.product_name = None
    loan.rights_title = None
    loan.rights_desc = None
    loan.rights_contact_phone = None
    loan.rights_price = 0
    loan.ecard_face_value = 0
    loan.product_total_price = 0
    loan.product_term_days = None
    loan.ecard_account = None
    loan.ecard_password = None
    loan.ecard_expires_at = None
    loan.order_no = ""
    loan.created_at = db_user.application_submitted_at
    await assign_review_admin_if_needed_async(db, loan)

    source_channel = None
    if db_user.source_channel_id:
        source_channel = (await db.execute(select(Channel).where(Channel.id == db_user.source_channel_id))).scalar_one_or_none()
    if source_channel and getattr(source_channel, "review_mode", "MANUAL_REVIEW") == "AUTO_REVIEW":
        history = (await db.execute(select(Loan).where(Loan.user_id == current_user.id))).scalars().all()
        borrower_type = resolve_borrower_type(history)
        candidate_products = (
            await db.execute(
                select(Product)
                .where(Product.product_type == "CASH_LOAN", Product.is_active.is_(True))
                .order_by(Product.nominal_loan_amount.asc(), Product.id.asc())
            )
        ).scalars().all()
        candidate_products = [
            item for item in candidate_products
            if (getattr(item, "borrower_type", None) or "ALL") in {"ALL", borrower_type}
        ]
        if candidate_products and not db_user.blacklist_hit and not db_user.risk_list_hit:
            selected_product = candidate_products[0]
            approved_amount = apply_auto_review_product(loan, db_user, selected_product)
            if approved_amount > 0:
                await log_user_event_async(
                    db,
                    user=db_user,
                    loan=loan,
                    actor_type="SYSTEM",
                    event_type="AUTO_REVIEW_APPROVED",
                    title="自动审核通过",
                    detail=f"渠道 {source_channel.channel_name}；借款人类型 {borrower_type}；授信额度 {approved_amount:.2f}",
                )

    await log_user_event_async(
        db,
        user=db_user,
        loan=loan,
        event_type="APPLICATION_RESUBMIT" if is_resubmitting else "APPLICATION_SUBMIT",
        title="更新补充资料并继续审核" if is_resubmitting else "提交补充资料",
        detail={
            "联系人1": f"{db_user.emergency_contact1_name}/{db_user.emergency_contact1_relation}/{db_user.emergency_contact1_phone}",
            "联系人2": f"{db_user.emergency_contact2_name}/{db_user.emergency_contact2_relation}/{db_user.emergency_contact2_phone}",
        },
    )
    await db.commit()
    await db.refresh(loan)
    await notify_loan_snapshot_changed(current_user.id)
    await notify_admin_stats_changed()
    return serialize_loan_snapshot(loan)


@router.post("/location")
async def upsert_user_location(
    request: Request,
    req: UserLocationUpsertRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        await apply_login_location(
            db,
            current_user,
            latitude=req.latitude,
            longitude=req.longitude,
            accuracy=req.accuracy,
            fallback_ip=resolve_client_ip(request, default_ip=""),
        )
    except ValueError as exc:
        await db.commit()
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    await db.commit()
    return {
        "msg": "位置已更新",
        "location_updated_at": current_user.location_updated_at,
        "province": current_user.location_province,
        "city": current_user.location_city,
        "district": current_user.location_district,
        "street": current_user.location_street,
        "address": current_user.location_address,
    }
