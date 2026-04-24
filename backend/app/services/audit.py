from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan
from app.models.user import User
from app.models.user_event import UserEvent


def _stringify_detail(detail: Any) -> Optional[str]:
    if detail is None:
        return None

    if isinstance(detail, str):
        return detail

    if isinstance(detail, dict):
        parts = [f"{key}：{value}" for key, value in detail.items() if value not in (None, "", [])]
        return "；".join(parts) if parts else None

    if isinstance(detail, (list, tuple, set)):
        parts = [str(item) for item in detail if item not in (None, "")]
        return "；".join(parts) if parts else None

    return str(detail)


async def log_user_event_async(
    db: AsyncSession,
    *,
    user: User,
    event_type: str,
    title: str,
    detail: Any = None,
    loan: Optional[Loan] = None,
    actor_type: str = "USER",
    operator_name: Optional[str] = None,
):
    event = UserEvent(
        user_id=user.id,
        loan_id=loan.id if loan else None,
        actor_type=actor_type,
        operator_name=operator_name,
        event_type=event_type,
        title=title,
        detail=_stringify_detail(detail),
    )
    db.add(event)
    await db.flush()
    return event
