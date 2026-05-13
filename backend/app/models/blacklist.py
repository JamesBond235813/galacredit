from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class BlacklistEntry(Base):
    __tablename__ = "blacklist_entries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=True, index=True)
    phone = Column(String(64), nullable=True, index=True)
    id_card_num = Column(String(64), nullable=True, index=True)
    phone_md5 = Column(String(32), nullable=True, index=True)
    id_card_md5 = Column(String(32), nullable=True, index=True)
    source = Column(String(30), nullable=False, default="MANUAL", index=True)
    reason = Column(String(255), nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    removed_at = Column(DateTime, nullable=True, index=True)
    removed_by = Column(String(50), nullable=True)
    remove_reason = Column(String(255), nullable=True)
    extra_json = Column(Text, nullable=True)
