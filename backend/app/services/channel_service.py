import re
from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.loan import Loan
from app.models.user import User
from app.services.audit import log_user_event_async
from app.services.loan_amounts import calculate_remaining_repayment_amount, round_money

CHANNEL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
CHANNEL_STATUSES = {"ACTIVE", "INACTIVE"}
APPLICATION_STATUSES = {"REVIEWING", "APPROVED", "REJECTED", "WITHDRAWING", "DISBURSED", "OVERDUE", "SETTLED"}
DISBURSED_STATUSES = {"DISBURSED", "OVERDUE", "SETTLED"}


def normalize_channel_name(value: str) -> str:
    channel_name = (value or "").strip().lower()
    if not CHANNEL_NAME_PATTERN.fullmatch(channel_name):
        raise ValueError("渠道名称仅支持 2-32 位小写字母、数字、中划线和下划线")
    return channel_name


def normalize_channel_status(value: Optional[str]) -> str:
    status = (value or "ACTIVE").strip().upper()
    if status not in CHANNEL_STATUSES:
        raise ValueError("渠道状态非法")
    return status


async def get_channel_by_name_async(
    db: AsyncSession,
    channel_name: str,
    *,
    active_only: bool = False,
) -> Optional[Channel]:
    try:
        normalized_name = normalize_channel_name(channel_name)
    except ValueError:
        return None
    query = select(Channel).where(Channel.channel_name == normalized_name)
    if active_only:
        query = query.where(Channel.status == "ACTIVE")
    return (await db.execute(query)).scalar_one_or_none()


async def bind_user_source_channel_async(
    db: AsyncSession,
    *,
    user: User,
    channel: Channel,
    loan: Optional[Loan] = None,
):
    now = datetime.utcnow()

    if user.source_channel_id is None:
        user.source_channel = channel
        user.channel_bound_at = now
        user.last_channel_visit_at = now
        await log_user_event_async(
            db,
            user=user,
            loan=loan,
            actor_type="SYSTEM",
            event_type="CHANNEL_BOUND",
            title="绑定专属渠道",
            detail=f"首次通过渠道 {channel.sales_name}（{channel.channel_name}）进入 H5，已绑定渠道归属。",
        )
        return "BOUND"

    if user.source_channel_id == channel.id:
        user.last_channel_visit_at = now
        return "REFRESHED"

    return "IGNORED"


def serialize_channel_landing(channel: Channel):
    return {
        "id": channel.id,
        "channel_name": channel.channel_name,
        "sales_name": channel.sales_name,
        "status": channel.status,
    }


def build_channel_metrics(channel: Channel):
    users = list(channel.users or [])
    attributed_user_count = len(users)
    application_count = 0
    submitted_user_count = 0
    disbursed_user_ids = set()
    overdue_user_ids = set()
    disbursed_amount = 0.0
    overdue_amount = 0.0
    latest_application_at = None
    latest_disbursed_at = None

    for user in users:
        if user.application_submitted_at:
            submitted_user_count += 1
            latest_application_at = _max_datetime(latest_application_at, user.application_submitted_at)

        for loan in user.loans or []:
            if loan.status in APPLICATION_STATUSES:
                application_count += 1
                latest_application_at = _max_datetime(latest_application_at, loan.created_at)

            if loan.status in DISBURSED_STATUSES:
                disbursed_user_ids.add(user.id)
                disbursed_amount += round_money(getattr(loan, "credit_limit", 0))
                latest_disbursed_at = _max_datetime(latest_disbursed_at, getattr(loan, "disbursed_at", None))

            if loan.status == "OVERDUE":
                overdue_user_ids.add(user.id)
                overdue_amount += calculate_remaining_repayment_amount(loan)

    disbursed_user_count = len(disbursed_user_ids)
    overdue_user_count = len(overdue_user_ids)
    overdue_rate = round((overdue_user_count / disbursed_user_count) * 100, 2) if disbursed_user_count else 0.0

    return {
        "id": channel.id,
        "channel_name": channel.channel_name,
        "sales_name": channel.sales_name,
        "status": channel.status,
        "note": channel.note,
        "created_at": channel.created_at,
        "attributed_user_count": attributed_user_count,
        "submitted_user_count": submitted_user_count,
        "application_count": application_count,
        "disbursed_user_count": disbursed_user_count,
        "disbursed_amount": round_money(disbursed_amount),
        "overdue_user_count": overdue_user_count,
        "overdue_amount": round_money(overdue_amount),
        "overdue_rate": overdue_rate,
        "latest_application_at": latest_application_at,
        "latest_disbursed_at": latest_disbursed_at,
    }


def build_channel_summary(items: Iterable[dict]):
    metrics = list(items)
    active_channels = sum(1 for item in metrics if item["status"] == "ACTIVE")
    total_channels = len(metrics)
    attributed_user_count = sum(int(item["attributed_user_count"]) for item in metrics)
    submitted_user_count = sum(int(item["submitted_user_count"]) for item in metrics)
    application_count = sum(int(item["application_count"]) for item in metrics)
    disbursed_user_count = sum(int(item["disbursed_user_count"]) for item in metrics)
    disbursed_amount = sum(float(item["disbursed_amount"]) for item in metrics)
    overdue_user_count = sum(int(item["overdue_user_count"]) for item in metrics)
    overdue_amount = sum(float(item["overdue_amount"]) for item in metrics)
    overdue_rate = round((overdue_user_count / disbursed_user_count) * 100, 2) if disbursed_user_count else 0.0

    return {
        "total_channels": total_channels,
        "active_channels": active_channels,
        "inactive_channels": max(total_channels - active_channels, 0),
        "attributed_user_count": attributed_user_count,
        "submitted_user_count": submitted_user_count,
        "application_count": application_count,
        "disbursed_user_count": disbursed_user_count,
        "disbursed_amount": round_money(disbursed_amount),
        "overdue_user_count": overdue_user_count,
        "overdue_amount": round_money(overdue_amount),
        "overdue_rate": overdue_rate,
    }


def _max_datetime(current, candidate):
    if candidate is None:
        return current
    if current is None or candidate > current:
        return candidate
    return current
