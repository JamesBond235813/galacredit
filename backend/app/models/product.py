from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    ecard_face_value = Column(Float, default=0.0, nullable=False)
    rights_price = Column(Float, default=0.0, nullable=False)
    rights_title = Column(String(120), nullable=False, default="韶关丹霞山旅游权益")
    rights_desc = Column(Text, nullable=True)
    rights_detail_json = Column(Text, nullable=True)
    term_days = Column(Integer, nullable=False, default=7)
    payment_amount = Column(Float, default=0.0, nullable=False)
    product_type = Column(String(30), default="ECARD_RIGHTS", nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
