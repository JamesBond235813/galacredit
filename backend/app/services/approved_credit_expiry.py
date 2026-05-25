from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.loan import Loan
from app.models.user import User
from app.services.audit import log_user_event_async

APPROVED_CREDIT_VALID_DAYS = 3


def get_approved_credit_expires_at(loan: Loan) -> Optional[datetime]:
    """获取审批额度失效时间。

    :param loan: 订单对象
    :return: 额度失效时间；未审批时返回 None
    """
    approved_at = getattr(loan, "approved_at", None)
    if not approved_at:
        return None
    return approved_at + timedelta(days=APPROVED_CREDIT_VALID_DAYS)


def is_unused_approved_credit_expired(loan: Loan, now: Optional[datetime] = None) -> bool:
    """判断未下单审批额度是否已过期。

    :param loan: 订单对象
    :param now: 当前时间，便于测试注入
    :return: 已过期返回 True
    """
    if getattr(loan, "status", None) != "APPROVED":
        return False
    expires_at = get_approved_credit_expires_at(loan)
    return bool(expires_at and (now or datetime.now()) >= expires_at)


async def expire_unused_approved_credit_for_loan(
    db: AsyncSession,
    loan: Loan,
    now: Optional[datetime] = None,
    *,
    commit: bool = True,
) -> bool:
    """将已过期且未下单的审批额度清零。

    :param db: 异步数据库会话
    :param loan: 订单对象
    :param now: 当前时间，便于测试注入
    :param commit: 是否立即提交
    :return: 发生过期处理返回 True
    """
    if not is_unused_approved_credit_expired(loan, now=now):
        return False

    owner = getattr(loan, "owner", None)
    if owner is None and getattr(loan, "user_id", None):
        owner = (await db.execute(select(User).where(User.id == loan.user_id))).scalar_one_or_none()
    if owner is None:
        return False
    previous_limit = float(getattr(loan, "approved_credit_limit", 0) or getattr(loan, "credit_limit", 0) or 0)
    expires_at = get_approved_credit_expires_at(loan)

    # 只退回未下单的 APPROVED 申请；已下单后状态会变更，不会进入这里。
    loan.status = "INIT"
    loan.credit_limit = 0
    loan.approved_credit_limit = 0
    loan.approval_discount_amount = 0
    loan.order_discount_amount = 0
    loan.approved_at = None
    loan.review_note = None
    if owner:
        owner.approved_limit = 0
        owner.available_credit_limit = 0
        owner.overdue_credit_locked = False

    await log_user_event_async(
        db,
        user=owner,
        loan=loan,
        actor_type="SYSTEM",
        event_type="APPROVED_CREDIT_EXPIRED",
        title="授信额度自动归零",
        detail=(
            f"审批额度 {previous_limit:.2f} 元超过 {APPROVED_CREDIT_VALID_DAYS} 天未下单，"
            f"系统已于 {expires_at.strftime('%Y-%m-%d %H:%M:%S') if expires_at else '--'} 后清零并允许重新申请。"
        ),
    )
    if commit:
        await db.commit()
        await db.refresh(loan)
    return True


async def expire_unused_approved_credits(
    db: AsyncSession,
    now: Optional[datetime] = None,
    *,
    loans: Optional[Iterable[Loan]] = None,
) -> int:
    """批量处理已过期且未下单的审批额度。

    :param db: 异步数据库会话
    :param now: 当前时间，便于测试注入
    :param loans: 可选订单集合；为空时从数据库查询
    :return: 已处理数量
    """
    current = now or datetime.now()
    if loans is None:
        cutoff = current - timedelta(days=APPROVED_CREDIT_VALID_DAYS)
        loans = (
            await db.execute(
                select(Loan)
                .options(joinedload(Loan.owner))
                .where(Loan.status == "APPROVED", Loan.approved_at.isnot(None), Loan.approved_at <= cutoff)
            )
        ).scalars().all()

    count = 0
    for loan in loans:
        expired = await expire_unused_approved_credit_for_loan(db, loan, now=current, commit=False)
        if expired:
            count += 1
    if count:
        await db.commit()
    return count
