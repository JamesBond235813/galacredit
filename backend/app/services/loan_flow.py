from typing import Optional
import asyncio

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.loan import Loan
from app.models.loan_installment import LoanInstallment

_CREATE_LOAN_LOCKS: dict[int, asyncio.Lock] = {}


def _get_create_loan_lock(user_id: int) -> asyncio.Lock:
    key = int(user_id)
    lock = _CREATE_LOAN_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _CREATE_LOAN_LOCKS[key] = lock
    return lock


def get_prior_settled_loans(loans, current_loan_id: Optional[int] = None):
    settled_loans = []
    for loan in loans or []:
        if loan.status != "SETTLED":
            continue
        if current_loan_id is not None and loan.id >= current_loan_id:
            continue
        settled_loans.append(loan)
    return sorted(settled_loans, key=lambda item: item.id, reverse=True)


def is_normal_settled_loan(loan: Loan) -> bool:
    if not loan or loan.status != "SETTLED":
        return False
    return float(loan.penalty_amount or 0) <= 0 and int(loan.collection_count or 0) <= 0


def get_latest_normal_settled_loan(loans, current_loan_id: Optional[int] = None) -> Optional[Loan]:
    settled_loans = get_prior_settled_loans(loans, current_loan_id=current_loan_id)
    for loan in settled_loans:
        if is_normal_settled_loan(loan):
            return loan
    return None


def get_relend_count(loans, current_loan_id: Optional[int] = None) -> int:
    return len(get_prior_settled_loans(loans, current_loan_id=current_loan_id))


def get_relend_label(loans, current_loan_id: Optional[int] = None) -> str:
    relend_count = get_relend_count(loans, current_loan_id=current_loan_id)
    if relend_count <= 0:
        return "初借"
    return f"复借{relend_count}"


def _extract_all_scalars(execute_result):
    scalars_result = execute_result.scalars()
    if hasattr(scalars_result, "all"):
        return scalars_result.all()
    if hasattr(scalars_result, "first"):
        first_item = scalars_result.first()
        if first_item is None:
            return []
        if isinstance(first_item, list):
            return first_item
        return [first_item]
    return []


async def get_latest_loan_async(db: AsyncSession, user_id: int) -> Optional[Loan]:
    # 分步单表查询：先取最新 loan，再按需查询关联表并手动回填，避免 selectinload 的批量预加载开销。
    loan = (
        await db.execute(
            select(Loan)
            .where(Loan.user_id == user_id)
            .where(or_(Loan.is_extension_fee_order.is_(False), Loan.is_extension_fee_order.is_(None)))
            .order_by(Loan.id.desc())
            .limit(1)
        )
    ).scalars().first()
    if loan is None:
        return None

    installments = _extract_all_scalars(
        await db.execute(
            select(LoanInstallment)
            .where(LoanInstallment.loan_id == loan.id)
            .order_by(LoanInstallment.period_no.asc())
        )
    )
    if installments and not isinstance(installments[0], LoanInstallment):
        installments = list(getattr(loan, "installments", []) or [])
    loan.installments = installments

    admin_ids = [item for item in {loan.review_admin_id, loan.collection_admin_id} if item]
    admins = _extract_all_scalars(
        await db.execute(select(Admin).where(Admin.id.in_(admin_ids)))
    ) if admin_ids else []
    admin_map = {int(item.id): item for item in admins}
    loan.review_admin = admin_map.get(int(loan.review_admin_id)) if loan.review_admin_id else None
    loan.collection_admin = admin_map.get(int(loan.collection_admin_id)) if loan.collection_admin_id else None
    return loan


async def create_init_loan_async(db: AsyncSession, user_id: int) -> Loan:
    lock = _get_create_loan_lock(user_id)
    async with lock:
        latest_loan = (
            await db.execute(
                select(Loan)
                .where(Loan.user_id == user_id)
                .where(or_(Loan.is_extension_fee_order.is_(False), Loan.is_extension_fee_order.is_(None)))
                .order_by(Loan.id.desc())
                .limit(1)
            )
        ).scalars().first()
        if latest_loan is not None and latest_loan.status != "SETTLED":
            return latest_loan

        loan = Loan(user_id=user_id, status="INIT")
        db.add(loan)
        await db.flush()
        return loan


async def get_or_create_loan_async(db: AsyncSession, user_id: int) -> Loan:
    loan = await get_latest_loan_async(db, user_id)
    if loan is None or loan.status == "SETTLED":
        loan = await create_init_loan_async(db, user_id)
    return loan
