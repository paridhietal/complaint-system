import { createSlice } from "@reduxjs/toolkit";

const emptyFields = {
  complaint_source: "",
  customer_name: "",
  product_name: "",
  product_strength_grade: "",
  batch_lot_number: "",
  manufacturing_date: "",
  expiry_date: "",
  quantity_affected: "",
  quantity_unit: "kg",
  complaint_type: "",
  complaint_date: "",
  detailed_complaint_description: "",
  initial_severity: "",
  priority: "",
};

const initialState = {
  fields: { ...emptyFields },
  status: "Pending Triage",
  savedComplaintId: null,
};

const complaintFormSlice = createSlice({
  name: "complaintForm",
  initialState,
  reducers: {
    setField(state, action) {
      const { name, value } = action.payload;
      state.fields[name] = value;
    },
    fillFromAI(state, action) {
      // Only overwrite fields the AI actually returned a value for, so
      // partial extractions don't blank out fields the user already typed.
      const extracted = action.payload || {};
      Object.keys(extracted).forEach((key) => {
        if (extracted[key] !== null && extracted[key] !== undefined && key in state.fields) {
          state.fields[key] = extracted[key];
        }
      });
    },
    resetForm(state) {
      state.fields = { ...emptyFields };
      state.status = "Pending Triage";
      state.savedComplaintId = null;
    },
    setSavedComplaintId(state, action) {
      state.savedComplaintId = action.payload;
    },
  },
});

export const { setField, fillFromAI, resetForm, setSavedComplaintId } =
  complaintFormSlice.actions;
export default complaintFormSlice.reducer;
