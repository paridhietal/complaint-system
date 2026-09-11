from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.groq_client import call_llm, REASONING_MODEL
from app.models import Complaint
from app.schemas import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat_about_complaint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Backs the "Ask me anything about this complaint..." box in the AI Copilot
    panel. Works both for a saved complaint (complaint_id) and an in-progress
    draft that hasn't been saved yet (draft_context) -- the reference UI shows
    the assistant chatting during intake, before "Save Complaint" is clicked.
    """
    context = payload.draft_context or ""

    if payload.complaint_id is not None:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if not complaint:
            raise HTTPException(404, "Complaint not found")
        context = (
            f"Product: {complaint.product_name}\n"
            f"Batch/Lot: {complaint.batch_lot_number}\n"
            f"Complaint type: {complaint.complaint_type}\n"
            f"Severity: {complaint.initial_severity} | Priority: {complaint.priority}\n"
            f"Description: {complaint.detailed_complaint_description}\n"
            f"Risk category: {complaint.risk_category}\n"
            f"Root cause suggestion: {complaint.root_cause_suggestion}\n"
            f"CAPA recommendation: {complaint.capa_recommendation}\n"
            f"Raw source text: {complaint.raw_source_text}\n"
        )

    if not context:
        raise HTTPException(400, "No complaint context available to chat about yet.")

    system_prompt = (
        "You are the AI Complaint Intake Assistant inside a pharmaceutical QMS "
        "complaint management tool. Answer the user's question using ONLY the "
        "complaint context provided. Be concise and factual. If the context doesn't "
        "contain the answer, say so plainly rather than guessing."
    )
    user_prompt = f"Complaint context:\n{context}\n\nQuestion: {payload.message}"

    reply = call_llm(system_prompt, user_prompt, model=REASONING_MODEL)
    return {"reply": reply}
