import asyncio
import pymysql
from app.core.config import settings
from sqlalchemy import select

from app.core.database import Base, AsyncSessionLocal, engine
from app.models.user import User
from app.models.loan import Loan
from app.models.admin import Admin
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_db():
    # 1. 连接MySQL并创建数据库 (避免因为数据库不存在导致SQLAlchemy报错)
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Database '{settings.MYSQL_DATABASE}' ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")

    # 2. 如果之前没有表，就创建表
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
    
    # 3. 初始化超级管理员账号
    async with AsyncSessionLocal() as session:
        admin = (await session.execute(select(Admin).where(Admin.username == "admin"))).scalar_one_or_none()
        if not admin:
            admin_user = Admin(
                username="admin",
                password_hash=pwd_context.hash("admin123")
            )
            session.add(admin_user)
            await session.commit()
            print("Admin user 'admin' (password: 'admin123') created.")

if __name__ == "__main__":
    asyncio.run(init_db())
