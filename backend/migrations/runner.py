"""执行 GalaCredit 生产数据库版本迁移。

该命令只在部署阶段执行，应用启动过程不会修改数据库结构。
"""

from pathlib import Path

import pymysql

from app.core.config import settings


MIGRATION_DIR = Path(__file__).resolve().parent / "versions"


def upgrade() -> None:
    """按文件名顺序执行尚未执行的数据库迁移。

    :return: None
    """
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=int(settings.MYSQL_PORT),
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(100) PRIMARY KEY COMMENT '迁移版本',
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='GalaCredit数据库迁移记录'
                """
            )
            cursor.execute("SELECT version FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}
            for migration in sorted(MIGRATION_DIR.glob("*.sql")):
                version = migration.stem
                if version in applied:
                    continue
                sql = migration.read_text(encoding="utf-8")
                for statement in (item.strip() for item in sql.split(";")):
                    if statement:
                        cursor.execute(statement)
                cursor.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (version,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    upgrade()
    print("Database migrations applied.")
