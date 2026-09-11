import { useSelector, useDispatch } from "react-redux";
import { setField, resetForm, setSavedComplaintId } from "../store/complaintFormSlice";
import { resetCopilot } from "../store/aiCopilotSlice";
import { saveComplaint } from "../api/api";

const complaintTypes = [
  "Product Quality Defect",
  "Adverse Event",
  "Packaging Issue",
  "Documentation Error",
  "Delivery/Shipping Issue",
  "Other",
];
const severities = ["Critical", "Major", "Minor"];
const priorities = ["High", "Medium", "Low"];

function Field({ label, name, type = "text", options, textarea }) {
  const dispatch = useDispatch();
  const value = useSelector((s) => s.complaintForm.fields[name]);

  const handleChange = (e) => dispatch(setField({ name, value: e.target.value }));

  return (
    <div className="field">
      <label>{label}</label>
      {options ? (
        <select value={value || ""} onChange={handleChange}>
          <option value="">Awaiting AI extraction...</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : textarea ? (
        <textarea
          value={value || ""}
          onChange={handleChange}
          placeholder="Awaiting AI extraction..."
        />
      ) : (
        <input
          type={type}
          value={value || ""}
          onChange={handleChange}
          placeholder="Awaiting AI extraction..."
        />
      )}
    </div>
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const fields = useSelector((s) => s.complaintForm.fields);
  const status = useSelector((s) => s.complaintForm.status);
  const insights = useSelector((s) => s.aiCopilot.insights);
  const rawSourceText = useSelector((s) => s.aiCopilot.rawSourceText);

  const handleSave = async () => {
    const payload = {
      ...fields,
      quantity_affected: fields.quantity_affected ? Number(fields.quantity_affected) : null,
      risk_category: insights?.risk_category ?? null,
      ai_summary: insights?.ai_summary ?? null,
      root_cause_suggestion: insights?.root_cause_suggestion ?? null,
      capa_recommendation: insights?.capa_recommendation ?? null,
      completeness_flags: insights?.completeness_flags ?? null,
      duplicate_of_id: insights?.duplicate_of_id ?? null,
      duplicate_score: insights?.duplicate_score ?? null,
      raw_source_text: rawSourceText || null,
    };
    try {
      const res = await saveComplaint(payload);
      dispatch(setSavedComplaintId(res.data.id));
      alert(`Complaint #${res.data.id} saved successfully.`);
    } catch (err) {
      alert("Failed to save complaint: " + (err?.response?.data?.detail || err.message));
    }
  };

  const handleReset = () => {
    dispatch(resetForm());
    dispatch(resetCopilot());
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Log Customer Complaint</h2>
          <p className="panel-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className="badge badge-pending">{status}</span>
      </div>

      <div className="section-label">1. Origin &amp; Customer Details</div>
      <div className="field-row">
        <Field label="Complaint Source" name="complaint_source" />
        <Field label="Customer Name" name="customer_name" />
      </div>

      <div className="section-label">2. Product &amp; Batch Identification</div>
      <div className="field-row">
        <Field label="Product Name" name="product_name" />
        <Field label="Product Strength/Grade" name="product_strength_grade" />
      </div>
      <div className="field-row">
        <Field label="Batch/Lot Number" name="batch_lot_number" />
        <Field label="Manufacturing Date" name="manufacturing_date" type="date" />
      </div>
      <div className="field-row">
        <Field label="Expiry Date" name="expiry_date" type="date" />
        <Field label="Quantity Affected (kg)" name="quantity_affected" type="number" />
      </div>

      <div className="section-label">3. Complaint Details</div>
      <div className="field-row">
        <Field label="Complaint Type" name="complaint_type" options={complaintTypes} />
        <Field label="Complaint Date" name="complaint_date" type="date" />
      </div>
      <Field
        label="Detailed Complaint Description"
        name="detailed_complaint_description"
        textarea
      />

      <div className="section-label">4. Initial Assessment &amp; Priority</div>
      <div className="field-row">
        <Field label="Initial Severity" name="initial_severity" options={severities} />
        <Field label="Priority" name="priority" options={priorities} />
      </div>

      <div className="form-actions">
        <button className="btn-secondary" onClick={handleReset}>
          ↺ Reset Form
        </button>
        <button className="btn-primary" onClick={handleSave}>
          🗂 Save Complaint
        </button>
      </div>
    </div>
  );
}
