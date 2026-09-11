import datetime as dt

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON

from app.database import Base


class Complaint(Base):
    """
    Mirrors the four sections of the 'Log Customer Complaint' form:
    1. Origin & Customer Details
    2. Product & Batch Identification
    3. Complaint Details
    4. Initial Assessment & Priority

    Plus AI-derived fields (risk_category, root_cause, capa_recommendation,
    summary, duplicate_of_id) that power the "AI Copilot" panel / bonus features.
    """

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    # 1. Origin & Customer Details
    complaint_source = Column(String(255))
    customer_name = Column(String(255))

    # 2. Product & Batch Identification
    product_name = Column(String(255))
    product_strength_grade = Column(String(255))
    batch_lot_number = Column(String(255))
    manufacturing_date = Column(String(50))  # kept as string: free-text/partial dates ok
    expiry_date = Column(String(50))
    quantity_affected = Column(Float, nullable=True)
    quantity_unit = Column(String(20), default="kg")

    # 3. Complaint Details
    complaint_type = Column(String(255))
    complaint_date = Column(String(50))
    detailed_complaint_description = Column(Text)

    # 4. Initial Assessment & Priority
    initial_severity = Column(String(50))  # Critical / Major / Minor
    priority = Column(String(50))  # High / Medium / Low

    # AI bonus-feature outputs
    risk_category = Column(String(50), nullable=True)
    ai_summary = Column(Text, nullable=True)
    root_cause_suggestion = Column(Text, nullable=True)
    capa_recommendation = Column(Text, nullable=True)
    completeness_flags = Column(JSON, nullable=True)  # list of missing/low-confidence fields
    duplicate_of_id = Column(Integer, nullable=True)
    duplicate_score = Column(Float, nullable=True)

    status = Column(String(50), default="Pending Triage")
    raw_source_text = Column(Text, nullable=True)  # original uploaded/pasted text, for chat context

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
