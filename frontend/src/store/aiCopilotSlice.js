import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  extractionProgress: 0,
  extractionStatusText: "",
  isAnalyzing: false,
  insights: null, // { risk_category, ai_summary, root_cause_suggestion, capa_recommendation, completeness_flags, duplicate_of_id, duplicate_score }
  rawSourceText: "",
  chatLog: [], // { role: 'user' | 'assistant', text }
  isChatting: false,
  error: null,
};

const aiCopilotSlice = createSlice({
  name: "aiCopilot",
  initialState,
  reducers: {
    startAnalysis(state) {
      state.isAnalyzing = true;
      state.extractionProgress = 10;
      state.extractionStatusText = "Analyzing document content and extracting key details...";
      state.error = null;
    },
    setProgress(state, action) {
      state.extractionProgress = action.payload.progress;
      if (action.payload.text) state.extractionStatusText = action.payload.text;
    },
    analysisSucceeded(state, action) {
      state.isAnalyzing = false;
      state.extractionProgress = 100;
      state.extractionStatusText = "Extraction complete.";
      state.insights = action.payload.insights;
      state.rawSourceText = action.payload.raw_source_text;
    },
    analysisFailed(state, action) {
      state.isAnalyzing = false;
      state.extractionProgress = 0;
      state.error = action.payload;
    },
    addChatMessage(state, action) {
      state.chatLog.push(action.payload);
    },
    setChatting(state, action) {
      state.isChatting = action.payload;
    },
    resetCopilot() {
      return initialState;
    },
  },
});

export const {
  startAnalysis,
  setProgress,
  analysisSucceeded,
  analysisFailed,
  addChatMessage,
  setChatting,
  resetCopilot,
} = aiCopilotSlice.actions;
export default aiCopilotSlice.reducer;
