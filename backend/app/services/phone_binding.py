from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phone_binding import UserPhoneBinding
from app.models.user import User


def is_internal_released_phone(phone: Optional[str]) -> bool:
    return bool(phone and "#released#" in phone)


async def record_phone_binding(
    db: AsyncSession,
    *,
    user: User,
    phone: str,
    bind_type: str = "ACTIVE",
    note: Optional[str] = None,
) -> UserPhoneBinding:
    now = datetime.now()
    binding = UserPhoneBinding(
        user_id=user.id,
        phone=phone,
        bind_type=bind_type,
        note=note,
        bound_at=now,
        created_at=now,
    )
    db.add(binding)
    await db.flush()
    return binding


async def close_active_phone_bindings(
    db: AsyncSession,
    *,
    phone: str,
    except_user_id: Optional[int] = None,
    note: Optional[str] = None,
) -> int:
    now = datetime.now()
    stmt = select(UserPhoneBinding).where(
        UserPhoneBinding.phone == phone,
        UserPhoneBinding.unbound_at.is_(None),
    )
    if except_user_id:
        stmt = stmt.where(UserPhoneBinding.user_id != except_user_id)
    bindings = (await db.execute(stmt)).scalars().all()
    for binding in bindings:
        binding.unbound_at = now
        binding.note = note or binding.note
    return len(bindings)


async def build_released_phone(db: AsyncSession, *, phone: str, user_id: int) -> str:
    base = f"{phone}#released#{user_id}"
    if len(base) <= 20:
        candidate = base
    else:
        candidate = f"{phone}#r{user_id}"[:20]

    suffix = 1
    while (await db.execute(select(User.id).where(User.phone == candidate))).scalar_one_or_none():
        suffix_text = str(suffix)
        candidate = f"{candidate[:20 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return candidate
