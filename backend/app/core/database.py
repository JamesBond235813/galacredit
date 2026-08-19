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
        "blacklist_hit": "ALTER TABLE users ADD COLUMN blacklist_hit TINYINT(1) NOT NULL DEFAULT 0",
        "blacklist_reason": "ALTER TABLE users ADD COLUMN blacklist_reason VARCHAR(255) NULL",
        "blacklist_checked_at": "ALTER TABLE users ADD COLUMN blacklist_checked_at DATETIME NULL",
        "risk_list_hit": "ALTER TABLE users ADD COLUMN risk_list_hit TINYINT(1) NOT NULL DEFAULT 0 COMMENT '风险名单命中状态'",
        "risk_list_source": "ALTER TABLE users ADD COLUMN risk_list_source VARCHAR(50) NULL COMMENT '风险名单命中来源'",
        "risk_list_reason": "ALTER TABLE users ADD COLUMN risk_list_reason VARCHAR(255) NULL COMMENT '风险名单命中原因'",
        "risk_list_checked_at": "ALTER TABLE users ADD COLUMN risk_list_checked_at DATETIME NULL COMMENT '风险名单最近核查时间'",
        "id_card_front_image": "ALTER TABLE users ADD COLUMN id_card_front_image VARCHAR(255) NULL",
        "id_card_back_image": "ALTER TABLE users ADD COLUMN id_card_back_image VARCHAR(255) NULL",
        "face_image": "ALTER TABLE users ADD COLUMN face_image VARCHAR(255) NULL",
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
        "location_risk_blocked": "ALTER TABLE users ADD COLUMN location_risk_blocked TINYINT(1) NOT NULL DEFAULT 0",
        "location_risk_reason": "ALTER TABLE users ADD COLUMN location_risk_reason VARCHAR(255) NULL",
        "location_risk_at": "ALTER TABLE users ADD COLUMN location_risk_at DATETIME NULL",
        "available_credit_limit": "ALTER TABLE users ADD COLUMN available_credit_limit FLOAT DEFAULT 0",
        "overdue_credit_locked": "ALTER TABLE users ADD COLUMN overdue_credit_locked TINYINT(1) NOT NULL DEFAULT 0",
    },
    "loans": {
        "approved_credit_limit": "ALTER TABLE loans ADD COLUMN approved_credit_limit FLOAT DEFAULT 0",
        "fee_rate": "ALTER TABLE loans ADD COLUMN fee_rate FLOAT DEFAULT 0.6",
        "fee_amount": "ALTER TABLE loans ADD COLUMN fee_amount FLOAT DEFAULT 0",
        "nominal_loan_amount": "ALTER TABLE loans ADD COLUMN nominal_loan_amount FLOAT NOT NULL DEFAULT 0",
        "upfront_fee_amount": "ALTER TABLE loans ADD COLUMN upfront_fee_amount FLOAT NOT NULL DEFAULT 0",
        "actual_disbursement_amount": "ALTER TABLE loans ADD COLUMN actual_disbursement_amount FLOAT NOT NULL DEFAULT 0",
        "total_repayment_amount_snapshot": "ALTER TABLE loans ADD COLUMN total_repayment_amount_snapshot FLOAT NOT NULL DEFAULT 0",
        "interest_start_day": "ALTER TABLE loans ADD COLUMN interest_start_day INT NOT NULL DEFAULT 1",
        "repayment_due_day": "ALTER TABLE loans ADD COLUMN repayment_due_day INT NOT NULL DEFAULT 7",
        "installment_count": "ALTER TABLE loans ADD COLUMN installment_count INT NOT NULL DEFAULT 1",
        "installment_ratios_json": "ALTER TABLE loans ADD COLUMN installment_ratios_json VARCHAR(2000) NULL",
        "fee_components_json": "ALTER TABLE loans ADD COLUMN fee_components_json VARCHAR(2000) NULL",
        "momo_disbursement_reference": "ALTER TABLE loans ADD COLUMN momo_disbursement_reference VARCHAR(100) NULL",
        "momo_repayment_reference": "ALTER TABLE loans ADD COLUMN momo_repayment_reference VARCHAR(100) NULL",
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
        "other_fee_amount": "ALTER TABLE loans ADD COLUMN other_fee_amount FLOAT DEFAULT 0 COMMENT '已登记其他费用'",
        "paid_penalty_amount": "ALTER TABLE loans ADD COLUMN paid_penalty_amount FLOAT DEFAULT 0",
        "reduced_penalty_amount": "ALTER TABLE loans ADD COLUMN reduced_penalty_amount FLOAT DEFAULT 0",
        "actual_repayment_date": "ALTER TABLE loans ADD COLUMN actual_repayment_date DATE NULL COMMENT '最近一次实际还款日期'",
        "product_id": "ALTER TABLE loans ADD COLUMN product_id INT NULL",
        "product_type": "ALTER TABLE loans ADD COLUMN product_type VARCHAR(30) NULL",
        "product_name": "ALTER TABLE loans ADD COLUMN product_name VARCHAR(120) NULL",
        "rights_title": "ALTER TABLE loans ADD COLUMN rights_title VARCHAR(120) NULL",
        "rights_desc": "ALTER TABLE loans ADD COLUMN rights_desc VARCHAR(255) NULL",
        "rights_contact_phone": "ALTER TABLE loans ADD COLUMN rights_contact_phone VARCHAR(20) NULL COMMENT '权益联系电话'",
        "rights_price": "ALTER TABLE loans ADD COLUMN rights_price FLOAT DEFAULT 0",
        "ecard_face_value": "ALTER TABLE loans ADD COLUMN ecard_face_value FLOAT DEFAULT 0",
        "product_total_price": "ALTER TABLE loans ADD COLUMN product_total_price FLOAT DEFAULT 0",
        "product_term_days": "ALTER TABLE loans ADD COLUMN product_term_days INT NULL",
        "ecard_account": "ALTER TABLE loans ADD COLUMN ecard_account VARCHAR(100) NULL",
        "ecard_password": "ALTER TABLE loans ADD COLUMN ecard_password VARCHAR(100) NULL",
        "ecard_expires_at": "ALTER TABLE loans ADD COLUMN ecard_expires_at DATETIME NULL",
        "order_no": "ALTER TABLE loans ADD COLUMN order_no VARCHAR(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '订单号'",
        "risk_report_checked_at": "ALTER TABLE loans ADD COLUMN risk_report_checked_at DATETIME NULL",
        "risk_report_checked_by": "ALTER TABLE loans ADD COLUMN risk_report_checked_by VARCHAR(50) NULL",
        "approval_discount_amount": "ALTER TABLE loans ADD COLUMN approval_discount_amount FLOAT DEFAULT 0",
        "order_discount_amount": "ALTER TABLE loans ADD COLUMN order_discount_amount FLOAT DEFAULT 0",
        "card_reissue_closed": "ALTER TABLE loans ADD COLUMN card_reissue_closed TINYINT(1) NOT NULL DEFAULT 0",
        "extension_count": "ALTER TABLE loans ADD COLUMN extension_count INT DEFAULT 0",
        "extension_type": "ALTER TABLE loans ADD COLUMN extension_type VARCHAR(30) NULL",
        "extension_note": "ALTER TABLE loans ADD COLUMN extension_note VARCHAR(255) NULL",
        "overdue_hidden": "ALTER TABLE loans ADD COLUMN overdue_hidden TINYINT(1) NOT NULL DEFAULT 0",
        "extension_source_loan_id": "ALTER TABLE loans ADD COLUMN extension_source_loan_id INT NULL",
        "extension_used_at": "ALTER TABLE loans ADD COLUMN extension_used_at DATETIME NULL",
        "is_extension_fee_order": "ALTER TABLE loans ADD COLUMN is_extension_fee_order TINYINT(1) NOT NULL DEFAULT 0",
        "identity_ocr_submitted_at": "ALTER TABLE loans ADD COLUMN identity_ocr_submitted_at DATETIME NULL",
        "identity_face_auth_at": "ALTER TABLE loans ADD COLUMN identity_face_auth_at DATETIME NULL",
    },
    "channels": {
        "sales_name": "ALTER TABLE channels ADD COLUMN sales_name VARCHAR(50) NOT NULL DEFAULT '未命名业务员'",
        "status": "ALTER TABLE channels ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'",
        "note": "ALTER TABLE channels ADD COLUMN note VARCHAR(255) NULL",
        "admin_user_id": "ALTER TABLE channels ADD COLUMN admin_user_id INT DEFAULT 0",
        "invite_code": "ALTER TABLE channels ADD COLUMN invite_code VARCHAR(32) NOT NULL DEFAULT '' COMMENT '渠道邀请码'",
        "disbursement_mode": "ALTER TABLE channels ADD COLUMN disbursement_mode VARCHAR(24) NOT NULL DEFAULT 'MANUAL_DISBURSE' COMMENT '渠道放款模式'",
    },
    "loan_mandates": {
        "loan_id": "ALTER TABLE loan_mandates ADD COLUMN loan_id INT NULL COMMENT '关联贷款订单ID'",
    },
    "momo_transactions": {
        "provider": "ALTER TABLE momo_transactions ADD COLUMN provider VARCHAR(40) NOT NULL DEFAULT 'mock' COMMENT '支付服务商'",
    },
    "user_events": {
        "operator_name": "ALTER TABLE user_events ADD COLUMN operator_name VARCHAR(50) NULL",
        "ip": "ALTER TABLE user_events ADD COLUMN ip VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'ip地址'",
        "ip_country": "ALTER TABLE user_events ADD COLUMN ip_country VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'ip所在国家'",
        "ip_province": "ALTER TABLE user_events ADD COLUMN ip_province VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'ip所在省份'",
        "ip_city": "ALTER TABLE user_events ADD COLUMN ip_city VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'ip所在城市'",
        "ip_district": "ALTER TABLE user_events ADD COLUMN ip_district VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'ip所在区县'",
        "ip_detail": "ALTER TABLE user_events ADD COLUMN ip_detail TEXT NULL COMMENT 'ip详情地址'",
        "lon_lat": "ALTER TABLE user_events ADD COLUMN lon_lat VARCHAR(32) NOT NULL DEFAULT '' COMMENT '经纬度。格式: lat,lon'",
        "lon_lat_country": "ALTER TABLE user_events ADD COLUMN lon_lat_country VARCHAR(32) NOT NULL DEFAULT '' COMMENT '经纬度所在国家'",
        "lon_lat_province": "ALTER TABLE user_events ADD COLUMN lon_lat_province VARCHAR(32) NOT NULL DEFAULT '' COMMENT '经纬度所在省份'",
        "lon_lat_city": "ALTER TABLE user_events ADD COLUMN lon_lat_city VARCHAR(32) NOT NULL DEFAULT '' COMMENT '经纬度所在城市'",
        "lon_lat_district": "ALTER TABLE user_events ADD COLUMN lon_lat_district VARCHAR(32) NOT NULL DEFAULT '' COMMENT '经纬度所在区县'",
        "lon_lat_detail": "ALTER TABLE user_events ADD COLUMN lon_lat_detail TEXT NULL COMMENT '经纬度详细地址'",
    },
    "risk_control_report": {
        "user_id": "ALTER TABLE risk_control_report ADD COLUMN user_id INT NULL",
        "source": "ALTER TABLE risk_control_report ADD COLUMN source VARCHAR(20) NULL",
    },
    "products": {
        "product_type": "ALTER TABLE products ADD COLUMN product_type VARCHAR(30) NOT NULL DEFAULT 'ECARD_RIGHTS'",
        "rights_detail_json": "ALTER TABLE products ADD COLUMN rights_detail_json TEXT NULL",
        "nominal_loan_amount": "ALTER TABLE products ADD COLUMN nominal_loan_amount FLOAT NOT NULL DEFAULT 0",
        "upfront_fee_rate": "ALTER TABLE products ADD COLUMN upfront_fee_rate FLOAT NOT NULL DEFAULT 0.4",
        "fee_components_json": "ALTER TABLE products ADD COLUMN fee_components_json TEXT NULL",
        "interest_start_day": "ALTER TABLE products ADD COLUMN interest_start_day INT NOT NULL DEFAULT 1",
        "repayment_due_day": "ALTER TABLE products ADD COLUMN repayment_due_day INT NOT NULL DEFAULT 7",
        "installment_count": "ALTER TABLE products ADD COLUMN installment_count INT NOT NULL DEFAULT 1",
        "installment_ratios_json": "ALTER TABLE products ADD COLUMN installment_ratios_json TEXT NULL",
        "daily_overdue_fee": "ALTER TABLE products ADD COLUMN daily_overdue_fee FLOAT NOT NULL DEFAULT 10",
    },
    "user_phone_bindings": {
        "bind_type": "ALTER TABLE user_phone_bindings ADD COLUMN bind_type VARCHAR(30) NOT NULL DEFAULT 'ACTIVE'",
        "note": "ALTER TABLE user_phone_bindings ADD COLUMN note VARCHAR(255) NULL",
        "unbound_at": "ALTER TABLE user_phone_bindings ADD COLUMN unbound_at DATETIME NULL",
    },
    "admins": {
        "roles": "ALTER TABLE admins ADD COLUMN roles TEXT NULL",
        "permissions": "ALTER TABLE admins ADD COLUMN permissions TEXT NULL",
        "updated_at": "ALTER TABLE admins ADD COLUMN updated_at DATETIME NULL",
        "active_session_id": "ALTER TABLE admins ADD COLUMN active_session_id VARCHAR(64) NULL",
        "active_session_issued_at": "ALTER TABLE admins ADD COLUMN active_session_issued_at DATETIME NULL",
        "active_web_session_id": "ALTER TABLE admins ADD COLUMN active_web_session_id VARCHAR(64) NULL",
        "active_web_session_issued_at": "ALTER TABLE admins ADD COLUMN active_web_session_issued_at DATETIME NULL",
        "active_mobile_session_id": "ALTER TABLE admins ADD COLUMN active_mobile_session_id VARCHAR(64) NULL",
        "active_mobile_session_issued_at": "ALTER TABLE admins ADD COLUMN active_mobile_session_issued_at DATETIME NULL",
    },
    "overdue_fee_configs": {
        "daily_penalty_amount": "ALTER TABLE overdue_fee_configs ADD COLUMN daily_penalty_amount FLOAT NOT NULL DEFAULT 10",
        "effective_date": "ALTER TABLE overdue_fee_configs ADD COLUMN effective_date DATE NOT NULL",
        "note": "ALTER TABLE overdue_fee_configs ADD COLUMN note VARCHAR(255) NULL",
        "created_by": "ALTER TABLE overdue_fee_configs ADD COLUMN created_by VARCHAR(50) NULL",
        "created_at": "ALTER TABLE overdue_fee_configs ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    },
    "risk_composite_reports": {
        "user_id": "ALTER TABLE risk_composite_reports ADD COLUMN user_id INT NULL",
        "panorama_report_id": "ALTER TABLE risk_composite_reports ADD COLUMN panorama_report_id INT NULL",
        "probe_a_report_id": "ALTER TABLE risk_composite_reports ADD COLUMN probe_a_report_id INT NULL",
        "name": "ALTER TABLE risk_composite_reports ADD COLUMN name VARCHAR(255) NULL",
        "id_card": "ALTER TABLE risk_composite_reports ADD COLUMN id_card VARCHAR(255) NULL",
        "phone": "ALTER TABLE risk_composite_reports ADD COLUMN phone VARCHAR(255) NULL",
        "report_json": "ALTER TABLE risk_composite_reports ADD COLUMN report_json TEXT NULL",
        "query_time": "ALTER TABLE risk_composite_reports ADD COLUMN query_time DATETIME NULL",
        "created_at": "ALTER TABLE risk_composite_reports ADD COLUMN created_at DATETIME NULL",
        "updated_at": "ALTER TABLE risk_composite_reports ADD COLUMN updated_at DATETIME NULL",
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

        if "user_events" in existing_tables:
            user_event_columns = {column["name"]: column for column in inspector.get_columns("user_events")}
            for column_name, comment in {
                "ip_detail": "ip详情地址",
                "lon_lat_detail": "经纬度详细地址",
            }.items():
                column = user_event_columns.get(column_name)
                if column and "TEXT" not in str(column.get("type", "")).upper():
                    connection.execute(
                        text(f"ALTER TABLE user_events MODIFY {column_name} TEXT NULL COMMENT '{comment}'")
                    )

        if "channels" in existing_tables:
            # 兼容历史数据：先为旧渠道补齐唯一邀请码，再补唯一索引，避免默认值冲突导致建索引失败
            connection.execute(
                text(
                    """
                    UPDATE channels
                    SET invite_code = CONCAT('ch', LPAD(CAST(id AS CHAR), 14, '0'))
                    WHERE invite_code IS NULL OR invite_code = ''
                    """
                )
            )
            channel_indexes = {idx["name"] for idx in inspector.get_indexes("channels")}
            if "ux_channels_invite_code" not in channel_indexes:
                connection.execute(text("ALTER TABLE channels ADD UNIQUE INDEX ux_channels_invite_code (invite_code)"))

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
            user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
            if "ix_users_risk_list_hit" not in user_indexes:
                connection.execute(text("ALTER TABLE users ADD INDEX ix_users_risk_list_hit (risk_list_hit)"))

        if "products" in existing_tables:
            product_indexes = {idx["name"] for idx in inspector.get_indexes("products")}
            if "ix_products_product_type" not in product_indexes:
                connection.execute(text("ALTER TABLE products ADD INDEX ix_products_product_type (product_type)"))

        if "blacklist_entries" in existing_tables:
            blacklist_indexes = {idx["name"] for idx in inspector.get_indexes("blacklist_entries")}
            for index_name, ddl in {
                "ix_blacklist_entries_phone": "ALTER TABLE blacklist_entries ADD INDEX ix_blacklist_entries_phone (phone)",
                "ix_blacklist_entries_id_card_num": "ALTER TABLE blacklist_entries ADD INDEX ix_blacklist_entries_id_card_num (id_card_num)",
                "ix_blacklist_entries_phone_md5": "ALTER TABLE blacklist_entries ADD INDEX ix_blacklist_entries_phone_md5 (phone_md5)",
                "ix_blacklist_entries_id_card_md5": "ALTER TABLE blacklist_entries ADD INDEX ix_blacklist_entries_id_card_md5 (id_card_md5)",
                "ix_blacklist_entries_removed_at": "ALTER TABLE blacklist_entries ADD INDEX ix_blacklist_entries_removed_at (removed_at)",
            }.items():
                if index_name not in blacklist_indexes:
                    connection.execute(text(ddl))

        if "user_phone_bindings" in existing_tables:
            phone_binding_indexes = {idx["name"] for idx in inspector.get_indexes("user_phone_bindings")}
            for index_name, ddl in {
                "ix_user_phone_bindings_phone": "ALTER TABLE user_phone_bindings ADD INDEX ix_user_phone_bindings_phone (phone)",
                "ix_user_phone_bindings_user_id": "ALTER TABLE user_phone_bindings ADD INDEX ix_user_phone_bindings_user_id (user_id)",
                "ix_user_phone_bindings_unbound_at": "ALTER TABLE user_phone_bindings ADD INDEX ix_user_phone_bindings_unbound_at (unbound_at)",
            }.items():
                if index_name not in phone_binding_indexes:
                    connection.execute(text(ddl))


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
                "product_type": "ECARD_RIGHTS",
                "ecard_face_value": 1000.0,
                "rights_price": 600.0,
                "rights_title": "韶关丹霞山2日旅游",
                "rights_desc": "酒店住宿3晚 + 丹霞山公园门票4张 + 酒店晚餐4顿",
                "term_days": 7,
                "payment_amount": 1600.0,
            },
            {
                "name": "京东E卡1500元 + 韶关丹霞山3日旅游",
                "product_type": "ECARD_RIGHTS",
                "ecard_face_value": 1500.0,
                "rights_price": 900.0,
                "rights_title": "韶关丹霞山3日旅游",
                "rights_desc": "酒店住宿4晚 + 丹霞山公园门票2张 + 酒店晚餐3顿",
                "term_days": 14,
                "payment_amount": 2400.0,
            },
            {
                "name": "京东E卡2000元 + 韶关丹霞山4日旅游",
                "product_type": "ECARD_RIGHTS",
                "ecard_face_value": 2000.0,
                "rights_price": 1200.0,
                "rights_title": "韶关丹霞山4日旅游",
                "rights_desc": "酒店住宿4晚 + 丹霞山公园门票6张 + 酒店晚餐4顿",
                "term_days": 21,
                "payment_amount": 3200.0,
            },
            {
                "name": "韶关丹霞山权益包",
                "product_type": "RIGHTS_ONLY",
                "ecard_face_value": 0.0,
                "rights_price": 600.0,
                "rights_title": "韶关丹霞山旅游权益",
                "rights_desc": "无E卡，仅包含旅游权益包，适用于展期等权益类订单。",
                "term_days": 7,
                "payment_amount": 600.0,
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


async def run_async_database_bootstrap():
    try:
        await ensure_default_admins()
        await ensure_default_products()
        await migrate_loan_to_new_semantics()
        await migrate_user_events_to_new_semantics()
    finally:
        await async_engine.dispose()


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
        ("首借", "首购"),
        ("初借", "首购"),
        ("复借", "复购"),
        ("在贷", "履约中"),
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
    asyncio.run(run_async_database_bootstrap())


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


async def get_async_db():
    async for db in get_db():
        yield db
