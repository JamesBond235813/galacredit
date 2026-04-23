import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.channel import ChannelBindRequest, ChannelBindResponse
from app.schemas.loan import LoanResponse
from app.schemas.user import ApplicationSubmitRequest, UserLocationUpsertRequest, UserResponse
from app.services.audit import log_user_event
from app.services.channel_service import bind_user_source_channel, get_channel_by_name
from app.services.esign_identity import ESignIdentityError, esign_identity_client
from app.services.location import reverse_geocode
from app.services.loan_amounts import DEFAULT_FEE_RATE, serialize_loan_snapshot
from app.services.loan_flow import create_init_loan, get_or_create_loan, get_latest_loan
from app.services.loan_assignment import assign_review_admin_if_needed

router = APIRouter()


@router.get("/info", response_model=UserResponse)
def get_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/channel-bind", response_model=ChannelBindResponse)
def bind_channel(
    req: ChannelBindRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    channel = get_channel_by_name(db, req.channel_name, active_only=True)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道链接不存在或已停用")

    loan = get_or_create_loan(db, current_user.id)
    attribution_status = bind_user_source_channel(db, user=current_user, channel=channel, loan=loan)
    db.commit()
    db.refresh(current_user)

    bound_channel = current_user.source_channel
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
    front_image: UploadFile = File(None),
    back_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not front_image:
        raise HTTPException(status_code=400, detail="请上传身份证人像面。")

    front_bytes = await front_image.read()
    back_bytes = await back_image.read() if back_image else None

    if settings.ESIGN_IDENTITY_ENABLED:
        try:
            ocr_result = esign_identity_client.id_card_ocr(front_bytes, back_bytes)
        except ESignIdentityError as exc:
            raise HTTPException(status_code=400, detail=f"身份证识别失败：{exc}") from exc
        current_user.name = (ocr_result.get("name") or "").strip()
        current_user.id_card_num = (ocr_result.get("id_card_num") or "").strip()
        current_user.id_address = (ocr_result.get("id_address") or "").strip()
        current_user.id_expiry = (ocr_result.get("id_expiry") or "").strip()
    else:
        await asyncio.sleep(0.8)
        id_suffix = current_user.phone[-4:] if current_user.phone else "1234"
        current_user.name = "张三"
        current_user.id_card_num = f"11010119900101{id_suffix}"
        current_user.id_address = "北京市朝阳区建国路 88 号"
        current_user.id_expiry = "2020.01.01-2040.01.01"

    current_user.ocr_submitted_at = datetime.utcnow()

    loan = get_or_create_loan(db, current_user.id)
    log_user_event(
        db,
        user=current_user,
        loan=loan,
        event_type="OCR_SUBMIT",
        title="提交身份证识别",
        detail={
            "身份证正面": "已上传" if front_image else "未上传",
            "身份证反面": "已上传" if back_image else "未上传",
            "识别姓名": current_user.name,
            "身份证号": current_user.id_card_num,
            "住址": current_user.id_address,
            "有效期": current_user.id_expiry,
            "识别方式": "e签宝OCR" if settings.ESIGN_IDENTITY_ENABLED else "本地模拟",
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        message = str(getattr(exc.orig, "args", [""])[-1] or exc)
        if "Duplicate entry" in message and "users.id_card_num" in message:
            raise HTTPException(status_code=400, detail="该身份证号已被其他账号使用，请核对后重试。") from exc
        raise HTTPException(status_code=500, detail="实名信息保存失败，请稍后重试。") from exc

    db.refresh(current_user)
    return current_user


@router.post("/face-auth")
async def mock_face_auth(
    face_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.name or not current_user.id_card_num:
        raise HTTPException(status_code=400, detail="请先完成身份证识别并确认实名信息。")

    score = None
    if settings.ESIGN_IDENTITY_ENABLED:
        if not face_image:
            raise HTTPException(status_code=400, detail="请上传人脸照片。")

        face_image_bytes = await face_image.read()
        try:
            compare_result = esign_identity_client.face_compare(
                name=current_user.name,
                id_card_num=current_user.id_card_num,
                face_image_bytes=face_image_bytes,
            )
            score = compare_result.get("score")
        except ESignIdentityError as exc:
            fail_detail = str(exc).strip()
            mismatch_message = "人脸识别信息与身份证信息不符，请重新尝试借款。"
            if "不符" in fail_detail or "不匹配" in fail_detail or "未通过" in fail_detail:
                fail_detail = mismatch_message
            loan = get_or_create_loan(db, current_user.id)
            log_user_event(
                db,
                user=current_user,
                loan=loan,
                event_type="FACE_AUTH_FAIL",
                title="人脸识别未通过",
                detail={
                    "核验方式": "e签宝人脸核验",
                    "失败原因": fail_detail,
                },
            )
            db.commit()
            raise HTTPException(status_code=400, detail=fail_detail) from exc
    else:
        await asyncio.sleep(1.0)
        score = 0.99

    current_user.face_auth_status = "PASSED"
    current_user.face_auth_at = datetime.utcnow()

    loan = get_or_create_loan(db, current_user.id)
    log_user_event(
        db,
        user=current_user,
        loan=loan,
        event_type="FACE_AUTH_PASS",
        title="完成人脸识别",
        detail={
            "核验方式": "e签宝人脸核验" if settings.ESIGN_IDENTITY_ENABLED else "本地模拟",
            "核验结果": "通过",
            "核验分值": score,
        },
    )

    db.commit()
    return {"msg": "人脸认证及三要素校验成功", "score": score}


@router.post("/application", response_model=LoanResponse)
def submit_application(
    req: ApplicationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_resubmitting = False
    contacts = req.emergency_contacts
    if len(contacts) != 2:
        raise HTTPException(status_code=400, detail="请完整填写两位紧急联系人")

    if contacts[0].phone == contacts[1].phone:
        raise HTTPException(status_code=400, detail="两位紧急联系人手机号不能相同")

    loan = get_latest_loan(db, current_user.id)
    if loan is None:
        loan = create_init_loan(db, current_user.id)
    elif loan.status == "SETTLED":
        loan = create_init_loan(db, current_user.id)
    elif loan.status == "REVIEWING":
        is_resubmitting = True
    elif loan.status in {"APPROVED", "WITHDRAWING", "DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="当前订单流程进行中，暂不能重复提交资料")

    current_user.emergency_contact1_name = contacts[0].name.strip()
    current_user.emergency_contact1_relation = contacts[0].relation.strip()
    current_user.emergency_contact1_phone = contacts[0].phone.strip()
    current_user.emergency_contact2_name = contacts[1].name.strip()
    current_user.emergency_contact2_relation = contacts[1].relation.strip()
    current_user.emergency_contact2_phone = contacts[1].phone.strip()
    current_user.application_submitted_at = datetime.utcnow()
    current_user.approved_limit = 0

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
    loan.paid_penalty_amount = 0
    loan.reduced_penalty_amount = 0
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
    loan.rights_price = 0
    loan.ecard_face_value = 0
    loan.product_total_price = 0
    loan.product_term_days = None
    loan.ecard_account = None
    loan.ecard_password = None
    loan.ecard_expires_at = None
    loan.created_at = current_user.application_submitted_at
    assign_review_admin_if_needed(db, loan)

    log_user_event(
        db,
        user=current_user,
        loan=loan,
        event_type="APPLICATION_RESUBMIT" if is_resubmitting else "APPLICATION_SUBMIT",
        title="更新补充资料并继续审核" if is_resubmitting else "提交补充资料",
        detail={
            "联系人1": f"{current_user.emergency_contact1_name}/{current_user.emergency_contact1_relation}/{current_user.emergency_contact1_phone}",
            "联系人2": f"{current_user.emergency_contact2_name}/{current_user.emergency_contact2_relation}/{current_user.emergency_contact2_phone}",
        },
    )

    db.commit()
    db.refresh(loan)
    return serialize_loan_snapshot(loan)


@router.post("/location")
def upsert_user_location(
    req: UserLocationUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latitude = round(float(req.latitude), 7)
    longitude = round(float(req.longitude), 7)
    accuracy = None if req.accuracy is None else round(float(req.accuracy), 2)

    location = reverse_geocode(latitude=latitude, longitude=longitude)

    current_user.location_latitude = str(latitude)
    current_user.location_longitude = str(longitude)
    current_user.location_accuracy = str(accuracy) if accuracy is not None else None
    current_user.location_source = (req.source or "h5-geolocation").strip()[:30]
    current_user.location_address = location.get("address")
    current_user.location_province = location.get("province")
    current_user.location_city = location.get("city")
    current_user.location_district = location.get("district")
    current_user.location_street = location.get("street")
    current_user.location_updated_at = datetime.utcnow()

    loan = get_or_create_loan(db, current_user.id)
    log_user_event(
        db,
        user=current_user,
        loan=loan,
        event_type="LOCATION_UPDATE",
        title="更新位置信息",
        detail={
            "纬度": current_user.location_latitude,
            "经度": current_user.location_longitude,
            "精度米": current_user.location_accuracy,
            "省": current_user.location_province,
            "市": current_user.location_city,
            "区县": current_user.location_district,
            "街道": current_user.location_street,
            "地址": current_user.location_address,
            "来源": current_user.location_source,
        },
    )

    db.commit()
    return {
        "msg": "位置已更新",
        "location_updated_at": current_user.location_updated_at,
        "province": current_user.location_province,
        "city": current_user.location_city,
        "district": current_user.location_district,
        "street": current_user.location_street,
        "address": current_user.location_address,
    }
