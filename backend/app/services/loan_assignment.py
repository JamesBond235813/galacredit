from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.loan import Loan
from app.services.admin_permissions import parse_admin_roles

COLLECTION_TRANSFER_OVERDUE_DAYS = 14


def admin_has_role(admin: Admin, role_key: str) -> bool:
    roles = parse_admin_roles(getattr(admin, "roles", None))
    return "ADMIN" in roles or role_key in roles


def list_admins_by_role(db: Session, role_key: str) -> List[Admin]:
    admins = db.query(Admin).order_by(Admin.id.asc()).all()
    matched = [item for item in admins if role_key in parse_admin_roles(getattr(item, "roles", None))]
    if matched:
        return matched
    return [item for item in admins if "ADMIN" in parse_admin_roles(getattr(item, "roles", None))]


def pick_round_robin_admin_id(loan_id: int, admins: Iterable[Admin]) -> Optional[int]:
    pool = list(admins)
    if not pool:
        return None
    index = max(int(loan_id) - 1, 0) % len(pool)
    return pool[index].id


def assign_review_admin_if_needed(db: Session, loan: Loan, force: bool = False) -> Optional[int]:
    if loan is None:
        return None
    if loan.review_admin_id and not force:
        return loan.review_admin_id

    reviewers = list_admins_by_role(db, "REVIEW")
    review_admin_id = pick_round_robin_admin_id(loan.id, reviewers)
    if review_admin_id:
        loan.review_admin_id = review_admin_id
    return loan.review_admin_id


def is_collection_stage(loan: Loan, now: Optional[datetime] = None) -> bool:
    if not loan or loan.status != "OVERDUE" or not loan.due_date:
        return False
    now_dt = now or datetime.utcnow()
    overdue_days = max((now_dt.date() - loan.due_date.date()).days, 0)
    return overdue_days > COLLECTION_TRANSFER_OVERDUE_DAYS


def assign_collection_admin_if_needed(
    db: Session,
    loan: Loan,
    force: bool = False,
    now: Optional[datetime] = None,
) -> Optional[int]:
    if not is_collection_stage(loan, now=now):
        return None
    if loan.collection_admin_id and not force:
        return loan.collection_admin_id

    collectors = list_admins_by_role(db, "COLLECTION")
    collection_admin_id = pick_round_robin_admin_id(loan.id, collectors)
    if collection_admin_id:
        loan.collection_admin_id = collection_admin_id
        if loan.collection_transferred_at is None:
            loan.collection_transferred_at = now or datetime.utcnow()
    return loan.collection_admin_id


def assign_collection_admins_for_overdue_loans(db: Session, now: Optional[datetime] = None) -> int:
    now_dt = now or datetime.utcnow()
    loans = db.query(Loan).filter(Loan.status == "OVERDUE").all()
    changed = 0
    for loan in loans:
        prev_assignee = loan.collection_admin_id
        assigned = assign_collection_admin_if_needed(db, loan, force=False, now=now_dt)
        if assigned and assigned != prev_assignee:
            changed += 1
    return changed
