from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import SessionLocal
from app.models.loan import Loan
from app.services.audit import log_user_event
from app.services.loan_assignment import assign_collection_admins_for_overdue_loans
from app.services.loan_ledger import ensure_installment_records, sync_loan_repayment_state

scheduler = AsyncIOScheduler()


def process_overdue_loans():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        active_loans = db.query(Loan).filter(Loan.status.in_(["DISBURSED", "OVERDUE"])).all()

        for loan in active_loans:
            previous_status = loan.status
            ensure_installment_records(db, loan)
            sync_loan_repayment_state(loan, now=now)

            overdue_base_date = loan.due_date
            if getattr(loan, "installments", None):
                overdue_candidates = [
                    item.due_date
                    for item in loan.installments
                    if item.status == "OVERDUE" and item.due_date is not None
                ]
                if overdue_candidates:
                    overdue_base_date = min(overdue_candidates)

            if previous_status != "OVERDUE" and loan.status == "OVERDUE" and loan.owner:
                log_user_event(
                    db,
                    user=loan.owner,
                    loan=loan,
                    actor_type="SYSTEM",
                    event_type="AUTO_OVERDUE",
                    title="系统自动转为逾期",
                    detail=f"存在逾期账单，订单 {loan.id} 自动转为逾期。",
                )

            if loan.status != "OVERDUE" or not overdue_base_date:
                continue

            days_overdue = max((now.date() - overdue_base_date.date()).days, 1)
            loan.penalty_amount = float(days_overdue * 10)

        assign_collection_admins_for_overdue_loans(db, now=now)

        db.commit()
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(process_overdue_loans, "cron", hour=0, minute=1, id="daily-overdue-check", replace_existing=True)
    scheduler.add_job(process_overdue_loans, "interval", minutes=1, id="debug-overdue-check", replace_existing=True)
    scheduler.start()
