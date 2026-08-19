from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.loan import Loan
from app.models.user import User
from app.services.audit import log_user_event_async
from app.services.approved_credit_expiry import expire_unused_approved_credits
from app.services.blacklist_service import blacklist_user
from app.services.loan_assignment import assign_collection_admins_for_overdue_loans_async
from app.services.loan_ledger import ensure_installment_records_async, sync_loan_repayment_state
from app.services.overdue_fee_config import resolve_daily_penalty_amount

scheduler = AsyncIOScheduler()
LOAN_SCAN_PAGE_SIZE = 200


async def process_overdue_loans():
    async with AsyncSessionLocal() as db:
        now = datetime.now()
        last_loan_id = 0
        while True:
            active_loans = (
                await db.execute(
                    select(Loan)
                    .where(
                        Loan.status.in_(["DISBURSED", "OVERDUE"]),
                        Loan.id > last_loan_id,
                    )
                    .order_by(Loan.id.asc())
                    .limit(LOAN_SCAN_PAGE_SIZE)
                )
            ).scalars().all()
            if not active_loans:
                break

            # 分步单表查询：按 loan.user_id 批量获取用户，避免在调度扫描阶段使用 selectinload。
            owner_ids = [int(item.user_id) for item in active_loans if getattr(item, "user_id", None)]
            owners = (
                await db.execute(select(User).where(User.id.in_(owner_ids)))
            ).scalars().all() if owner_ids else []
            owners_by_id = {int(item.id): item for item in owners}

            for loan in active_loans:
                previous_status = loan.status
                installments = await ensure_installment_records_async(db, loan)
                sync_loan_repayment_state(loan, now=now)

                overdue_base_date = loan.due_date
                if installments:
                    overdue_candidates = [
                        item.due_date
                        for item in installments
                        if item.status == "OVERDUE" and item.due_date is not None
                    ]
                    if overdue_candidates:
                        overdue_base_date = min(overdue_candidates)

                loan_owner = owners_by_id.get(int(loan.user_id)) if getattr(loan, "user_id", None) else None
                if previous_status != "OVERDUE" and loan.status == "OVERDUE" and loan_owner:
                    await blacklist_user(
                        db,
                        loan_owner,
                        source="OVERDUE",
                        reason="订单逾期自动进入黑名单",
                        created_by="SYSTEM",
                    )
                    loan.approved_credit_limit = 0
                    loan_owner.approved_limit = 0
                    loan_owner.available_credit_limit = 0
                    loan_owner.overdue_credit_locked = True
                    await log_user_event_async(
                        db,
                        user=loan_owner,
                        loan=loan,
                        actor_type="SYSTEM",
                        event_type="AUTO_OVERDUE",
                        title="系统自动转为逾期",
                        detail=f"存在逾期账单，订单 {loan.id} 自动转为逾期。",
                    )

                if loan.status == "OVERDUE" and overdue_base_date:
                    days_overdue = max((now.date() - overdue_base_date.date()).days, 1)
                    # 现金贷逾期费在下单/放款时固化，避免后台修改产品后重算历史订单。
                    daily_penalty_amount = float(getattr(loan, "daily_overdue_fee_snapshot", 0) or 0)
                    if daily_penalty_amount <= 0:
                        daily_penalty_amount = await resolve_daily_penalty_amount(db, overdue_base_date.date())
                    loan.penalty_amount = float(days_overdue * daily_penalty_amount)

            last_loan_id = active_loans[-1].id

        await assign_collection_admins_for_overdue_loans_async(db, now=now)

        await db.commit()


async def process_unused_approved_credit_expiry():
    """定时清理超过有效期且未下单的审批额度。

    :return: None
    """
    async with AsyncSessionLocal() as db:
        await expire_unused_approved_credits(db, now=datetime.now())


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(process_overdue_loans, "cron", hour=0, minute=1, id="daily-overdue-check", replace_existing=True,max_instances=1)
    scheduler.add_job(process_unused_approved_credit_expiry, "cron", hour=0, minute=1, id="daily-approved-credit-expiry", replace_existing=True,max_instances=1)
    # scheduler.add_job(process_overdue_loans, "interval", hour=1, id="debug-overdue-check", replace_existing=True)
    scheduler.start()
