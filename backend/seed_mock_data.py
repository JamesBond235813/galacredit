from datetime import datetime, timedelta
from typing import Optional

from app.core.database import SessionLocal, initialize_database
from app.models.channel import Channel
from app.models.loan import Loan
from app.models.user import User
from app.services.audit import log_user_event
from app.services.loan_amounts import DEFAULT_FEE_RATE, calculate_total_repayment_amount, sync_loan_fee_fields

TEST_PHONE_PREFIX = "1999100"
TOTAL_USERS = 100

NAME_POOL = [
    "张晨", "李浩", "王悦", "赵磊", "刘洋", "陈静", "杨帆", "黄莹",
    "周凯", "吴倩", "徐峰", "孙婷", "胡斌", "朱琳", "高远", "林薇",
]
RELATIONS = ["父母", "子女", "兄弟姐妹", "同事", "朋友"]
AMOUNTS = [1000, 1500, 2000, 3000]
TERMS = [7, 14, 21, 28]
FEE_RATES = [0.2, 0.3, 0.4, 0.5, 0.6]
OPERATORS = ["admin", "xiaojiang"]
CHANNEL_POOL = [
    ("xiaojiang", "小江"),
    ("chenchen", "陈晨"),
    ("laoliu", "老刘"),
    ("maying", "马莹"),
    ("zhouzhou", "周舟"),
]

STATUS_PLAN = [
    ("INIT", 10),
    ("REVIEWING", 15),
    ("APPROVED", 12),
    ("REJECTED", 8),
    ("WITHDRAWING", 15),
    ("DISBURSED_TODAY", 10),
    ("DISBURSED_TOMORROW", 8),
    ("DISBURSED_ACTIVE", 7),
    ("OVERDUE_1", 5),
    ("OVERDUE_2", 4),
    ("OVERDUE_7", 4),
    ("SETTLED", 2),
]


def due_date_from_today(now: datetime, day_offset: int, hour: int) -> datetime:
    base = datetime(now.year, now.month, now.day)
    return base + timedelta(days=day_offset, hours=hour)


def calc_due_date(disbursed_at: datetime, term_days: int):
    return disbursed_at + timedelta(days=max(int(term_days) - 1, 0))


def make_phone(index: int) -> str:
    return f"{int(TEST_PHONE_PREFIX) * 10000 + index:011d}"


def make_id_card(index: int) -> str:
    month = index % 12 + 1
    day = index % 28 + 1
    return f"1101011990{month:02d}{day:02d}{index:04d}"


def choose_name(index: int) -> str:
    return f"{NAME_POOL[index % len(NAME_POOL)]}{index:03d}"


def set_event_time(event, when: datetime):
    event.created_at = when
    return event


def add_event(db, *, user, loan, when: datetime, event_type: str, title: str, detail, actor_type="USER", operator_name=None):
    event = log_user_event(
        db,
        user=user,
        loan=loan,
        actor_type=actor_type,
        operator_name=operator_name,
        event_type=event_type,
        title=title,
        detail=detail,
    )
    set_event_time(event, when)


def populate_identity(user: User, index: int, ocr_time: datetime, face_time: Optional[datetime] = None):
    user.name = choose_name(index)
    user.id_card_num = make_id_card(index)
    user.id_address = f"北京市朝阳区建国路 {80 + index} 号"
    user.id_expiry = "2020.01.01-2040.01.01"
    user.ocr_submitted_at = ocr_time
    if face_time:
        user.face_auth_status = "PASSED"
        user.face_auth_at = face_time
    else:
        user.face_auth_status = "PENDING"
        user.face_auth_at = None


def populate_application(user: User, index: int, submitted_at: datetime):
    user.emergency_contact1_name = f"联系人A{index:03d}"
    user.emergency_contact1_relation = RELATIONS[index % len(RELATIONS)]
    user.emergency_contact1_phone = f"139000{index:05d}"
    user.emergency_contact2_name = f"联系人B{index:03d}"
    user.emergency_contact2_relation = RELATIONS[(index + 2) % len(RELATIONS)]
    user.emergency_contact2_phone = f"138000{index:05d}"
    user.application_submitted_at = submitted_at


def create_previous_settled_loan(db, user: User, index: int, now: datetime):
    credit_limit = AMOUNTS[(index + 1) % len(AMOUNTS)]
    term_days = TERMS[(index + 1) % len(TERMS)]
    fee_rate = FEE_RATES[(index + 1) % len(FEE_RATES)]
    disbursed_at = now - timedelta(days=40 + index % 6)
    loan = Loan(
        user_id=user.id,
        status="SETTLED",
        credit_limit=credit_limit,
        fee_rate=fee_rate,
        term_days=term_days,
        penalty_amount=0,
        review_note="历史复借订单，已结清",
        approved_at=disbursed_at - timedelta(days=1),
        created_at=disbursed_at - timedelta(days=2),
        disbursed_at=disbursed_at,
        due_date=calc_due_date(disbursed_at, term_days),
        repaid_amount=0,
        reduction_amount=0,
    )
    sync_loan_fee_fields(loan)
    loan.reduction_amount = round(loan.fee_amount * 0.1, 2)
    loan.repaid_amount = round(calculate_total_repayment_amount(loan) - loan.reduction_amount, 2)
    db.add(loan)
    db.flush()

    add_event(
        db,
        user=user,
        loan=loan,
        when=loan.created_at,
        event_type="APPLICATION_SUBMIT",
        title="历史借款提交",
        detail="模拟历史已结清订单，用于测试复借统计。",
    )
    add_event(
        db,
        user=user,
        loan=loan,
        when=loan.approved_at,
        actor_type="ADMIN",
        operator_name=OPERATORS[index % len(OPERATORS)],
        event_type="ADMIN_APPROVED",
        title="历史订单审批通过",
        detail=f"额度 {credit_limit} 元；期限 {term_days} 天；综合息费率 {fee_rate * 100:.0f}%",
    )
    add_event(
        db,
        user=user,
        loan=loan,
        when=loan.disbursed_at,
        actor_type="ADMIN",
        operator_name=OPERATORS[(index + 1) % len(OPERATORS)],
        event_type="ADMIN_DISBURSED",
        title="历史订单放款完成",
        detail=f"已放款 {credit_limit} 元。",
    )
    add_event(
        db,
        user=user,
        loan=loan,
        when=loan.due_date + timedelta(hours=3),
        actor_type="ADMIN",
        operator_name=OPERATORS[index % len(OPERATORS)],
        event_type="ADMIN_SETTLED",
        title="历史订单已结清",
        detail="历史订单用于测试复借统计，已完成结清。",
    )


def build_current_loan(db, user: User, status_code: str, index: int, now: datetime) -> Loan:
    credit_limit = AMOUNTS[index % len(AMOUNTS)]
    term_days = TERMS[index % len(TERMS)]
    fee_rate = FEE_RATES[index % len(FEE_RATES)]
    created_at = now - timedelta(days=18 - (index % 7), hours=3 + index % 5)

    loan = Loan(
        user_id=user.id,
        status="INIT",
        credit_limit=0,
        fee_rate=DEFAULT_FEE_RATE,
        fee_amount=0,
        term_days=None,
        due_date=None,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        review_note=None,
        approved_at=None,
        reminder_count=0,
        last_reminded_at=None,
        collection_count=0,
        last_collection_at=None,
        collection_note=None,
        created_at=created_at,
        disbursed_at=None,
    )
    db.add(loan)
    db.flush()

    if status_code == "INIT":
        return loan

    ocr_time = created_at + timedelta(hours=3)
    face_time = ocr_time + timedelta(hours=2)
    populate_identity(user, index, ocr_time, face_time)
    add_event(db, user=user, loan=loan, when=ocr_time, event_type="OCR_SUBMIT", title="提交身份证识别", detail="已上传身份证正反面并完成模拟识别。")
    add_event(db, user=user, loan=loan, when=face_time, event_type="FACE_AUTH_PASS", title="完成人脸识别", detail="人脸识别及三要素校验通过。")

    if status_code == "INIT":
        return loan

    application_time = face_time + timedelta(hours=2)
    populate_application(user, index, application_time)
    loan.created_at = application_time
    add_event(
        db,
        user=user,
        loan=loan,
        when=application_time,
        event_type="APPLICATION_SUBMIT",
        title="提交补充资料",
        detail="联系人信息已提交，进入额度审核。",
    )

    if status_code == "REVIEWING":
        loan.status = "REVIEWING"
        return loan

    review_time = application_time + timedelta(hours=6)

    if status_code == "REJECTED":
        loan.status = "REJECTED"
        loan.credit_limit = 0
        loan.term_days = None
        loan.review_note = "资料完整，但暂不符合当前授信策略。"
        loan.approved_at = None
        user.approved_limit = 0
        add_event(
            db,
            user=user,
            loan=loan,
            when=review_time,
            actor_type="ADMIN",
            operator_name=OPERATORS[index % len(OPERATORS)],
            event_type="ADMIN_REJECTED",
            title="后台审批拒绝",
            detail=loan.review_note,
        )
        return loan

    loan.status = "APPROVED"
    loan.credit_limit = credit_limit
    loan.fee_rate = fee_rate
    loan.term_days = term_days
    loan.review_note = "审批通过，等待用户提现或后台确认放款。"
    loan.approved_at = review_time
    sync_loan_fee_fields(loan)
    user.approved_limit = int(credit_limit)
    add_event(
        db,
        user=user,
        loan=loan,
        when=review_time,
        actor_type="ADMIN",
        operator_name=OPERATORS[index % len(OPERATORS)],
        event_type="ADMIN_APPROVED",
        title="后台审批通过",
        detail=f"额度 {credit_limit} 元；期限 {term_days} 天；综合息费率 {fee_rate * 100:.0f}%。",
    )

    if status_code == "APPROVED":
        return loan

    withdraw_time = review_time + timedelta(hours=8)
    loan.status = "WITHDRAWING"
    add_event(
        db,
        user=user,
        loan=loan,
        when=withdraw_time,
        event_type="WITHDRAW_APPLY",
        title="提交提现申请",
        detail=f"用户申请提现 {credit_limit} 元，等待后台线下放款。",
    )

    if status_code == "WITHDRAWING":
        return loan

    if status_code == "DISBURSED_TODAY":
        due_date = due_date_from_today(now, 0, 11 + index % 6)
    elif status_code == "DISBURSED_TOMORROW":
        due_date = due_date_from_today(now, 1, 10 + index % 6)
    elif status_code == "DISBURSED_ACTIVE":
        due_date = due_date_from_today(now, 3 + index % 5, 13)
    elif status_code == "OVERDUE_1":
        due_date = due_date_from_today(now, -1, 10)
    elif status_code == "OVERDUE_2":
        due_date = due_date_from_today(now, -2, 10)
    elif status_code == "OVERDUE_7":
        due_date = due_date_from_today(now, -7, 10)
    else:
        due_date = due_date_from_today(now, -3, 12)

    disbursed_at = due_date - timedelta(days=term_days - 1)
    loan.status = "DISBURSED"
    loan.disbursed_at = disbursed_at
    loan.due_date = due_date
    loan.penalty_amount = 0

    add_event(
        db,
        user=user,
        loan=loan,
        when=disbursed_at,
        actor_type="ADMIN",
        operator_name=OPERATORS[(index + 1) % len(OPERATORS)],
        event_type="ADMIN_DISBURSED",
        title="后台确认放款",
        detail=f"线下已放款 {credit_limit} 元；到期日 {due_date.strftime('%Y-%m-%d %H:%M:%S')}。",
    )

    if status_code == "DISBURSED_TODAY":
        loan.reminder_count = 1 + index % 2
        loan.last_reminded_at = due_date_from_today(now, 0, 8 + index % 3)
        add_event(
            db,
            user=user,
            loan=loan,
            when=loan.last_reminded_at,
            actor_type="ADMIN",
            operator_name=OPERATORS[index % len(OPERATORS)],
            event_type="ADMIN_REMIND",
            title="登记还款提醒",
            detail=f"第 {loan.reminder_count} 次提醒；备注：今日到期，已电话提醒。",
        )
    elif status_code == "DISBURSED_ACTIVE":
        if index % 2 == 0:
            loan.repaid_amount = round(min(credit_limit * 0.25, calculate_total_repayment_amount(loan)), 2)
            add_event(
                db,
                user=user,
                loan=loan,
                when=disbursed_at + timedelta(days=1),
                actor_type="ADMIN",
                operator_name=OPERATORS[index % len(OPERATORS)],
                event_type="ADMIN_FINANCE_RECONCILE",
                title="财务登记平账",
                detail=f"登记收款 {loan.repaid_amount:.2f} 元；剩余待还 {calculate_total_repayment_amount(loan) - loan.repaid_amount:.2f} 元。",
            )

    if status_code.startswith("OVERDUE"):
        loan.status = "OVERDUE"
        days = 1 if status_code == "OVERDUE_1" else 2 if status_code == "OVERDUE_2" else 7
        loan.penalty_amount = float(days * 10)
        loan.collection_count = 1 + index % 3
        loan.last_collection_at = now - timedelta(hours=2 + index % 4)
        loan.collection_note = f"逾期 {days} 天，已联系客户跟进还款。"
        if days >= 2:
            loan.reduction_amount = float(10 if days == 2 else 30)
        if days >= 7:
            loan.repaid_amount = float(credit_limit * 0.3)

        add_event(
            db,
            user=user,
            loan=loan,
            when=loan.due_date + timedelta(hours=1),
            actor_type="SYSTEM",
            event_type="AUTO_OVERDUE",
            title="系统自动转为逾期",
            detail=f"最后还款日已过，订单自动转为逾期 {days} 天。",
        )
        add_event(
            db,
            user=user,
            loan=loan,
            when=loan.last_collection_at,
            actor_type="ADMIN",
            operator_name=OPERATORS[index % len(OPERATORS)],
            event_type="ADMIN_COLLECT",
            title="登记催收跟进",
            detail=f"第 {loan.collection_count} 次催收；备注：{loan.collection_note}",
        )

    if status_code == "SETTLED":
        loan.status = "SETTLED"
        loan.reduction_amount = round(loan.fee_amount * 0.15, 2)
        loan.repaid_amount = round(calculate_total_repayment_amount(loan) - loan.reduction_amount, 2)
        add_event(
            db,
            user=user,
            loan=loan,
            when=due_date + timedelta(hours=4),
            actor_type="ADMIN",
            operator_name=OPERATORS[index % len(OPERATORS)],
            event_type="ADMIN_SETTLED",
            title="后台确认结清",
            detail=f"已结清；累计已还 {loan.repaid_amount:.2f} 元；减免 {loan.reduction_amount:.2f} 元。",
        )

    return loan


def create_user_record(db, index: int, status_code: str, now: datetime):
    channel = db.query(Channel).filter(Channel.channel_name == CHANNEL_POOL[index % len(CHANNEL_POOL)][0]).first()
    created_at = now - timedelta(days=20 - index % 9, hours=2 + index % 6)
    user = User(
        phone=make_phone(index),
        name=None,
        face_auth_status="PENDING",
        approved_limit=0,
        source_channel=channel,
        channel_bound_at=created_at,
        last_channel_visit_at=created_at,
        created_at=created_at,
        last_login_at=created_at + timedelta(hours=1),
    )
    db.add(user)
    db.flush()

    if status_code in {"APPROVED", "WITHDRAWING", "DISBURSED_TODAY", "DISBURSED_TOMORROW", "DISBURSED_ACTIVE", "OVERDUE_1", "OVERDUE_2", "OVERDUE_7", "SETTLED"} and index % 8 == 0:
        create_previous_settled_loan(db, user, index, now)

    loan = build_current_loan(db, user, status_code, index, now)

    add_event(
        db,
        user=user,
        loan=loan,
        when=created_at,
        event_type="USER_REGISTER",
        title="模拟用户注册",
        detail=f"创建模拟用户 {user.phone}，归属渠道 {channel.sales_name}（{channel.channel_name}），用于后台联调。",
    )


def ensure_seed_channels(db):
    channels = []
    for channel_name, sales_name in CHANNEL_POOL:
        channel = db.query(Channel).filter(Channel.channel_name == channel_name).first()
        if channel is None:
            channel = Channel(channel_name=channel_name, sales_name=sales_name, status="ACTIVE", note="模拟渠道数据")
            db.add(channel)
            db.flush()
        channels.append(channel)
    return channels


def clear_previous_seed_data(db):
    seeded_users = (
        db.query(User)
        .filter(User.phone.like(f"{TEST_PHONE_PREFIX}%"))
        .all()
    )
    for user in seeded_users:
        db.delete(user)
    db.commit()
    return len(seeded_users)


def seed_mock_data():
    initialize_database()
    db = SessionLocal()
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    planned_total = sum(count for _, count in STATUS_PLAN)
    if planned_total != TOTAL_USERS:
        raise ValueError(f"状态规划总数 {planned_total} 与目标总数 {TOTAL_USERS} 不一致")

    try:
        ensure_seed_channels(db)
        removed_count = clear_previous_seed_data(db)

        current_index = 0
        status_counter = {}
        for status_code, count in STATUS_PLAN:
            for _ in range(count):
                create_user_record(db, current_index, status_code, now)
                status_counter[status_code] = status_counter.get(status_code, 0) + 1
                current_index += 1

        db.commit()

        print(f"清理旧模拟用户 {removed_count} 条。")
        print(f"新增模拟用户 {current_index} 条。")
        for status_code, count in status_counter.items():
            print(f"{status_code}: {count}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_mock_data()
