import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export function analyzeFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/complaints/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export function analyzeText(text) {
  const formData = new FormData();
  formData.append("text", text);
  return api.post("/complaints/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export function saveComplaint(payload) {
  return api.post("/complaints", payload);
}

export function listComplaints() {
  return api.get("/complaints");
}

export function chatAboutComplaint({ complaintId, message, draftContext }) {
  return api.post("/chat", {
    complaint_id: complaintId ?? null,
    message,
    draft_context: draftContext ?? null,
  });
}

export default api;
