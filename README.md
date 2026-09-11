# AIVOA – AI-Powered Customer Complaint Management System

An AI-assisted complaint intake tool for pharmaceutical QMS (Quality Management System),
built for the AIVOA Round 1 AI Product Engineer assignment.

## What it does

1. A user pastes complaint text or uploads a document (PDF/DOCX/TXT/EML) on the right-hand
   "AI Complaint Intake Assistant" panel.
2. A LangGraph pipeline runs over Groq (`gemma2-9b-it` + `llama-3.3-70b-versatile`) to:
   - extract the 10 structured fields the "Log Customer Complaint" form needs
   - flag any fields it couldn't find (Completeness Checker)
   - classify severity/priority and an overall risk category (AI Risk Classification)
   - suggest a root cause and a CAPA (Corrective and Preventive Action) recommendation
   - write a one-line summary
   - check the new complaint against previously saved complaints for likely duplicates
     (sentence-transformer embeddings + cosine similarity, with a text-similarity fallback)
3. The extracted fields auto-fill the left-hand form; the user can edit anything before
   clicking "Save Complaint", which persists it to the database.
4. The "Ask me anything about this complaint..." box lets the user chat with the assistant
   about the current draft or a saved complaint (Groq + the stored complaint context).

## Why this architecture (worth knowing for the interview)

- **Two different Groq models, on purpose.** `gemma2-9b-it` handles the high-volume,
  low-complexity steps (field extraction, one-line summary) where speed matters more than
  depth. `llama-3.3-70b-versatile` handles the steps that need actual judgement
  (severity/priority classification, root cause reasoning, CAPA recommendation, chat).
- **LangGraph, not a single prompt.** Each step is a separate node with its own narrow
  prompt and its own JSON contract, so a bad output from one step (e.g. a hallucinated
  batch number) doesn't corrupt the whole pipeline, and each node is independently testable.
  Graph shape: `extract_fields → check_completeness → classify_risk → root_cause_and_capa
  → summarize`.
- **Duplicate detection degrades gracefully.** It tries a real embedding model
  (`all-MiniLM-L6-v2`) first; if that fails to load (e.g. no internet for the first
  download, or the optional dependency was skipped), it falls back to plain text
  similarity so the demo never hard-crashes.
- **The "analyze" and "save" steps are separate endpoints.** This mirrors the UI: the AI
  panel pre-fills the form, but nothing is persisted to the database until the user
  reviews it and clicks "Save Complaint" — matching how a real QMS shouldn't auto-commit
  unreviewed AI output.

## Project structure

```
backend/
  app/
    main.py                 FastAPI app, CORS, router registration, error handling
    config.py                env vars, model names
    database.py               SQLAlchemy engine/session
    models.py                 Complaint table
    schemas.py                 Pydantic request/response models
    document_parser.py        PDF/DOCX/EML/TXT -> raw text
    groq_client.py             thin wrapper around the Groq SDK (JSON-mode helper)
    langgraph_workflow.py       the LangGraph StateGraph (the core of the assignment)
    duplicate_detection.py       embeddings + cosine similarity / difflib fallback
    routers/
      complaints.py            /api/complaints/analyze, /api/complaints (CRUD)
      chat.py                    /api/chat
  sample_data/                 3 sample pharma complaints (incl. one intentional duplicate)
  requirements.txt
  .env.example
frontend/
  src/
    main.jsx / App.jsx           entry point, two-panel layout
    store/                       Redux Toolkit slices (complaintForm, aiCopilot) + store
    components/
      ComplaintForm.jsx           left panel — the 4-section form
      AICopilotPanel.jsx           right panel — upload/paste, progress, insights, chat
    api/api.js                   axios calls to the backend
    index.css                    styling, Inter font applied globally
  index.html                    loads Google Inter font
  vite.config.js                 dev proxy: /api -> http://localhost:8000
```

## Running it locally

You need **Python 3.10+**, **Node.js 18+**, and a free Groq API key from
https://console.groq.com/keys

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste your real Groq key in place of `your_groq_api_key_here`.

```bash
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`). It uses a local
SQLite file (`complaints.db`, created automatically) so there's no database server to set
up. To use real Postgres/MySQL instead, change `DATABASE_URL` in `.env`, e.g.:
```
DATABASE_URL=postgresql://user:password@localhost:5432/aivoa_complaints
```
(install `psycopg2-binary`, already in `requirements.txt`, for Postgres; use
`pymysql`/`mysqlclient` for MySQL).

### 2. Frontend

In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the printed localhost URL (usually `http://localhost:5173`). The Vite dev server
proxies `/api` calls to `http://localhost:8000`, so keep the backend running.

### 3. Try it end-to-end

1. In the AI Copilot panel, click the upload box and pick
   `backend/sample_data/complaint_1_critical.txt` (or paste its contents into the text box).
2. Watch the progress bar, then check the auto-filled form fields plus the AI Risk
   Classification / Root Cause / CAPA / Summary cards on the right.
3. Click **Save Complaint**.
4. Now analyze `backend/sample_data/complaint_3_duplicate_of_1.txt` — it should flag as a
   likely duplicate of complaint #1.
5. Try the "Ask me anything about this complaint..." box, e.g. "What batch number was
   affected?"

## Bonus features implemented
- ✅ Complaint Completeness Checker
- ✅ Root Cause Recommendation
- ✅ Duplicate Complaint Detection
- ✅ CAPA Recommendation
- ✅ Complaint Summary
- ✅ AI Risk Classification
- ✅ Conversational follow-up assistant (chat box, per the reference UI)

## Known limitations (intentionally out of scope per the assignment brief)
- Document parsing is basic text extraction, not production-grade OCR (explicitly not
  required by the brief).
- No auth/user management — out of scope for a Round 1 assignment.
- Duplicate detection uses a similarity threshold (0.80) rather than a tuned classifier.
- CORS is wide open (`allow_origins=["*"]`) for local dev/demo convenience only.
