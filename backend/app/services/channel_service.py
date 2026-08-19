import hashlib
import hmac
import re
from datetime import datetime, time, timedelta
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.channel import Channel
from app.models.loan import Loan
from app.models.user import User
from app.services.audit import log_user_event_async
from app.services.loan_amounts import calculate_remaining_repayment_amount, round_money

CHANNEL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
DAILY_INVITE_CODE_PATTERN = re.compile(r"^[a-z0-9]{24,32}$")
CHANNEL_STATUSES = {"ACTIVE", "INACTIVE"}
CHANNEL_DISBURSEMENT_MODES = {"AUTO_DISBURSE", "MANUAL_DISBURSE"}
APPLICATION_STATUSES = {"REVIEWING", "APPROVED", "REJECTED", "WITHDRAWING", "DISBURSED", "OVERDUE", "SETTLED"}
DISBURSED_STATUSES = {"DISBURSED", "OVERDUE", "SETTLED"}
CHANNEL_DAILY_ROTATE_AT = time(0, 1, 0)


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


def normalize_channel_disbursement_mode(value: Optional[str]) -> str:
    """规范化渠道放款模式。

    :param value: 渠道放款模式
    :return: 规范化后的放款模式
    """
    mode = (value or "MANUAL_DISBURSE").strip().upper()
    if mode not in CHANNEL_DISBURSEMENT_MODES:
        raise ValueError("渠道放款模式非法")
    return mode


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


async def get_channel_by_invite_code_async(
    db: AsyncSession,
    invite_code: str,
    *,
    active_only: bool = False,
) -> Optional[Channel]:
    code = (invite_code or "").strip().lower()
    if not DAILY_INVITE_CODE_PATTERN.fullmatch(code):
        return None
    channel_id = _parse_daily_invite_channel_id(code)
    if channel_id is None:
        return None
    query = select(Channel).where(Channel.id == channel_id)
    if active_only:
        query = query.where(Channel.status == "ACTIVE")
    channel = (await db.execute(query)).scalar_one_or_none()
    if not channel:
        return None
    return channel if code == build_daily_channel_invite_code(channel) else None


def build_daily_channel_invite_code(channel: Channel, now: Optional[datetime] = None) -> str:
    """生成渠道当日有效的邀请码。

    :param channel: 渠道对象
    :param now: 当前时间，默认使用系统当前时间
    :return: 当日动态邀请码
    """
    cycle_day = _resolve_channel_invite_cycle_day(now or datetime.now())
    channel_id = int(getattr(channel, "id", 0) or 0)
    seed = f"{channel_id}:{getattr(channel, 'invite_code', '')}:{cycle_day.isoformat()}".encode("utf-8")
    secret = (settings.SECRET_KEY or "xiaohebao-channel-link").encode("utf-8")
    digest = hmac.new(secret, seed, hashlib.sha256).hexdigest()
    return f"{_to_base36(channel_id).zfill(6)}{digest[:18]}"


def _resolve_channel_invite_cycle_day(now: datetime):
    """按每日 00:01 切换渠道码所属日期。

    :param now: 当前时间
    :return: 渠道码业务日期
    """
    return (now.date() - timedelta(days=1)) if now.time() < CHANNEL_DAILY_ROTATE_AT else now.date()


def _to_base36(value: int) -> str:
    """将数字转换为小写 base36。

    :param value: 数字
    :return: base36 字符串
    """
    if value <= 0:
        return "0"
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    output = ""
    while value:
        value, remainder = divmod(value, 36)
        output = alphabet[remainder] + output
    return output


def _parse_daily_invite_channel_id(code: str) -> Optional[int]:
    """从动态邀请码中解析渠道ID。

    :param code: 动态邀请码
    :return: 渠道ID，解析失败返回 None
    """
    try:
        return int(code[:6], 36)
    except ValueError:
        return None


async def bind_user_source_channel_async(
    db: AsyncSession,
    *,
    user: User,
    channel: Channel,
    loan: Optional[Loan] = None,
):
    now = datetime.now()

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
        "disbursement_mode": normalize_channel_disbursement_mode(getattr(channel, "disbursement_mode", None)),
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
