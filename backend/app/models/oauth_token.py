from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    access_token = Column(String(2048), nullable=False)
    refresh_token = Column(String(2048), nullable=False)
    access_jti = Column(String(64), nullable=False, unique=True, index=True)
    refresh_jti = Column(String(64), nullable=False, unique=True, index=True)
    access_expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
