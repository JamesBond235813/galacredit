import asyncio
import logging
import time
import pymysql
from sqlalchemy import create_engine, event, inspect, text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings
from app.services.admin_permissions import serialize_admin_permissions, serialize_admin_roles

sql_logger = logging.getLogger("app.sql")

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
)
async_engine = create_async_engine(
    settings.SQLALCHEMY_ASYNC_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
)


def _bind_sql_logging(db_engine):
    @event.listens_for(db_engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(db_engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_time = conn.info.get("query_start_time", []).pop(-1) if conn.info.get("query_start_time") else None
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2) if start_time else 0.0
        sql_logger.debug(
            "sql_exec duration_ms=%s executemany=%s statement=%s parameters=%s",
            duration_ms,
            executemany,
            statement,
            parameters,
            extra={"duration_ms": duration_ms},
        )
        if duration_ms >= float(settings.SQL_SLOW_MS):
            sql_logger.warning(
                "sql_slow duration_ms=%s threshold_ms=%s executemany=%s statement=%s parameters=%s",
                duration_ms,
                settings.SQL_SLOW_MS,
                executemany,
                statement,
                parameters,
                extra={"duration_ms": duration_ms},
            )


_bind_sql_logging(engine)
_bind_sql_logging(async_engine.sync_engine)

AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

SCHEMA_PATCHES = {
    "users": {
        "emergency_contact1_name": "ALTER TABLE users ADD COLUMN emergency_contact1_name VARCHAR(50) NULL",
        "emergency_contact1_relation": "ALTER TABLE users ADD COLUMN emergency_contact1_relation VARCHAR(20) NULL",
        "emergency_contact1_phone": "ALTER TABLE users ADD COLUMN emergency_contact1_phone VARCHAR(20) NULL",
        "emergency_contact2_name": "ALTER TABLE users ADD COLUMN emergency_contact2_name VARCHAR(50) NULL",
        "emergency_contact2_relation": "ALTER TABLE users ADD COLUMN emergency_contact2_relation VARCHAR(20) NULL",
        "emergency_contact2_phone": "ALTER TABLE users ADD COLUMN emergency_contact2_phone VARCHAR(20) NULL",
        "face_auth_status": "ALTER TABLE users ADD COLUMN face_auth_status VARCHAR(20) DEFAULT 'PENDING'",
        "real_name_status": "ALTER TABLE users ADD COLUMN real_name_status VARCHAR(20) DEFAULT 'UNVERIFIED'",
        "face_auth_at": "ALTER TABLE users ADD COLUMN face_auth_at DATETIME NULL",
        "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL",
        "ocr_submitted_at": "ALTER TABLE users ADD COLUMN ocr_submitted_at DATETIME NULL",
        "application_submitted_at": "ALTER TABLE users ADD COLUMN application_submitted_at DATETIME NULL",
        "source_channel_id": "ALTER TABLE users ADD COLUMN source_channel_id INT NULL",
        "channel_bound_at": "ALTER TABLE users ADD COLUMN channel_bound_at DATETIME NULL",
        "last_channel_visit_at": "ALTER TABLE users ADD COLUMN last_channel_visit_at DATETIME NULL",
        "location_latitude": "ALTER TABLE users ADD COLUMN location_latitude VARCHAR(32) NULL",
        "location_longitude": "ALTER TABLE users ADD COLUMN location_longitude VARCHAR(32) NULL",
        "location_accuracy": "ALTER TABLE users ADD COLUMN location_accuracy VARCHAR(32) NULL",
        "location_address": "ALTER TABLE users ADD COLUMN location_address VARCHAR(255) NULL",
        "location_province": "ALTER TABLE users ADD COLUMN location_province VARCHAR(50) NULL",
        "location_city": "ALTER TABLE users ADD COLUMN location_city VARCHAR(50) NULL",
        "location_district": "ALTER TABLE users ADD COLUMN location_district VARCHAR(50) NULL",
        "location_street": "ALTER TABLE users ADD COLUMN location_street VARCHAR(80) NULL",
        "location_source": "ALTER TABLE users ADD COLUMN location_source VARCHAR(30) NULL",
        "location_updated_at": "ALTER TABLE users ADD COLUMN location_updated_at DATETIME NULL",
    },
    "loans": {
        "approved_credit_limit": "ALTER TABLE loans ADD COLUMN approved_credit_limit FLOAT DEFAULT 0",
        "fee_rate": "ALTER TABLE loans ADD COLUMN fee_rate FLOAT DEFAULT 0.6",
        "fee_amount": "ALTER TABLE loans ADD COLUMN fee_amount FLOAT DEFAULT 0",
        "review_note": "ALTER TABLE loans ADD COLUMN review_note VARCHAR(255) NULL",
        "approved_at": "ALTER TABLE loans ADD COLUMN approved_at DATETIME NULL",
        "reminder_count": "ALTER TABLE loans ADD COLUMN reminder_count INT DEFAULT 0",
        "last_reminded_at": "ALTER TABLE loans ADD COLUMN last_reminded_at DATETIME NULL",
        "collection_count": "ALTER TABLE loans ADD COLUMN collection_count INT DEFAULT 0",
        "last_collection_at": "ALTER TABLE loans ADD COLUMN last_collection_at DATETIME NULL",
        "collection_note": "ALTER TABLE loans ADD COLUMN collection_note VARCHAR(255) NULL",
        "repay_attempt_count": "ALTER TABLE loans ADD COLUMN repay_attempt_count INT DEFAULT 0",
        "review_admin_id": "ALTER TABLE loans ADD COLUMN review_admin_id INT NULL",
        "collection_admin_id": "ALTER TABLE loans ADD COLUMN collection_admin_id INT NULL",
        "collection_transferred_at": "ALTER TABLE loans ADD COLUMN collection_transferred_at DATETIME NULL",
        "repaid_amount": "ALTER TABLE loans ADD COLUMN repaid_amount FLOAT DEFAULT 0",
        "reduction_amount": "ALTER TABLE loans ADD COLUMN reduction_amount FLOAT DEFAULT 0",
        "paid_penalty_amount": "ALTER TABLE loans ADD COLUMN paid_penalty_amount FLOAT DEFAULT 0",
        "reduced_penalty_amount": "ALTER TABLE loans ADD COLUMN reduced_penalty_amount FLOAT DEFAULT 0",
        "product_id": "ALTER TABLE loans ADD COLUMN product_id INT NULL",
        "product_name": "ALTER TABLE loans ADD COLUMN product_name VARCHAR(120) NULL",
        "rights_title": "ALTER TABLE loans ADD COLUMN rights_title VARCHAR(120) NULL",
        "rights_desc": "ALTER TABLE loans ADD COLUMN rights_desc VARCHAR(255) NULL",
        "rights_price": "ALTER TABLE loans ADD COLUMN rights_price FLOAT DEFAULT 0",
        "ecard_face_value": "ALTER TABLE loans ADD COLUMN ecard_face_value FLOAT DEFAULT 0",
        "product_total_price": "ALTER TABLE loans ADD COLUMN product_total_price FLOAT DEFAULT 0",
        "product_term_days": "ALTER TABLE loans ADD COLUMN product_term_days INT NULL",
        "ecard_account": "ALTER TABLE loans ADD COLUMN ecard_account VARCHAR(100) NULL",
        "ecard_password": "ALTER TABLE loans ADD COLUMN ecard_password VARCHAR(100) NULL",
        "ecard_expires_at": "ALTER TABLE loans ADD COLUMN ecard_expires_at DATETIME NULL",
        "order_no": "ALTER TABLE loans ADD COLUMN order_no VARCHAR(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '订单号'",
    },
    "channels": {
        "sales_name": "ALTER TABLE channels ADD COLUMN sales_name VARCHAR(50) NOT NULL DEFAULT '未命名业务员'",
        "status": "ALTER TABLE channels ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'",
        "note": "ALTER TABLE channels ADD COLUMN note VARCHAR(255) NULL",
    },
    "user_events": {
        "operator_name": "ALTER TABLE user_events ADD COLUMN operator_name VARCHAR(50) NULL",
    },
    "risk_control_report": {
        "source": "ALTER TABLE risk_control_report ADD COLUMN source VARCHAR(20) NULL",
    },
    "admins": {
        "roles": "ALTER TABLE admins ADD COLUMN roles TEXT NULL",
        "permissions": "ALTER TABLE admins ADD COLUMN permissions TEXT NULL",
        "updated_at": "ALTER TABLE admins ADD COLUMN updated_at DATETIME NULL",
    },
}

SCHEMA_REMOVALS = {
    "users": (
        "bank_card_num",
        "bank_account_name",
        "bank_name",
    )
}


def ensure_database_exists():
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=int(settings.MYSQL_PORT),
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


def sync_legacy_schema():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, columns in SCHEMA_REMOVALS.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name in columns:
                if column_name in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"))

        for table_name, columns in SCHEMA_PATCHES.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(ddl))

        if "users" in existing_tables:
            connection.execute(
                text(
                    """
                    UPDATE users
                    SET real_name_status = 'AUTHED'
                    WHERE face_auth_status = 'PASSED'
                      AND (real_name_status IS NULL OR real_name_status = 'UNVERIFIED')
                    """
                )
            )


async def ensure_default_admins():
    from app.core.security import get_password_hash
    from app.models.admin import Admin

    async with AsyncSessionLocal() as db:
        default_accounts = {
            "admin": "admin123",
            "xiaojiang": "admin123",
        }
        changed = False

        for username, password in default_accounts.items():
            exists = (await db.execute(select(Admin).where(Admin.username == username))).scalar_one_or_none()
            roles = serialize_admin_roles(["ADMIN"])
            permissions = serialize_admin_permissions(None)
            if exists:
                if exists.roles != roles:
                    exists.roles = roles
                    changed = True
                if exists.permissions != permissions:
                    exists.permissions = permissions
                    changed = True
                continue

            db.add(
                Admin(
                    username=username,
                    password_hash=get_password_hash(password),
                    roles=roles,
                    permissions=permissions,
                )
            )
            changed = True

        if changed:
            await db.commit()


async def ensure_default_products():
    from app.models.product import Product

    async with AsyncSessionLocal() as db:
        default_products = [
            {
                "name": "京东E卡1000元 + 韶关丹霞山2日旅游",
                "ecard_face_value": 1000.0,
                "rights_price": 600.0,
                "rights_title": "韶关丹霞山2日旅游",
                "rights_desc": "酒店住宿3晚 + 丹霞山公园门票4张 + 酒店晚餐4顿",
                "term_days": 7,
                "payment_amount": 1600.0,
            },
            {
                "name": "京东E卡1500元 + 韶关丹霞山3日旅游",
                "ecard_face_value": 1500.0,
                "rights_price": 900.0,
                "rights_title": "韶关丹霞山3日旅游",
                "rights_desc": "酒店住宿4晚 + 丹霞山公园门票2张 + 酒店晚餐3顿",
                "term_days": 14,
                "payment_amount": 2400.0,
            },
            {
                "name": "京东E卡2000元 + 韶关丹霞山4日旅游",
                "ecard_face_value": 2000.0,
                "rights_price": 1200.0,
                "rights_title": "韶关丹霞山4日旅游",
                "rights_desc": "酒店住宿4晚 + 丹霞山公园门票6张 + 酒店晚餐4顿",
                "term_days": 21,
                "payment_amount": 3200.0,
            },
        ]

        changed = False
        for item in default_products:
            exists = (await db.execute(select(Product).where(Product.name == item["name"]))).scalar_one_or_none()
            if exists:
                continue
            db.add(Product(**item))
            changed = True

        if changed:
            await db.commit()


async def migrate_loan_to_new_semantics():
    from app.models.loan import Loan
    from app.models.product import Product

    def _round_money(value):
        return round(float(value or 0), 2)

    async with AsyncSessionLocal() as db:
        products = (await db.execute(select(Product))).scalars().all()
        rights_desc_preset = {
            1000: "酒店住宿3晚 + 丹霞山公园门票4张 + 酒店晚餐4顿",
            1500: "酒店住宿4晚 + 丹霞山公园门票2张 + 酒店晚餐3顿",
            2000: "酒店住宿4晚 + 丹霞山公园门票6张 + 酒店晚餐4顿",
        }

        loans = (await db.execute(select(Loan))).scalars().all()
        changed = False
        for loan in loans:
            credit_limit = _round_money(getattr(loan, "credit_limit", 0))
            ecard_face_value = _round_money(getattr(loan, "ecard_face_value", 0))
            fee_rate = float(getattr(loan, "fee_rate", 0) or 0)
            fee_amount = _round_money(getattr(loan, "fee_amount", 0))
            rights_price = _round_money(getattr(loan, "rights_price", 0))

            if credit_limit <= 0 and ecard_face_value > 0:
                credit_limit = ecard_face_value
                loan.credit_limit = ecard_face_value
                changed = True

            if fee_amount <= 0 and credit_limit > 0 and fee_rate > 0:
                fee_amount = _round_money(credit_limit * fee_rate)
                loan.fee_amount = fee_amount
                changed = True

            if rights_price <= 0 and fee_amount > 0:
                rights_price = fee_amount
                loan.rights_price = rights_price
                changed = True

            if fee_amount <= 0 and rights_price > 0:
                fee_amount = rights_price
                loan.fee_amount = fee_amount
                changed = True

            if not getattr(loan, "approved_credit_limit", 0):
                loan.approved_credit_limit = credit_limit
                changed = True

            if ecard_face_value <= 0 and credit_limit > 0:
                loan.ecard_face_value = credit_limit
                ecard_face_value = credit_limit
                changed = True

            if not getattr(loan, "product_total_price", 0):
                loan.product_total_price = _round_money(credit_limit + fee_amount)
                changed = True

            if not getattr(loan, "product_term_days", None) and getattr(loan, "term_days", None):
                loan.product_term_days = loan.term_days
                changed = True

            if not getattr(loan, "rights_title", None):
                loan.rights_title = "韶关丹霞山旅游权益"
                changed = True

            if not getattr(loan, "rights_desc", None):
                face_value_int = int(ecard_face_value) if float(ecard_face_value).is_integer() else None
                loan.rights_desc = rights_desc_preset.get(face_value_int, "韶关丹霞山旅游权益（历史迁移订单）")
                changed = True

            if not getattr(loan, "product_name", None) and credit_limit > 0:
                loan.product_name = f"京东E卡{int(credit_limit) if credit_limit.is_integer() else credit_limit}元 + 韶关丹霞山旅游权益"
                changed = True

            if not getattr(loan, "product_id", None):
                term_days = getattr(loan, "product_term_days", None) or getattr(loan, "term_days", None)
                matched = next(
                    (
                        item
                        for item in products
                        if _round_money(getattr(item, "ecard_face_value", 0)) == _round_money(ecard_face_value or credit_limit)
                        and _round_money(getattr(item, "rights_price", 0)) == _round_money(rights_price or fee_amount)
                        and int(getattr(item, "term_days", 0) or 0) == int(term_days or 0)
                    ),
                    None,
                )
                if matched:
                    loan.product_id = matched.id
                    changed = True

        if changed:
            await db.commit()


async def migrate_user_events_to_new_semantics():
    from app.models.user_event import UserEvent

    text_pairs = [
        ("提交提现申请", "提交信用下单"),
        ("后台确认放款", "后台确认发卡"),
        ("历史订单放款完成", "历史订单发卡完成"),
        ("历史借款提交", "历史订单提交"),
        ("申请提现金额", "下单商品支付金额"),
        ("用户申请提现", "用户提交信用下单"),
        ("等待后台放款确认", "等待后台发卡确认"),
        ("等待后台线下放款", "等待后台线下发卡"),
        ("放款金额", "E卡发放面值"),
        ("线下已放款", "线下已发卡（E卡面值）"),
        ("已放款", "已发卡（E卡面值）"),
        ("初始借款单", "初始订单"),
        ("借款单", "订单"),
        ("借款", "订单"),
        ("提现", "信用下单"),
        ("放款", "发卡"),
    ]

    async with AsyncSessionLocal() as db:
        events = (await db.execute(select(UserEvent))).scalars().all()
        changed = False
        for event in events:
            original_type = (event.event_type or "").strip()
            original_title = event.title or ""
            original_detail = event.detail or ""

            next_type = original_type
            if original_type == "WITHDRAW_APPLY":
                next_type = "ORDER_SUBMIT"
            elif original_type == "ADMIN_DISBURSED":
                next_type = "ADMIN_CARD_ISSUED"

            next_title = original_title
            next_detail = original_detail
            for old_text, new_text in text_pairs:
                next_title = next_title.replace(old_text, new_text)
                next_detail = next_detail.replace(old_text, new_text)

            if next_type != original_type:
                event.event_type = next_type
                changed = True
            if next_title != original_title:
                event.title = next_title
                changed = True
            if next_detail != original_detail:
                event.detail = next_detail
                changed = True

        if changed:
            await db.commit()


def initialize_database():
    ensure_database_exists()

    # 导入模型以注册 metadata，再统一建表和补列
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    sync_legacy_schema()
    asyncio.run(ensure_default_admins())
    asyncio.run(ensure_default_products())
    asyncio.run(migrate_loan_to_new_semantics())
    asyncio.run(migrate_user_events_to_new_semantics())


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


async def get_async_db():
    async for db in get_db():
        yield db
