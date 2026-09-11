"""
The LangGraph pipeline that powers the "AI Complaint Intake Assistant" panel.

Graph shape:

    extract_fields
          |
          v
    check_completeness
          |
          v
    classify_risk  -----> (Initial Severity, Priority, risk_category)
          |
          v
    root_cause_and_capa
          |
          v
    summarize
          |
          v
        (END)

Each node is a small, independently-testable function with its own narrow
prompt and JSON contract -- a bad output in one step (e.g. a hallucinated
batch number) doesn't corrupt the whole pipeline. Field extraction and the
summary use the fast model (gemma2-9b-it); classification and root
cause/CAPA reasoning use the larger reasoning model (llama-3.3-70b-versatile)
because they need actual judgement, not just pattern matching.

Duplicate detection is intentionally NOT a graph node -- it needs a live DB
session, which the graph nodes don't have access to. It's run once in the
router right after this pipeline finishes (see routers/complaints.py).
"""
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END

from app.groq_client import call_llm_json, call_llm, FAST_MODEL, REASONING_MODEL

REQUIRED_FIELDS = [
    "complaint_source", "customer_name", "product_name", "product_strength_grade",
    "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
    "complaint_type", "complaint_date", "detailed_complaint_description",
]


class ComplaintState(TypedDict, total=False):
    raw_text: str
    fields: dict
    completeness_flags: List[str]
    initial_severity: Optional[str]
    priority: Optional[str]
    risk_category: Optional[str]
    root_cause_suggestion: Optional[str]
    capa_recommendation: Optional[str]
    ai_summary: Optional[str]


def extract_fields_node(state: ComplaintState) -> ComplaintState:
    system_prompt = (
        "You are a data extraction assistant for a pharmaceutical Quality Management "
        "System (QMS) Customer Complaint module. Extract structured fields from the "
        "complaint text. If a field is not mentioned, use null. Respond ONLY with a "
        "JSON object with exactly these keys: complaint_source, customer_name, "
        "product_name, product_strength_grade, batch_lot_number, manufacturing_date, "
        "expiry_date, quantity_affected (a number, or null), quantity_unit (default "
        "'kg' if a quantity is present), complaint_type (e.g. 'Product Quality Defect', "
        "'Adverse Event', 'Packaging Issue', 'Documentation Error'), complaint_date, "
        "detailed_complaint_description (a clear rewritten paragraph of the complaint)."
    )
    result = call_llm_json(system_prompt, state["raw_text"], model=FAST_MODEL)
    state["fields"] = result
    return state


def check_completeness_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    missing = [
        f for f in REQUIRED_FIELDS
        if fields.get(f) in (None, "", "null")
    ]
    state["completeness_flags"] = missing
    return state


def classify_risk_node(state: ComplaintState) -> ComplaintState:
    system_prompt = (
        "You are a pharmaceutical QMS risk assessor. Given complaint details, decide: "
        "1) initial_severity: one of 'Critical', 'Major', 'Minor' "
        "(Critical = potential patient safety/adverse event or GMP failure, "
        "Major = significant quality defect but no direct safety risk, "
        "Minor = cosmetic/documentation/minor packaging issue). "
        "2) priority: one of 'High', 'Medium', 'Low' for how urgently QA should triage this. "
        "3) risk_category: a short label like 'Patient Safety Risk', 'Quality Defect', "
        "'Regulatory/Documentation', or 'Packaging/Labeling'. "
        "Respond ONLY with a JSON object: {\"initial_severity\": ..., \"priority\": ..., "
        "\"risk_category\": ...}."
    )
    user_prompt = str(state.get("fields", {}))
    result = call_llm_json(system_prompt, user_prompt, model=REASONING_MODEL)
    state["initial_severity"] = result.get("initial_severity")
    state["priority"] = result.get("priority")
    state["risk_category"] = result.get("risk_category")
    return state


def root_cause_and_capa_node(state: ComplaintState) -> ComplaintState:
    system_prompt = (
        "You are a pharmaceutical QA/QC specialist. Given a customer complaint's "
        "details and its assessed severity, suggest: "
        "1) root_cause_suggestion: a plausible, brief root-cause hypothesis "
        "(2-3 sentences) that a QA investigator would want to check first. "
        "2) capa_recommendation: a brief Corrective and Preventive Action recommendation "
        "(2-3 sentences). Be clear these are AI-generated hypotheses for a human "
        "investigator to verify, not confirmed findings. "
        "Respond ONLY with a JSON object: {\"root_cause_suggestion\": ..., "
        "\"capa_recommendation\": ...}."
    )
    context = {
        "fields": state.get("fields", {}),
        "initial_severity": state.get("initial_severity"),
        "risk_category": state.get("risk_category"),
    }
    result = call_llm_json(system_prompt, str(context), model=REASONING_MODEL)
    state["root_cause_suggestion"] = result.get("root_cause_suggestion")
    state["capa_recommendation"] = result.get("capa_recommendation")
    return state


def summarize_node(state: ComplaintState) -> ComplaintState:
    system_prompt = (
        "Summarize this pharmaceutical customer complaint in exactly one clear, "
        "concise sentence for a QA dashboard. Respond with plain text only, no JSON."
    )
    summary = call_llm(system_prompt, str(state.get("fields", {})), model=FAST_MODEL,
                        json_mode=False)
    state["ai_summary"] = summary.strip()
    return state


def build_complaint_graph():
    graph = StateGraph(ComplaintState)
    graph.add_node("extract_fields", extract_fields_node)
    graph.add_node("check_completeness", check_completeness_node)
    graph.add_node("classify_risk", classify_risk_node)
    graph.add_node("root_cause_and_capa", root_cause_and_capa_node)
    graph.add_node("summarize", summarize_node)

    graph.set_entry_point("extract_fields")
    graph.add_edge("extract_fields", "check_completeness")
    graph.add_edge("check_completeness", "classify_risk")
    graph.add_edge("classify_risk", "root_cause_and_capa")
    graph.add_edge("root_cause_and_capa", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


# Compiled once at import time and reused across requests.
complaint_graph = build_complaint_graph()


def run_complaint_pipeline(raw_text: str) -> ComplaintState:
    return complaint_graph.invoke({"raw_text": raw_text})
