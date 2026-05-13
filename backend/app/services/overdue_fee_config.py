from datetime import date
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
