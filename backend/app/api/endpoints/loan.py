import asyncio
import json
import logging
import random
import string
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_async, get_user_by_token_async
from app.api.req_util import resolve_client_ip
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_async_db
from app.core.trace import new_trace_id, reset_trace_id, set_trace_id
from app.models.loan import Loan
from app.models.channel import Channel
from app.models.loan_ecard import LoanEcard
from app.models.product import Product
from app.models.purchase_contract import PurchaseContractSignature
from app.models.loan_mandate import LoanMandate
from app.models.user import User
from app.schemas.loan import DisburseRequest, EcardSecretResponse, LoanOrderRequest, LoanOrderSmsCodeResponse, LoanResponse, ProductItemResponse, PurchaseContractPreviewRequest, PurchaseContractResponse
from app.services.audit import log_user_event_async
from app.services.approved_credit_expiry import expire_unused_approved_credit_for_loan
from app.services.blacklist_service import refresh_user_blacklist_status
from app.services.loan_amounts import serialize_loan_snapshot
from app.services.loan_assignment import assign_review_admin_if_needed_async
from app.services.loan_flow import create_init_loan_async, get_latest_loan_async, get_or_create_loan_async, resolve_borrower_type
from app.services.loan_ledger import sync_loan_repayment_state
from app.services.loan_ws_notify import notify_loan_snapshot_changed, wait_loan_snapshot_changed
from app.services.admin_service import _disburse_loan, notify_admin_stats_changed
from app.services.channel_service import normalize_channel_disbursement_mode
from app.services.purchase_contract import PARTY_A_LEGAL_PERSON, PARTY_A_NAME, build_contract_payload, generate_contract_no, serialize_purchase_contract
from app.services.risk_list_service import refresh_user_risk_list_status
from app.services.risk_decision import record_risk_decision_async
from app.services.sms_service import sms_service

router = APIRouter()
LOAN_STATUS_WS_PUSH_SECONDS = 30
ORDER_SMS_BIZ_TYPE = "ORDER"
request_logger = logging.getLogger("app.request")


def generate_order_no(now: Optional[datetime] = None) -> str:
    """生成订单号。

    :param now: 可选时间（用于测试）
    :return: 订单号
    """
    current = now or datetime.now()
    # 订单号规则：毫秒级时间戳 + 4位随机字母数字，保证可读且易追踪。
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{current.strftime('%Y%m%d%H%M%S%f')[:-3]}{suffix}"


def _is_rights_only_product(product: Product) -> bool:
    return getattr(product, "product_type", None) == "RIGHTS_ONLY"


def _is_regular_ecard_rights_loan(loan: Loan) -> bool:
    return float(getattr(loan, "ecard_face_value", 0) or 0) > 0 and float(getattr(loan, "rights_price", 0) or 0) > 0


async def _record_ecard_secret_copy(
    db: AsyncSession,
    *,
    user: User,
    loan: Loan,
    field: str,
    loan_ecard_id: Optional[int] = None,
    ecard_pool_id: Optional[int] = None,
    index: Optional[int] = None,
) -> None:
    """记录用户在H5端复制/查看E卡卡密的动作。

    :param db: 异步数据库会话
    :param user: 当前用户
    :param loan: 当前订单
    :param field: 复制字段，account 或 password
    :param loan_ecard_id: 订单E卡明细ID
    :param ecard_pool_id: 卡池记录ID
    :param index: 前端传入的卡片序号
    :return: None
    """
    await log_user_event_async(
        db,
        user=user,
        loan=loan,
        event_type="USER_ECARD_SECRET_COPIED",
        title="用户复制E卡卡密",
        detail=(
            f"field={field}；"
            f"loan_ecard_id={loan_ecard_id or ''}；"
            f"ecard_pool_id={ecard_pool_id or ''}；"
            f"index={index if index is not None else ''}"
        ),
    )
    await db.commit()


def _extract_product_contact_phone(product: Product) -> Optional[str]:
    """从商品权益配置中提取联系电话。

    :param product: 商品对象
    :return: 权益联系电话
    """
    if not getattr(product, "rights_detail_json", None):
        return None
    try:
        rights_detail = json.loads(product.rights_detail_json)
    except (TypeError, json.JSONDecodeError):
        return None
    contact_phone = str((rights_detail or {}).get("contact_phone") or "").strip()
    return contact_phone or None


async def _resolve_order_contract_context(
    db: AsyncSession,
    *,
    current_user: User,
    product_id: int,
    extension_source_loan_id: Optional[int] = None,
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    loan = await get_or_create_latest_loan(db, current_user.id)
    await expire_unused_approved_credit_for_loan(db, loan)
    source_loan = None
    if extension_source_loan_id:
        source_loan = (
            await db.execute(
                select(Loan)
                .where(
                    Loan.id == extension_source_loan_id,
                    Loan.user_id == current_user.id,
                    Loan.status.in_(["DISBURSED", "OVERDUE"]),
                )
            )
        ).scalar_one_or_none()
        if not source_loan:
            raise HTTPException(status_code=400, detail="未找到可展期的原账单")
        if not _is_regular_ecard_rights_loan(source_loan):
            raise HTTPException(status_code=400, detail="纯权益包只能用于已有常规订单的展期")
    elif loan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="当前状态不可下单")

    product = (
        await db.execute(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在或已下架")
    if source_loan and not _is_rights_only_product(product):
        raise HTTPException(status_code=400, detail="带息费展期只能下单纯权益包")
    if not source_loan and getattr(product, "product_type", None) == "CASH_LOAN":
        history = (await db.execute(select(Loan).where(Loan.user_id == current_user.id))).scalars().all()
        borrower_type = resolve_borrower_type(history)
        product_type = getattr(product, "borrower_type", None) or "ALL"
        if product_type not in {"ALL", borrower_type}:
            raise HTTPException(status_code=400, detail="当前贷款政策不适用于您的借款人类型")
    if not source_loan and _is_rights_only_product(product):
        raise HTTPException(status_code=400, detail="纯权益包只能用于已有常规订单的展期")
    return db_user, loan, source_loan, product


async def get_or_create_latest_loan(db: AsyncSession, user_id: int):
    latest_before = await get_latest_loan_async(db, user_id)
    latest_loan = latest_before or await get_or_create_loan_async(db, user_id)
    if latest_before is None:
        await db.commit()
        await db.refresh(latest_loan)
    return latest_loan


async def get_latest_loan_snapshot_async(db: AsyncSession, user_id: int) -> Loan:
    """获取用于返回快照的订单对象，并预加载账单相关关系。

    :param db: 异步数据库会话
    :param user_id: 用户ID
    :return: 预加载分期关系的订单对象
    """
    loan = await get_or_create_latest_loan(db, user_id)
    await expire_unused_approved_credit_for_loan(db, loan)
    # 这里强制预加载 installments，避免在序列化阶段触发异步懒加载导致 MissingGreenlet。
    snapshot_loan = (
        await db.execute(
            select(Loan)
            .options(selectinload(Loan.installments), selectinload(Loan.owner), selectinload(Loan.ecard_items))
            .where(Loan.id == loan.id)
        )
    )
    if hasattr(snapshot_loan, "scalar_one"):
        snapshot_loan = snapshot_loan.scalar_one()
    else:
        snapshot_loan = snapshot_loan.scalars().first()
    sync_loan_repayment_state(snapshot_loan)
    return snapshot_loan


async def _get_ws_user_by_token(db: AsyncSession, token: Optional[str]) -> Optional[User]:
    """通过 WebSocket Token 获取用户。

    :param db: 异步数据库会话
    :param token: token 字符串
    :return: 用户对象；token 非法或为空时返回 None
    """
    if not token:
        return None
    try:
        return await get_user_by_token_async(db, token)
    except HTTPException:
        return None


def _extract_ws_token(websocket: WebSocket) -> Optional[str]:
    """提取 WebSocket 连接中的用户 token。

    :param websocket: WebSocket 连接对象
    :return: token 字符串
    """
    query_token = websocket.query_params.get("token")
    if query_token:
        return query_token
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return None


def serialize_h5_loan_snapshot(loan: Loan, include_ledger: bool = False) -> dict:
    """序列化 H5 订单快照，并隐藏后台审批备注。

    :param loan: 订单对象
    :param include_ledger: 是否包含账单流水快照
    :return: H5 可见的订单快照
    """
    payload = serialize_loan_snapshot(loan, include_ledger=include_ledger)
    # 后台审批备注仅供管理端内部使用，H5 接口与 WebSocket 均不返回，避免调试工具可见。
    payload.pop("review_note", None)
    return payload


@router.get("/status", response_model=LoanResponse, response_model_exclude={"review_note"})
async def get_loan_status(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_latest_loan_snapshot_async(db, current_user.id)
    return serialize_h5_loan_snapshot(loan, include_ledger=True)


@router.post("/apply", response_model=LoanResponse, response_model_exclude={"review_note"})
async def apply_limit(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_or_create_latest_loan(db, current_user.id)
    await expire_unused_approved_credit_for_loan(db, loan)
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    if await refresh_user_blacklist_status(db, db_user):
        await db.commit()
        raise HTTPException(status_code=400, detail="抱歉 您当前无法申请信用购物额度")
    await refresh_user_risk_list_status(db, db_user)
    # 第一阶段采用 shadow mode，只沉淀规则命中和特征快照，不改变现有审批结果。
    await record_risk_decision_async(db, user=db_user, loan=loan, stage="APPLICATION", mode="SHADOW")

    if not db_user.application_submitted_at:
        raise HTTPException(status_code=400, detail="请先完成补充资料提交")
    if loan.status == "REJECTED":
        raise HTTPException(status_code=400, detail="很遗憾，您当前未通过审核")
    if loan.status != "INIT":
        raise HTTPException(status_code=400, detail="当前状态不可重新申请额度")

    loan.status = "REVIEWING"
    loan.review_note = None
    await assign_review_admin_if_needed_async(db, loan)
    await log_user_event_async(
        db,
        user=db_user,
        loan=loan,
        event_type="LOAN_REAPPLY",
        title="重新发起额度申请",
        detail="用户重新发起额度审核。",
    )

    await db.commit()
    await db.refresh(loan)
    await notify_loan_snapshot_changed(current_user.id)
    await notify_admin_stats_changed()
    return serialize_h5_loan_snapshot(loan)


@router.post("/purchase-contract/preview", response_model=PurchaseContractResponse)
async def preview_purchase_contract(
    req: PurchaseContractPreviewRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user, loan, _source_loan, product = await _resolve_order_contract_context(
        db,
        current_user=current_user,
        product_id=req.product_id,
        extension_source_loan_id=req.extension_source_loan_id,
    )
    order_no = generate_order_no()
    payload = build_contract_payload(
        user=db_user,
        loan=loan,
        product=product,
        order_no=order_no,
        use_discount=req.use_discount,
    )
    return {
        "id": None,
        "signature_no": None,
        "order_no": order_no,
        "user_id": db_user.id,
        "loan_id": loan.id,
        "product_id": product.id,
        "contract_title": "GalaCredit Loan Agreement",
        "contract_content": payload["contract_content"],
        "party_a_name": PARTY_A_NAME,
        "party_a_legal_person": PARTY_A_LEGAL_PERSON,
        "party_b_name": db_user.name,
        "party_b_id_card": db_user.id_card_num,
        "party_b_phone": db_user.phone,
        "product_name": payload["product_name"],
        "ecard_face_value": payload["ecard_face_value"],
        "rights_price": payload["rights_price"],
        "discount_amount": payload["discount_amount"],
        "payment_amount": payload["payment_amount"],
        "term_days": payload["term_days"],
        "due_date_text": payload["due_date_text"],
        "signed_at": None,
        "ip": None,
    }


@router.post("/purchase-contract/sign", response_model=PurchaseContractResponse)
async def sign_purchase_contract(
    req: PurchaseContractPreviewRequest,
    request: Request,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user, loan, source_loan, product = await _resolve_order_contract_context(
        db,
        current_user=current_user,
        product_id=req.product_id,
        extension_source_loan_id=req.extension_source_loan_id,
    )
    signed_at = datetime.now()
    order_no = generate_order_no(signed_at)
    payload = build_contract_payload(
        user=db_user,
        loan=loan,
        product=product,
        order_no=order_no,
        use_discount=req.use_discount,
        signed_at=signed_at,
    )
    signature = PurchaseContractSignature(
        signature_no=generate_contract_no(signed_at),
        order_no=order_no,
        user_id=db_user.id,
        loan_id=loan.id,
        product_id=product.id,
        extension_source_loan_id=source_loan.id if source_loan else None,
        contract_title="GalaCredit Loan Agreement",
        contract_content=payload["contract_content"],
        contract_text=payload["contract_text"],
        party_a_name=PARTY_A_NAME,
        party_a_legal_person=PARTY_A_LEGAL_PERSON,
        party_b_name=db_user.name,
        party_b_id_card=db_user.id_card_num,
        party_b_phone=db_user.phone,
        party_b_address=payload["party_b_address"],
        product_name=payload["product_name"],
        ecard_face_value=payload["ecard_face_value"],
        rights_price=payload["rights_price"],
        discount_amount=payload["discount_amount"],
        payment_amount=payload["payment_amount"],
        term_days=payload["term_days"],
        due_date_text=payload["due_date_text"],
        signed_at=signed_at,
        ip=resolve_client_ip(request, default_ip=""),
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    db.add(signature)
    await db.flush()
    if getattr(product, "product_type", None) == "CASH_LOAN":
        db.add(
            LoanMandate(
                loan_id=loan.id,
                user_id=db_user.id,
                provider="momo",
                status="ACTIVE",
                consent_version="v1",
                consent_content=(
                    "The borrower authorizes GalaCredit and its appointed MoMo provider "
                    "to process the confirmed disbursement and supported repayment collection."
                ),
                phone=db_user.phone,
                signed_at=signed_at,
            )
        )
    await log_user_event_async(
        db,
        user=db_user,
        loan=loan,
        event_type="PURCHASE_CONTRACT_SIGNED",
        title="Sign GalaCredit Loan Agreement",
        detail=f"合同编号：{signature.signature_no}；订单号：{order_no}；商品：{product.name}；金额：{payload['payment_amount']:.2f} 元。",
    )
    await db.commit()
    await db.refresh(signature)
    return serialize_purchase_contract(signature)


@router.post("/withdraw", response_model=LoanResponse, response_model_exclude={"review_note"})
async def withdraw(
    req: LoanOrderRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    loan = await get_or_create_latest_loan(db, current_user.id)
    await expire_unused_approved_credit_for_loan(db, loan)
    if await refresh_user_blacklist_status(db, db_user):
        await db.commit()
        raise HTTPException(status_code=400, detail="抱歉 您当前无法申请信用购物额度")
    await refresh_user_risk_list_status(db, db_user)
    # 下单前再次记录决策，后续可切换为放款前强制策略并支持决策重放。
    await record_risk_decision_async(db, user=db_user, loan=loan, stage="ORDER", mode="SHADOW")
    source_loan = None
    if req.extension_source_loan_id:
        source_loan = (
            await db.execute(
                select(Loan)
                .where(
                    Loan.id == req.extension_source_loan_id,
                    Loan.user_id == current_user.id,
                    Loan.status.in_(["DISBURSED", "OVERDUE"]),
                )
            )
        ).scalar_one_or_none()
        if not source_loan:
            raise HTTPException(status_code=400, detail="未找到可展期的原账单")
        if not _is_regular_ecard_rights_loan(source_loan):
            raise HTTPException(status_code=400, detail="纯权益包只能用于已有常规订单的展期")
    elif loan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="当前状态不可下单")
    verified = await sms_service.verify_code(phone=db_user.phone, biz_type=ORDER_SMS_BIZ_TYPE, code=req.sms_code)
    if not verified:
        raise HTTPException(status_code=400, detail="短信验证码错误或已过期")

    product = (
        await db.execute(select(Product).where(Product.id == req.product_id, Product.is_active.is_(True)))
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在或已下架")
    if source_loan and not _is_rights_only_product(product):
        raise HTTPException(status_code=400, detail="带息费展期只能下单纯权益包")
    if not source_loan and _is_rights_only_product(product):
        raise HTTPException(status_code=400, detail="纯权益包只能用于已有常规订单的展期")
    if not source_loan and getattr(product, "product_type", None) == "CASH_LOAN":
        history = (await db.execute(select(Loan).where(Loan.user_id == current_user.id))).scalars().all()
        borrower_type = resolve_borrower_type(history)
        product_type = getattr(product, "borrower_type", None) or "ALL"
        if product_type not in {"ALL", borrower_type}:
            raise HTTPException(status_code=400, detail="当前贷款政策不适用于您的借款人类型")

    available_limit = float(getattr(db_user, "available_credit_limit", 0) or 0)
    payment_amount = float(product.payment_amount or 0)
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="商品支付金额配置异常")
    if available_limit <= 0:
        raise HTTPException(status_code=400, detail="暂无可用信用额度")
    if payment_amount - available_limit > 1e-6:
        raise HTTPException(status_code=400, detail="信用额度不足，请选择更低金额商品")

    is_cash_loan = getattr(product, "product_type", None) == "CASH_LOAN"
    nominal_amount = float(getattr(product, "nominal_loan_amount", 0) or payment_amount)
    upfront_fee_rate = float(getattr(product, "upfront_fee_rate", 0.4) or 0.4)
    upfront_fee_amount = round(nominal_amount * upfront_fee_rate, 2)
    actual_disbursement_amount = round(max(nominal_amount - upfront_fee_amount, 0), 2)
    ecard_face_value = 0 if is_cash_loan else float(product.ecard_face_value or 0)
    rights_price = 0 if is_cash_loan else float(product.rights_price or 0)
    available_discount = 0.0 if source_loan or is_cash_loan else float(loan.approval_discount_amount or 0)
    discount_amount = min(available_discount, rights_price) if req.use_discount else 0.0
    payment_amount = round(nominal_amount if is_cash_loan else payment_amount - discount_amount, 2)
    effective_rights_price = max(rights_price - discount_amount, 0)
    signature = (
        await db.execute(
            select(PurchaseContractSignature).where(
                PurchaseContractSignature.id == req.contract_signature_id,
                PurchaseContractSignature.user_id == current_user.id,
                PurchaseContractSignature.product_id == product.id,
            )
        )
    ).scalar_one_or_none()
    if not signature:
        raise HTTPException(status_code=400, detail="请先阅读并同意《GalaCredit Loan Agreement》")
    if (signature.extension_source_loan_id or None) != (req.extension_source_loan_id or None):
        raise HTTPException(status_code=400, detail="合同签署记录与当前下单类型不匹配")
    if abs(float(signature.payment_amount or 0) - float(payment_amount or 0)) > 1e-6:
        raise HTTPException(status_code=400, detail="合同签署金额与当前下单金额不一致，请重新阅读并同意合同")
    fee_rate = upfront_fee_rate if is_cash_loan else ((effective_rights_price / ecard_face_value) if ecard_face_value > 0 else 0.0)

    order_loan = loan
    if source_loan:
        order_loan = Loan(
            user_id=current_user.id,
            status="WITHDRAWING",
            approved_credit_limit=payment_amount,
            is_extension_fee_order=True,
            extension_source_loan_id=source_loan.id,
        )
        db.add(order_loan)
        await db.flush()

    order_loan.credit_limit = ecard_face_value if ecard_face_value > 0 else payment_amount
    order_loan.fee_rate = fee_rate
    order_loan.fee_amount = upfront_fee_amount if is_cash_loan else effective_rights_price
    order_loan.nominal_loan_amount = payment_amount if is_cash_loan else ecard_face_value
    order_loan.upfront_fee_amount = upfront_fee_amount if is_cash_loan else effective_rights_price
    order_loan.actual_disbursement_amount = actual_disbursement_amount if is_cash_loan else ecard_face_value
    order_loan.total_repayment_amount_snapshot = payment_amount if is_cash_loan else 0
    order_loan.interest_start_day = int(getattr(product, "interest_start_day", 1) or 1)
    order_loan.repayment_due_day = int(getattr(product, "repayment_due_day", product.term_days) or product.term_days)
    order_loan.installment_count = int(getattr(product, "installment_count", 1) or 1)
    order_loan.installment_ratios_json = getattr(product, "installment_ratios_json", None)
    order_loan.fee_components_json = getattr(product, "fee_components_json", None)
    order_loan.daily_overdue_fee_snapshot = round(float(getattr(product, "daily_overdue_fee", 0) or 0), 2)
    order_term_days = source_loan.term_days if source_loan else (loan.term_days or product.term_days)
    order_loan.term_days = order_term_days
    order_loan.product_term_days = order_term_days
    order_loan.product_id = product.id
    order_loan.product_type = getattr(product, "product_type", None) or "CASH_LOAN"
    order_loan.product_name = product.name
    order_loan.rights_title = product.rights_title
    order_loan.rights_desc = product.rights_desc
    order_loan.rights_contact_phone = _extract_product_contact_phone(product)
    order_loan.rights_price = effective_rights_price if not is_cash_loan else 0
    order_loan.ecard_face_value = ecard_face_value
    order_loan.product_total_price = payment_amount
    order_loan.order_discount_amount = discount_amount
    order_loan.order_no = signature.order_no or generate_order_no()
    order_loan.status = "WITHDRAWING"
    order_loan.disbursed_at = None
    order_loan.due_date = None
    order_loan.penalty_amount = 0
    order_loan.repaid_amount = 0
    order_loan.reduction_amount = 0
    order_loan.other_fee_amount = 0
    order_loan.paid_penalty_amount = 0
    order_loan.reduced_penalty_amount = 0
    order_loan.actual_repayment_date = None
    order_loan.reminder_count = 0
    order_loan.last_reminded_at = None
    order_loan.collection_count = 0
    order_loan.last_collection_at = None
    order_loan.collection_note = None
    order_loan.collection_admin_id = None
    order_loan.collection_transferred_at = None
    order_loan.repay_attempt_count = 0
    order_loan.ecard_account = None
    order_loan.ecard_password = None
    order_loan.ecard_expires_at = None
    signature.loan_id = order_loan.id
    db_user.available_credit_limit = round(max(available_limit - payment_amount, 0), 2)

    await log_user_event_async(
        db,
        user=db_user,
        loan=order_loan,
        event_type="ORDER_SUBMIT",
        title="提交信用下单",
        detail=(
            f"已下单商品：{product.name}；"
            f"京东E卡面值 {ecard_face_value:.2f} 元；"
            f"旅游权益 {effective_rights_price:.2f} 元；"
            f"抵扣券 {discount_amount:.2f} 元；"
            f"信用支付金额 {payment_amount:.2f} 元；"
            f"账期 {order_term_days} 天。"
        ),
    )

    source_channel = None
    if db_user.source_channel_id:
        source_channel = (
            await db.execute(select(Channel).where(Channel.id == db_user.source_channel_id))
        ).scalar_one_or_none()
    if source_channel and normalize_channel_disbursement_mode(getattr(source_channel, "disbursement_mode", None)) == "AUTO_DISBURSE":
        # 自动渠道复用后台放款服务，确保MoMo、账本、分期和审计口径完全一致。
        system_operator = SimpleNamespace(
            id=0,
            username="SYSTEM_AUTO_DISBURSE",
            roles='["ADMIN"]',
            permissions=None,
        )
        await _disburse_loan(
            db,
            system_operator,
            order_loan.id,
            DisburseRequest(
                term_days=order_loan.term_days,
                interest_start_day=order_loan.interest_start_day,
                repayment_due_day=order_loan.repayment_due_day,
            ),
        )

    await db.commit()
    await db.refresh(order_loan)
    await notify_loan_snapshot_changed(current_user.id)
    await notify_admin_stats_changed()
    return serialize_h5_loan_snapshot(order_loan)


@router.post("/order-sms-code", response_model=LoanOrderSmsCodeResponse)
async def send_order_sms_code(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """下发订单短信验证码。

    :param current_user: 当前登录用户
    :param db: 异步数据库会话
    :return: 下发结果
    """
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    success, cooldown_seconds, message = await sms_service.send_code(phone=db_user.phone, biz_type=ORDER_SMS_BIZ_TYPE)
    if not success:
        raise HTTPException(status_code=429, detail=message)
    return {"msg": message, "cooldown_seconds": cooldown_seconds}


@router.post("/repay-attempt")
async def register_repay_attempt(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    started = time.perf_counter()
    checkpoint = started
    # 这里直接复用鉴权产物，避免重复查询 users 表。
    db_user = current_user
    user_query_cost_ms = round((time.perf_counter() - checkpoint) * 1000, 2)

    checkpoint = time.perf_counter()
    # repay-attempt 仅需读取/更新当前订单基础字段，改为单表分步查询，避免 selectinload 关系预加载。
    loan = (
        await db.execute(
            select(Loan)
            .where(Loan.user_id == current_user.id)
            .order_by(Loan.id.desc())
            .limit(1)
        )
    ).scalars().first()
    if loan is None or loan.status == "SETTLED":
        loan = await create_init_loan_async(db, current_user.id)
    loan_query_cost_ms = round((time.perf_counter() - checkpoint) * 1000, 2)

    checkpoint = time.perf_counter()
    sync_loan_repayment_state(loan)
    if loan.status not in {"DISBURSED", "OVERDUE"}:
        raise HTTPException(status_code=400, detail="当前账单状态不可发起还款提醒")

    loan.repay_attempt_count = int(loan.repay_attempt_count or 0) + 1
    await log_user_event_async(
        db,
        user=db_user,
        loan=loan,
        event_type="USER_REPAY_ATTEMPT",
        title="用户点击立即还款",
        detail=f"累计点击立即还款 {loan.repay_attempt_count} 次。",
    )
    event_write_cost_ms = round((time.perf_counter() - checkpoint) * 1000, 2)

    checkpoint = time.perf_counter()
    await db.commit()
    await notify_loan_snapshot_changed(current_user.id)
    await notify_admin_stats_changed()
    commit_cost_ms = round((time.perf_counter() - checkpoint) * 1000, 2)
    total_cost_ms = round((time.perf_counter() - started) * 1000, 2)
    # 分段埋点：用于定位 repay-attempt 慢请求是卡在查询、事件写入还是事务提交。
    request_logger.info(
        "repay_attempt_perf user_id=%s loan_id=%s total_ms=%s user_query_ms=%s loan_query_ms=%s event_write_ms=%s commit_ms=%s",
        current_user.id,
        getattr(loan, "id", None),
        total_cost_ms,
        user_query_cost_ms,
        loan_query_cost_ms,
        event_write_cost_ms,
        commit_cost_ms,
    )
    return {"msg": "已登记还款尝试", "repay_attempt_count": loan.repay_attempt_count}


@router.get("/products", response_model=list[ProductItemResponse])
async def get_products(
    extension_source_loan_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    available_limit = float(getattr(db_user, "available_credit_limit", 0) or 0)
    products = (
        await db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.payment_amount.asc(), Product.id.asc()))
    ).scalars().all()
    if extension_source_loan_id:
        source_loan = (
            await db.execute(
                select(Loan).where(
                    Loan.id == extension_source_loan_id,
                    Loan.user_id == current_user.id,
                    Loan.status.in_(["DISBURSED", "OVERDUE"]),
                )
            )
        ).scalar_one_or_none()
        if not source_loan or not _is_regular_ecard_rights_loan(source_loan):
            return []
        products = [item for item in products if _is_rights_only_product(item)]
    else:
        products = [item for item in products if not _is_rights_only_product(item)]
        history = (await db.execute(select(Loan).where(Loan.user_id == current_user.id))).scalars().all()
        borrower_type = resolve_borrower_type(history)
        products = [
            item for item in products
            if getattr(item, "product_type", None) != "CASH_LOAN"
            or (getattr(item, "borrower_type", None) or "ALL") in {"ALL", borrower_type}
        ]
    if available_limit > 0:
        products = [item for item in products if float(item.payment_amount or 0) <= available_limit + 1e-6]
    else:
        products = []
    result = []
    for item in products:
        rights_detail = None
        if getattr(item, "rights_detail_json", None):
            try:
                rights_detail = json.loads(item.rights_detail_json)
            except (TypeError, ValueError):
                rights_detail = None
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "ecard_face_value": item.ecard_face_value,
                "rights_price": item.rights_price,
                "rights_title": item.rights_title,
                "rights_desc": item.rights_desc,
                "rights_detail": rights_detail,
                "term_days": item.term_days,
                "payment_amount": item.payment_amount,
                "nominal_loan_amount": getattr(item, "nominal_loan_amount", 0),
                "upfront_fee_rate": getattr(item, "upfront_fee_rate", 0),
                "upfront_fee_amount": round(float(getattr(item, "nominal_loan_amount", 0) or item.payment_amount or 0) * float(getattr(item, "upfront_fee_rate", 0) or 0), 2) if item.product_type == "CASH_LOAN" else 0,
                "actual_disbursement_amount": round(float(getattr(item, "nominal_loan_amount", 0) or item.payment_amount or 0) * (1 - float(getattr(item, "upfront_fee_rate", 0) or 0)), 2) if item.product_type == "CASH_LOAN" else 0,
                "fee_components": json.loads(item.fee_components_json) if getattr(item, "fee_components_json", None) else None,
                "interest_start_day": getattr(item, "interest_start_day", 1),
                "repayment_due_day": getattr(item, "repayment_due_day", item.term_days),
                "installment_count": getattr(item, "installment_count", 1),
                "installment_ratios": json.loads(item.installment_ratios_json) if getattr(item, "installment_ratios_json", None) else [],
                "daily_overdue_fee": getattr(item, "daily_overdue_fee", 0),
                "borrower_type": getattr(item, "borrower_type", None) or "ALL",
                "product_type": item.product_type,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
        )
    return result


@router.get("/ecard-secret", response_model=EcardSecretResponse)
async def get_ecard_secret(
    field: str,
    item_id: Optional[int] = None,
    index: Optional[int] = None,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    if field not in {"account", "password"}:
        raise HTTPException(status_code=400, detail="字段参数非法")
    loan = await get_or_create_latest_loan(db, current_user.id)
    if loan.status not in {"DISBURSED", "OVERDUE", "SETTLED"}:
        raise HTTPException(status_code=400, detail="当前订单尚未发卡")
    if item_id is not None or index is not None:
        stmt = select(LoanEcard).where(LoanEcard.loan_id == loan.id).order_by(LoanEcard.id.asc())
        if item_id is not None:
            stmt = stmt.where(LoanEcard.id == item_id)
            ecard_item = (await db.execute(stmt)).scalars().first()
        else:
            ecard_items = (await db.execute(stmt)).scalars().all()
            ecard_item = ecard_items[index] if index is not None and 0 <= index < len(ecard_items) else None
        if not ecard_item:
            raise HTTPException(status_code=404, detail="未找到该张E卡")
        value = ecard_item.account if field == "account" else ecard_item.password
        await _record_ecard_secret_copy(
            db,
            user=current_user,
            loan=loan,
            field=field,
            loan_ecard_id=ecard_item.id,
            ecard_pool_id=ecard_item.ecard_pool_id,
            index=index,
        )
        return {"field": field, "value": value, "item_id": ecard_item.id, "index": index}

    ecard_item = (
        await db.execute(select(LoanEcard).where(LoanEcard.loan_id == loan.id).order_by(LoanEcard.id.asc()).limit(1))
    ).scalars().first()
    if ecard_item:
        value = ecard_item.account if field == "account" else ecard_item.password
        await _record_ecard_secret_copy(
            db,
            user=current_user,
            loan=loan,
            field=field,
            loan_ecard_id=ecard_item.id,
            ecard_pool_id=ecard_item.ecard_pool_id,
            index=0,
        )
        return {"field": field, "value": value, "item_id": ecard_item.id, "index": 0}

    value = loan.ecard_account if field == "account" else loan.ecard_password
    if not value:
        raise HTTPException(status_code=404, detail="暂无可复制卡密")
    await _record_ecard_secret_copy(db, user=current_user, loan=loan, field=field)
    return {"field": field, "value": value}


@router.get("/bill", response_model=LoanResponse, response_model_exclude={"review_note"})
async def get_bill(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_latest_loan_snapshot_async(db, current_user.id)
    return serialize_h5_loan_snapshot(loan, include_ledger=True)


@router.websocket("/ws/status")
async def loan_status_ws(websocket: WebSocket):
    """通过 WebSocket 推送用户订单与账单快照。

    :param websocket: WebSocket 连接
    :return: None
    """
    trace_id = websocket.headers.get((settings.TID_HEADER_NAME or "X-Trace-Id")) or new_trace_id()
    tid_token = set_trace_id(trace_id)
    try:
        await websocket.accept()
        token = _extract_ws_token(websocket)
        async with AsyncSessionLocal() as auth_db:
            current_user = await _get_ws_user_by_token(auth_db, token)
        if current_user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        current_user_id = int(current_user.id)

        try:
            last_version = -1
            while True:
                # 每次推送使用独立短会话，避免长连接长期占用连接和事务快照不刷新问题。
                async with AsyncSessionLocal() as loop_db:
                    snapshot = await get_latest_loan_snapshot_async(loop_db, current_user_id)
                await websocket.send_json(
                    jsonable_encoder({"type": "loan_snapshot", "data": serialize_h5_loan_snapshot(snapshot, include_ledger=True)})
                )
                last_version = await wait_loan_snapshot_changed(current_user_id, last_version, LOAN_STATUS_WS_PUSH_SECONDS)
        except WebSocketDisconnect:
            return
    finally:
        reset_trace_id(tid_token)
