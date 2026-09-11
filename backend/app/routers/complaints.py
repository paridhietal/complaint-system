from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.document_parser import extract_text_from_upload
from app.duplicate_detection import find_likely_duplicate
from app.langgraph_workflow import run_complaint_pipeline
from app.models import Complaint
from app.schemas import (
    AnalyzeResponse, ComplaintFields, AIInsights, ComplaintCreate, ComplaintOut,
)

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_complaint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Runs the LangGraph pipeline over either an uploaded document or pasted text.
    Does NOT save anything to the database -- this only powers the AI panel's
    auto-fill preview. Nothing is persisted until the user clicks "Save Complaint".
    """
    if file is not None:
        content = await file.read()
        raw_text = extract_text_from_upload(file.filename, content)
    elif text:
        raw_text = text
    else:
        raise HTTPException(400, "Provide either a file upload or pasted text.")

    if not raw_text.strip():
        raise HTTPException(400, "Could not extract any text from the provided input.")

    result = run_complaint_pipeline(raw_text)
    fields_dict = result.get("fields", {}) or {}

    dup_id, dup_score = find_likely_duplicate(
        db, fields_dict.get("detailed_complaint_description") or raw_text
    )

    return AnalyzeResponse(
        fields=ComplaintFields(**fields_dict),
        insights=AIInsights(
            risk_category=result.get("risk_category"),
            ai_summary=result.get("ai_summary"),
            root_cause_suggestion=result.get("root_cause_suggestion"),
            capa_recommendation=result.get("capa_recommendation"),
            completeness_flags=result.get("completeness_flags", []),
            duplicate_of_id=dup_id,
            duplicate_score=dup_score,
        ),
        raw_source_text=raw_text,
    )


@router.post("", response_model=ComplaintOut)
def save_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    complaint = Complaint(**payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("", response_model=List[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    return complaint
