from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


class PurchaseContractSignature(Base):
    __tablename__ = "purchase_contract_signatures"

    id = Column(Integer, primary_key=True, index=True)
    signature_no = Column(String(40), nullable=False, unique=True, index=True)
    order_no = Column(String(32), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    extension_source_loan_id = Column(Integer, nullable=True, index=True)

    contract_title = Column(String(100), nullable=False, default="小荷包商品购销合同")
    contract_content = Column(Text, nullable=False)
    contract_text = Column(Text, nullable=True)
    party_a_name = Column(String(100), nullable=False)
    party_a_legal_person = Column(String(50), nullable=False)
    party_b_name = Column(String(50), nullable=True)
    party_b_id_card = Column(String(32), nullable=True)
    party_b_phone = Column(String(20), nullable=True)
    party_b_address = Column(String(255), nullable=True)

    product_name = Column(String(120), nullable=True)
    ecard_face_value = Column(Float, default=0.0)
    rights_price = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    payment_amount = Column(Float, default=0.0)
    term_days = Column(Integer, nullable=True)
    due_date_text = Column(String(80), nullable=True)

    signed_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
