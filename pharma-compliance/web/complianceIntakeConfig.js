export const REGULATORY_OPTIONS = [
  {
    id: "CDSCO",
    title: "CDSCO",
    description: "Central licensing, quality, deviations, vendor approval, and data integrity.",
    gradient: "regulator-cdsco",
    requirementCount: 8
  },
  {
    id: "GMP",
    title: "GMP",
    description: "Manufacturing controls, equipment readiness, CAPA discipline, and auditability.",
    gradient: "regulator-gmp",
    requirementCount: 6
  },
  {
    id: "NPPA",
    title: "NPPA",
    description: "Ceiling price compliance, MRP checks, and pricing traceability for products.",
    gradient: "regulator-nppa",
    requirementCount: 4
  },
  {
    id: "SLA",
    title: "State License Authority",
    description: "State inspection readiness, storage, documentation, and license visibility.",
    gradient: "regulator-sla",
    requirementCount: 7
  }
];

export const INTAKE_SECTIONS = [
  {
    id: "profile",
    title: "Company Profile",
    description: "Basic company identity used across all compliance checks.",
    bodies: ["CDSCO", "GMP", "NPPA", "SLA"],
    collectionKey: null,
    fields: [
      { key: "company_name", label: "Company Name", type: "text", placeholder: "MedSure Formulations Pvt Ltd" },
      { key: "manufacturer_name", label: "Manufacturer Name", type: "text", placeholder: "Registered manufacturer name" }
    ]
  },
  {
    id: "licenses",
    title: "Licenses",
    description: "Manufacturing license details used for CDSCO and state-level checks.",
    bodies: ["CDSCO", "SLA"],
    collectionKey: "licenses",
    addLabel: "Add License",
    fields: [
      { key: "license_number", label: "License Number", type: "text" },
      { key: "license_issue_date", label: "Issue Date", type: "date" },
      { key: "license_expiry_date", label: "Expiry Date", type: "date" },
      { key: "issuing_authority", label: "Issuing Authority", type: "text" }
    ]
  },
  {
    id: "products",
    title: "Products and Pricing",
    description: "Only shown when NPPA compliance is selected.",
    bodies: ["NPPA"],
    collectionKey: "products",
    addLabel: "Add Product",
    fields: [
      { key: "product_name", label: "Product Name", type: "text" },
      { key: "formulation_type", label: "Formulation Type", type: "text" },
      { key: "dosage_strength", label: "Dosage Strength", type: "text" },
      { key: "pack_size", label: "Pack Size", type: "text" },
      { key: "mrp", label: "MRP", type: "number" },
      { key: "nppa_ceiling_price", label: "NPPA Ceiling Price", type: "number" },
      { key: "price_to_retailer", label: "Price to Retailer", type: "number" },
      { key: "price_revision_date", label: "Price Revision Date", type: "date" },
      { key: "wpi_adjustment", label: "WPI Adjustment", type: "number" }
    ]
  },
  {
    id: "batches",
    title: "Batches and Distribution",
    description: "Batch manufacturing, dispatch, and sale traceability details.",
    bodies: ["CDSCO", "GMP", "NPPA", "SLA"],
    collectionKey: "batches",
    addLabel: "Add Batch",
    fields: [
      { key: "batch_id", label: "Batch ID", type: "text" },
      { key: "product_name", label: "Product Name", type: "text" },
      { key: "manufacturing_date", label: "Manufacturing Date", type: "date" },
      { key: "process_steps", label: "Process Steps", type: "tags", placeholder: "Dispensing, Granulation, Compression" },
      { key: "approval_status", label: "Approval Status", type: "text" },
      { key: "distributor", label: "Distributor", type: "text" },
      { key: "dispatch_details", label: "Dispatch Details", type: "textarea" },
      { key: "sale_date", label: "Sale Date", type: "date" },
      { key: "invoice_id", label: "Invoice ID", type: "text" },
      { key: "customer_type", label: "Customer Type", type: "text" }
    ]
  },
  {
    id: "quality",
    title: "Quality Records",
    description: "QC results and release evidence used for CDSCO and GMP quality checks.",
    bodies: ["CDSCO", "GMP"],
    collectionKey: "quality_records",
    addLabel: "Add Quality Record",
    fields: [
      { key: "batch_id", label: "Batch ID", type: "text" },
      { key: "test_parameters", label: "Test Parameters", type: "tags", placeholder: "Assay, Dissolution, Uniformity" },
      { key: "test_results", label: "Test Results", type: "tags", placeholder: "Pass, Fail, Pass" },
      { key: "approval_status", label: "Approval Status", type: "text" },
      { key: "coa_reference", label: "COA Reference", type: "text" }
    ]
  },
  {
    id: "vendors",
    title: "Raw Materials and Vendors",
    description: "Vendor qualification and material specification evidence.",
    bodies: ["CDSCO", "GMP"],
    collectionKey: "raw_materials_and_vendors",
    addLabel: "Add Vendor",
    fields: [
      { key: "supplier_name", label: "Supplier Name", type: "text" },
      { key: "approval_status", label: "Approval Status", type: "text" },
      { key: "specifications", label: "Specifications", type: "tags", placeholder: "Paracetamol IP, Moisture NMT 0.5%" }
    ]
  },
  {
    id: "equipment",
    title: "Equipment Records",
    description: "Calibration and maintenance details for GMP and CDSCO readiness.",
    bodies: ["CDSCO", "GMP"],
    collectionKey: "equipment_records",
    addLabel: "Add Equipment",
    fields: [
      { key: "equipment_id", label: "Equipment ID", type: "text" },
      { key: "last_calibration_date", label: "Last Calibration Date", type: "date" },
      { key: "next_due_date", label: "Next Due Date", type: "date" },
      { key: "maintenance_status", label: "Maintenance Status", type: "text" }
    ]
  },
  {
    id: "deviations",
    title: "Deviation and CAPA",
    description: "Deviation investigations and closure status.",
    bodies: ["CDSCO", "GMP"],
    collectionKey: "deviations_and_capa",
    addLabel: "Add Deviation / CAPA",
    fields: [
      { key: "issue", label: "Issue", type: "textarea" },
      { key: "root_cause", label: "Root Cause", type: "textarea" },
      { key: "corrective_action", label: "Corrective Action", type: "textarea" },
      { key: "closure_status", label: "Closure Status", type: "text" }
    ]
  },
  {
    id: "inspections",
    title: "Inspection Records",
    description: "State inspection details and current facility status.",
    bodies: ["SLA"],
    collectionKey: "inspection_records",
    addLabel: "Add Inspection",
    fields: [
      { key: "inspection_date", label: "Inspection Date", type: "date" },
      { key: "inspector_name", label: "Inspector Name", type: "text" },
      { key: "inspection_observation", label: "Inspection Observation", type: "textarea" },
      { key: "compliance_status", label: "Compliance Status", type: "text" }
    ]
  },
  {
    id: "storage",
    title: "Storage Records",
    description: "Storage conditions needed for SLA storage checks.",
    bodies: ["SLA"],
    collectionKey: "storage_records",
    addLabel: "Add Storage Record",
    fields: [
      { key: "product_name", label: "Product Name", type: "text" },
      { key: "batch_id", label: "Batch ID", type: "text" },
      { key: "storage_temperature", label: "Storage Temperature", type: "text" },
      { key: "storage_temperature_range", label: "Storage Temperature Range", type: "text" },
      { key: "monitoring_system", label: "Monitoring System", type: "text" },
      { key: "temperature_logs", label: "Temperature Logs", type: "tags", placeholder: "2026-03-02: 24 C, 2026-03-03: 25 C" }
    ]
  },
  {
    id: "documents",
    title: "Controlled Documents",
    description: "Document versioning and traceability evidence.",
    bodies: ["CDSCO", "GMP", "SLA"],
    collectionKey: "documents",
    addLabel: "Add Document",
    fields: [
      { key: "document_id", label: "Document ID", type: "text" },
      { key: "document_version", label: "Document Version", type: "text" },
      { key: "record_changes", label: "Record Changes", type: "tags", placeholder: "Updated workflow, Added checklist" }
    ]
  },
  {
    id: "audit",
    title: "Audit Trail Logs",
    description: "User-linked system actions and change history.",
    bodies: ["CDSCO", "GMP", "SLA"],
    collectionKey: "audit_trail_logs",
    addLabel: "Add Audit Log",
    fields: [
      { key: "user_id", label: "User ID", type: "text" },
      { key: "action", label: "Action", type: "text" },
      { key: "timestamp", label: "Timestamp", type: "datetime-local" },
      { key: "record_changes", label: "Record Changes", type: "tags", placeholder: "Approval status set to Released" }
    ]
  }
];

export function createEmptyItem(section) {
  return section.fields.reduce((accumulator, field) => {
    if (field.type === "tags") {
      accumulator[field.key] = [];
      return accumulator;
    }
    accumulator[field.key] = "";
    return accumulator;
  }, {});
}
