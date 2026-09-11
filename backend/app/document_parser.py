"""
Basic (non-production-grade, per the assignment brief) text extraction from
uploaded complaint documents. Supports PDF, DOCX, EML, and plain TXT.
"""
import email
import io

from pypdf import PdfReader
from docx import Document


def extract_text_from_upload(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        return _extract_pdf(content)
    if lower.endswith(".docx"):
        return _extract_docx(content)
    if lower.endswith(".eml"):
        return _extract_eml(content)
    # .txt and anything else: best-effort decode
    return content.decode("utf-8", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_eml(content: bytes) -> str:
    msg = email.message_from_bytes(content)
    parts = []
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    if subject:
        parts.append(f"Subject: {subject}")
    if sender:
        parts.append(f"From: {sender}")

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="ignore"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parts.append(payload.decode("utf-8", errors="ignore"))

    return "\n".join(parts)
