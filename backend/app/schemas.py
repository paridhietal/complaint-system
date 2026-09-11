from typing import Optional, List
from pydantic import BaseModel


class ComplaintFields(BaseModel):
    """The 10 form fields the AI extraction pipeline fills in."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[float] = None
    quantity_unit: Optional[str] = "kg"

    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_complaint_description: Optional[str] = None

    initial_severity: Optional[str] = None
    priority: Optional[str] = None


class AIInsights(BaseModel):
    risk_category: Optional[str] = None
    ai_summary: Optional[str] = None
    root_cause_suggestion: Optional[str] = None
    capa_recommendation: Optional[str] = None
    completeness_flags: Optional[List[str]] = None
    duplicate_of_id: Optional[int] = None
    duplicate_score: Optional[float] = None


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None  # used when pasting text instead of uploading a file


class AnalyzeResponse(BaseModel):
    fields: ComplaintFields
    insights: AIInsights
    raw_source_text: str


class ComplaintCreate(ComplaintFields):
    risk_category: Optional[str] = None
    ai_summary: Optional[str] = None
    root_cause_suggestion: Optional[str] = None
    capa_recommendation: Optional[str] = None
    completeness_flags: Optional[List[str]] = None
    duplicate_of_id: Optional[int] = None
    duplicate_score: Optional[float] = None
    raw_source_text: Optional[str] = None


class ComplaintOut(ComplaintCreate):
    id: int
    status: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    complaint_id: Optional[int] = None
    message: str
    # allows chatting about a complaint that hasn't been saved yet
    draft_context: Optional[str] = None
