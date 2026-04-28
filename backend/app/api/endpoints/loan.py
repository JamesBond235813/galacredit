import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_async, get_user_by_token_async
from app.core.database import get_async_db
from app.models.loan import Loan
from app.models.product import Product
from app.models.user import User
from app.schemas.loan import EcardSecretResponse, LoanOrderRequest, LoanResponse, ProductItemResponse
from app.services.audit import log_user_event_async
from app.services.loan_amounts import serialize_loan_snapshot
from app.services.loan_assignment import assign_review_admin_if_needed_async
from app.services.loan_flow import get_latest_loan_async, get_or_create_loan_async
from app.services.loan_ledger import sync_loan_repayment_state

router = APIRouter()
LOAN_STATUS_WS_PUSH_SECONDS = 3


async def get_or_create_latest_loan(db: AsyncSession, user_id: int):
    latest_before = await get_latest_loan_async(db, user_id)
    latest_loan = await get_or_create_loan_async(db, user_id)
    if latest_before is None or latest_before.status == "SETTLED":
        await db.commit()
        await db.refresh(latest_loan)
    return latest_loan


async def get_latest_loan_snapshot_async(db: AsyncSession, user_id: int) -> Loan:
    """获取用于返回快照的贷款对象，并预加载账单相关关系。

    :param db: 异步数据库会话
    :param user_id: 用户ID
    :return: 预加载分期关系的贷款对象
    """
    loan = await get_or_create_latest_loan(db, user_id)
    # 这里强制预加载 installments，避免在序列化阶段触发异步懒加载导致 MissingGreenlet。
    snapshot_loan = (
        await db.execute(
            select(Loan)
            .options(selectinload(Loan.installments))
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


@router.get("/status", response_model=LoanResponse)
async def get_loan_status(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_latest_loan_snapshot_async(db, current_user.id)
    return serialize_loan_snapshot(loan, include_ledger=True)


@router.post("/apply", response_model=LoanResponse)
async def apply_limit(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_or_create_latest_loan(db, current_user.id)
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()

    if not db_user.application_submitted_at:
        raise HTTPException(status_code=400, detail="请先完成补充资料提交")
    if loan.status not in {"INIT", "REJECTED"}:
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
    return serialize_loan_snapshot(loan)


@router.post("/withdraw", response_model=LoanResponse)
async def withdraw(
    req: LoanOrderRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    loan = await get_or_create_latest_loan(db, current_user.id)
    if loan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="当前状态不可下单")

    product = (
        await db.execute(select(Product).where(Product.id == req.product_id, Product.is_active.is_(True)))
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在或已下架")

    approved_limit = float(loan.approved_credit_limit or loan.credit_limit or db_user.approved_limit or 0)
    payment_amount = float(product.payment_amount or 0)
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="商品支付金额配置异常")
    if approved_limit <= 0:
        raise HTTPException(status_code=400, detail="暂无可用信用额度")
    if payment_amount - approved_limit > 1e-6:
        raise HTTPException(status_code=400, detail="信用额度不足，请选择更低金额商品")

    ecard_face_value = float(product.ecard_face_value or 0)
    rights_price = float(product.rights_price or 0)
    fee_rate = (rights_price / ecard_face_value) if ecard_face_value > 0 else 0.0

    loan.credit_limit = ecard_face_value
    loan.fee_rate = fee_rate
    loan.fee_amount = rights_price
    loan.term_days = product.term_days
    loan.product_term_days = product.term_days
    loan.product_id = product.id
    loan.product_name = product.name
    loan.rights_title = product.rights_title
    loan.rights_desc = product.rights_desc
    loan.rights_price = rights_price
    loan.ecard_face_value = ecard_face_value
    loan.product_total_price = payment_amount
    loan.status = "WITHDRAWING"
    loan.disbursed_at = None
    loan.due_date = None
    loan.penalty_amount = 0
    loan.repaid_amount = 0
    loan.reduction_amount = 0
    loan.paid_penalty_amount = 0
    loan.reduced_penalty_amount = 0
    loan.reminder_count = 0
    loan.last_reminded_at = None
    loan.collection_count = 0
    loan.last_collection_at = None
    loan.collection_note = None
    loan.collection_admin_id = None
    loan.collection_transferred_at = None
    loan.repay_attempt_count = 0
    loan.ecard_account = None
    loan.ecard_password = None
    loan.ecard_expires_at = None

    await log_user_event_async(
        db,
        user=db_user,
        loan=loan,
        event_type="ORDER_SUBMIT",
        title="提交信用下单",
        detail=(
            f"已下单商品：{product.name}；"
            f"京东E卡面值 {ecard_face_value:.2f} 元；"
            f"旅游权益 {rights_price:.2f} 元；"
            f"信用支付金额 {payment_amount:.2f} 元；"
            f"账期 {product.term_days} 天。"
        ),
    )

    await db.commit()
    await db.refresh(loan)
    return serialize_loan_snapshot(loan)


@router.post("/repay-attempt")
async def register_repay_attempt(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    loan = await get_or_create_latest_loan(db, current_user.id)
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
    await db.commit()
    return {"msg": "已登记还款尝试", "repay_attempt_count": loan.repay_attempt_count}


@router.get("/products", response_model=list[ProductItemResponse])
async def get_products(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    db_user = (await db.execute(select(User).where(User.id == current_user.id))).scalar_one()
    loan = await get_or_create_latest_loan(db, current_user.id)
    approved_limit = float(loan.approved_credit_limit or loan.credit_limit or db_user.approved_limit or 0)
    products = (
        await db.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.payment_amount.asc(), Product.id.asc()))
    ).scalars().all()
    if approved_limit > 0:
        products = [item for item in products if float(item.payment_amount or 0) <= approved_limit + 1e-6]
    return products


@router.get("/ecard-secret", response_model=EcardSecretResponse)
async def get_ecard_secret(
    field: str,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    if field not in {"account", "password"}:
        raise HTTPException(status_code=400, detail="字段参数非法")
    loan = await get_or_create_latest_loan(db, current_user.id)
    if loan.status not in {"DISBURSED", "OVERDUE", "SETTLED"}:
        raise HTTPException(status_code=400, detail="当前订单尚未发卡")
    value = loan.ecard_account if field == "account" else loan.ecard_password
    if not value:
        raise HTTPException(status_code=404, detail="暂无可复制卡密")
    return {"field": field, "value": value}


@router.get("/bill", response_model=LoanResponse)
async def get_bill(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    loan = await get_latest_loan_snapshot_async(db, current_user.id)
    return serialize_loan_snapshot(loan, include_ledger=True)


@router.websocket("/ws/status")
async def loan_status_ws(websocket: WebSocket, db: AsyncSession = Depends(get_async_db)):
    """通过 WebSocket 推送用户贷款与账单快照。

    :param websocket: WebSocket 连接
    :param db: 异步数据库会话
    :return: None
    """
    await websocket.accept()
    token = _extract_ws_token(websocket)
    current_user = await _get_ws_user_by_token(db, token)
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    current_user_id = int(current_user.id)

    try:
        while True:
            # WebSocket 长连接会复用同一个 AsyncSession，这里先 rollback 结束上一轮只读事务，
            # 避免 MySQL 在默认隔离级别下持续读取到旧快照，导致前端看不到最新状态。
            rollback = getattr(db, "rollback", None)
            if rollback is not None:
                await rollback()
            snapshot = await get_latest_loan_snapshot_async(db, current_user_id)
            await websocket.send_json(
                jsonable_encoder({"type": "loan_snapshot", "data": serialize_loan_snapshot(snapshot, include_ledger=True)})
            )
            await asyncio.sleep(LOAN_STATUS_WS_PUSH_SECONDS)
    except WebSocketDisconnect:
        return
