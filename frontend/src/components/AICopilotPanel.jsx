import { useRef, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  startAnalysis,
  setProgress,
  analysisSucceeded,
  analysisFailed,
  addChatMessage,
  setChatting,
} from "../store/aiCopilotSlice";
import { fillFromAI } from "../store/complaintFormSlice";
import { analyzeFile, analyzeText, chatAboutComplaint } from "../api/api";

export default function AICopilotPanel() {
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);
  const [pasteText, setPasteText] = useState("");
  const [chatInput, setChatInput] = useState("");

  const {
    isAnalyzing,
    extractionProgress,
    extractionStatusText,
    insights,
    chatLog,
    isChatting,
    error,
  } = useSelector((s) => s.aiCopilot);
  const savedComplaintId = useSelector((s) => s.complaintForm.savedComplaintId);
  const rawSourceText = useSelector((s) => s.aiCopilot.rawSourceText);

  const runAnalysis = async (apiCall) => {
    dispatch(startAnalysis());
    // Simulated staged progress so the bar feels alive while the pipeline runs;
    // the real jump to 100% only happens once the backend actually responds.
    const stages = [
      { at: 400, progress: 30, text: "Parsing document and extracting text..." },
      { at: 1200, progress: 55, text: "Running LangGraph extraction agents..." },
      { at: 2200, progress: 78, text: "Classifying risk and checking for duplicates..." },
    ];
    const timers = stages.map((s) =>
      setTimeout(() => dispatch(setProgress({ progress: s.progress, text: s.text })), s.at)
    );

    try {
      const res = await apiCall();
      dispatch(analysisSucceeded(res.data));
      dispatch(fillFromAI(res.data.fields));
    } catch (err) {
      dispatch(analysisFailed(err?.response?.data?.detail || err.message));
    } finally {
      timers.forEach(clearTimeout);
    }
  };

  const handleFileSelected = (e) => {
    const file = e.target.files?.[0];
    if (file) runAnalysis(() => analyzeFile(file));
  };

  const handlePasteSubmit = () => {
    if (pasteText.trim()) runAnalysis(() => analyzeText(pasteText));
  };

  const handleSendChat = async () => {
    const message = chatInput.trim();
    if (!message) return;
    dispatch(addChatMessage({ role: "user", text: message }));
    setChatInput("");
    dispatch(setChatting(true));
    try {
      const res = await chatAboutComplaint({
        complaintId: savedComplaintId,
        message,
        draftContext: savedComplaintId ? null : rawSourceText,
      });
      dispatch(addChatMessage({ role: "assistant", text: res.data.reply }));
    } catch (err) {
      dispatch(
        addChatMessage({
          role: "assistant",
          text: "Sorry, I couldn't process that: " + (err?.response?.data?.detail || err.message),
        })
      );
    } finally {
      dispatch(setChatting(false));
    }
  };

  const riskClass = insights?.initial_severity
    ? `risk-${insights.initial_severity.toLowerCase()}`
    : insights?.risk_category?.toLowerCase().includes("safety")
    ? "risk-critical"
    : "";

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">✨ AI Complaint Intake Assistant</h2>
        </div>
        <span className="badge badge-beta">BETA</span>
      </div>

      <div
        className="dropzone"
        onClick={() => fileInputRef.current?.click()}
      >
        ⬆ Drag &amp; drop complaint document here
        <br />
        or click to browse
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.eml"
          style={{ display: "none" }}
          onChange={handleFileSelected}
        />
      </div>

      <div className="or-divider">OR</div>

      <div className="paste-input">
        <textarea
          placeholder="Paste Complaint Text / Email"
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
        />
        <div style={{ marginTop: 8, textAlign: "right" }}>
          <button className="btn-primary" onClick={handlePasteSubmit} disabled={isAnalyzing}>
            Analyze Text
          </button>
        </div>
      </div>

      <div className="hint-box">
        ⓘ Supported formats: PDF, DOCX, TXT, EML — Max file size: 10MB
      </div>

      {(isAnalyzing || extractionProgress > 0) && (
        <>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${extractionProgress}%` }} />
          </div>
          <div className="progress-label">
            <span>{extractionStatusText}</span>
            <span>{extractionProgress}%</span>
          </div>
        </>
      )}

      {error && (
        <div className="assistant-msg" style={{ background: "#fef2f2", color: "#b91c1c" }}>
          ⚠ {error}
        </div>
      )}

      {!insights && !isAnalyzing && !error && (
        <div className="assistant-msg">
          🤖 Upload a complaint document or paste text above. I will automatically
          extract the details and populate the form for you.
        </div>
      )}

      {insights && (
        <>
          <div className={`insight-card ${riskClass}`}>
            <div className="insight-title">AI Risk Classification</div>
            {insights.risk_category || "—"}
          </div>

          {insights.duplicate_of_id && (
            <div className="insight-card" style={{ borderLeft: "4px solid #d97706" }}>
              <div className="insight-title">⚠ Possible Duplicate Complaint</div>
              This looks similar to Complaint #{insights.duplicate_of_id} (similarity{" "}
              {(insights.duplicate_score * 100).toFixed(0)}%). Please verify before proceeding.
            </div>
          )}

          {insights.completeness_flags?.length > 0 && (
            <div className="insight-card" style={{ borderLeft: "4px solid #dc2626" }}>
              <div className="insight-title">Completeness Check</div>
              Missing or unclear: {insights.completeness_flags.join(", ")}
            </div>
          )}

          <div className="insight-card">
            <div className="insight-title">Complaint Summary</div>
            {insights.ai_summary || "—"}
          </div>

          <div className="insight-card">
            <div className="insight-title">Root Cause Suggestion</div>
            {insights.root_cause_suggestion || "—"}
          </div>

          <div className="insight-card">
            <div className="insight-title">CAPA Recommendation</div>
            {insights.capa_recommendation || "—"}
          </div>
        </>
      )}

      <div className="section-label" style={{ marginTop: 20 }}>
        AI Assistant
      </div>
      <div className="chat-log">
        {chatLog.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {isChatting && <div className="chat-bubble assistant">Thinking...</div>}
      </div>
      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Ask me anything about this complaint..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
        />
        <button onClick={handleSendChat}>➤</button>
      </div>
      <div className="disclaimer">AI responses may contain errors. Please verify information.</div>
    </div>
  );
}
