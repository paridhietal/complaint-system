import { configureStore } from "@reduxjs/toolkit";
import complaintFormReducer from "./complaintFormSlice";
import aiCopilotReducer from "./aiCopilotSlice";

export const store = configureStore({
  reducer: {
    complaintForm: complaintFormReducer,
    aiCopilot: aiCopilotReducer,
  },
});
