from datetime import date, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.overdue_fee_config import OverdueFeeConfig

DEFAULT_DAILY_PENALTY_AMOUNT = 10.0


async def get_effective_overdue_fee_config(
    db: AsyncSession,
    target_date: Optional[date],
) -> Optional[OverdueFeeConfig]:
    if target_date is None:
        target_date = date.today()
    return (
        await db.execute(
            select(OverdueFeeConfig)
            .where(OverdueFeeConfig.effective_date <= target_date)
            .order_by(OverdueFeeConfig.effective_date.desc(), OverdueFeeConfig.id.desc())
            .limit(1)
        )
    ).scalars().first()


async def resolve_daily_penalty_amount(db: AsyncSession, target_date: Optional[date]) -> float:
    config = await get_effective_overdue_fee_config(db, target_date)
    if not config:
        return DEFAULT_DAILY_PENALTY_AMOUNT
    return float(config.daily_penalty_amount or 0)


def calculate_overdue_days(
    due_date: Optional[datetime],
    actual_repayment_date: Optional[date],
) -> int:
    """根据应还日和实际还款日计算逾期天数。

    :param due_date: 订单应还时间
    :param actual_repayment_date: 实际还款日期
    :return: 逾期天数，最小为 0
    """
    if due_date is None or actual_repayment_date is None:
        return 0
    return max((actual_repayment_date - due_date.date()).days, 0)


async def calculate_penalty_by_repayment_date(
    db: AsyncSession,
    due_date: Optional[datetime],
    actual_repayment_date: Optional[date],
) -> dict:
    """按实际还款日和逾期配置计算应收逾期费。

    :param db: 异步数据库会话
    :param due_date: 订单应还时间
    :param actual_repayment_date: 实际还款日期
    :return: 逾期费用拆解信息
    """
    overdue_days = calculate_overdue_days(due_date, actual_repayment_date)
    daily_penalty_amount = await resolve_daily_penalty_amount(db, actual_repayment_date)
    penalty_amount = round(float(overdue_days * daily_penalty_amount), 2)
    return {
        "overdue_days": overdue_days,
        "daily_penalty_amount": round(float(daily_penalty_amount), 2),
        "penalty_amount": penalty_amount,
    }
