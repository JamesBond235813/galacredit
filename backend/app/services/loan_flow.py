from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan


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


async def get_latest_loan_async(db: AsyncSession, user_id: int) -> Optional[Loan]:
    result = await db.execute(select(Loan).where(Loan.user_id == user_id).order_by(Loan.id.desc()))
    return result.scalars().first()


async def create_init_loan_async(db: AsyncSession, user_id: int) -> Loan:
    loan = Loan(user_id=user_id, status="INIT")
    db.add(loan)
    await db.flush()
    return loan


async def get_or_create_loan_async(db: AsyncSession, user_id: int) -> Loan:
    loan = await get_latest_loan_async(db, user_id)
    if loan is None or loan.status == "SETTLED":
        loan = await create_init_loan_async(db, user_id)
    return loan
