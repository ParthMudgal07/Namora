"""Match structured requirements against company evidence."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable


BASE_DIR = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = BASE_DIR / "data" / "processed" / "requirements.json"
COMPANY_DATA_PATH = BASE_DIR / "data" / "company" / "company_data.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "compliance_assessment.json"
REFERENCE_DATE = date(2026, 4, 18)

AssessmentFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, list):
        return any(is_meaningful(item) for item in value)
    if isinstance(value, dict):
        return any(is_meaningful(item) for item in value.values())
    return bool(value)


def collect_attribute_values(data: Any, attribute_name: str) -> list[Any]:
    matches: list[Any] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == attribute_name and is_meaningful(value):
                matches.append(value)
            matches.extend(collect_attribute_values(value, attribute_name))
    elif isinstance(data, list):
        for item in data:
            matches.extend(collect_attribute_values(item, attribute_name))
    return matches


def summarize_values(values: list[Any]) -> list[str]:
    summaries: list[str] = []
    for value in values[:3]:
        if isinstance(value, list):
            summaries.append(", ".join(str(item) for item in value[:3]))
        elif isinstance(value, dict):
            summaries.append(", ".join(f"{k}={v}" for k, v in list(value.items())[:3]))
        else:
            summaries.append(str(value))
    return summaries


def parse_date(value: str) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip().split("T")[0]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def make_result(
    status: str,
    reason: str,
    *,
    evidence: list[str] | None = None,
    missing: list[str] | None = None,
    failing: list[str] | None = None,
    coverage_ratio: float | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "evidence": evidence or [],
        "missing_attributes": missing or [],
        "failing_attributes": failing or [],
        "coverage_ratio": coverage_ratio,
    }


def build_attribute_summary(company_data: dict[str, Any], required_attributes: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    matched: list[dict[str, Any]] = []
    missing: list[str] = []
    for attribute_name in required_attributes:
        values = collect_attribute_values(company_data, attribute_name)
        if values:
            matched.append({"attribute": attribute_name, "sample_values": summarize_values(values)})
        else:
            missing.append(attribute_name)
    return matched, missing


def released_batches(company_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        batch for batch in company_data.get("batches", [])
        if str(batch.get("approval_status", "")).strip().lower() == "released"
    ]


def quality_records_map(company_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for item in company_data.get("quality_records", []):
        batch_id = item.get("batch_id")
        if is_meaningful(batch_id):
            records[str(batch_id)] = item
    return records


def valid_license_check(company_data: dict[str, Any], authority_hint: str | None = None) -> dict[str, Any]:
    licenses = company_data.get("licenses", [])
    if not licenses:
        return make_result("non_compliant", "No license records found.", missing=["license_number", "license_issue_date", "license_expiry_date"])

    valid: list[str] = []
    expired: list[str] = []
    for item in licenses:
        number = str(item.get("license_number", "")).strip()
        issue_date = parse_date(str(item.get("license_issue_date", "")))
        expiry_date = parse_date(str(item.get("license_expiry_date", "")))
        authority = str(item.get("issuing_authority", "")).strip().lower()
        authority_ok = authority_hint is None or authority_hint.lower() in authority
        if number and issue_date and expiry_date and expiry_date >= REFERENCE_DATE and authority_ok:
            valid.append(number)
        elif number and expiry_date and authority_ok:
            expired.append(number)

    if valid:
        return make_result("compliant", "At least one current valid manufacturing license is present.", evidence=valid, coverage_ratio=1.0)
    if expired:
        return make_result("non_compliant", "License records exist but the relevant license is expired.", evidence=expired, failing=["license_expiry_date"], coverage_ratio=0.33)
    return make_result("partial", "License data exists but does not fully prove current validity.", missing=["license_number", "license_issue_date", "license_expiry_date"], coverage_ratio=0.33)


def evaluate_batch_records(company_data: dict[str, Any]) -> dict[str, Any]:
    batches = company_data.get("batches", [])
    if not batches:
        return make_result("non_compliant", "No batch records found.", missing=["batch_id", "manufacturing_date", "process_steps"])

    incomplete = [
        str(batch.get("batch_id", "unknown"))
        for batch in batches
        if not (is_meaningful(batch.get("batch_id")) and is_meaningful(batch.get("manufacturing_date")) and is_meaningful(batch.get("process_steps")))
    ]

    if not incomplete:
        return make_result("compliant", "All batches contain core manufacturing record fields.", evidence=[str(batch.get("batch_id")) for batch in batches], coverage_ratio=1.0)
    if len(incomplete) < len(batches):
        return make_result("partial", "Some batches have incomplete manufacturing record data.", evidence=incomplete, missing=["batch_id", "manufacturing_date", "process_steps"], coverage_ratio=round((len(batches) - len(incomplete)) / len(batches), 2))
    return make_result("non_compliant", "All visible batch records are incomplete.", evidence=incomplete, missing=["batch_id", "manufacturing_date", "process_steps"], coverage_ratio=0.0)


def evaluate_quality_release(company_data: dict[str, Any]) -> dict[str, Any]:
    released = released_batches(company_data)
    quality_map = quality_records_map(company_data)
    if not released:
        return make_result("insufficient_data", "No released batches found to assess quality release.", missing=["batch_id", "approval_status"])

    missing_records: list[str] = []
    invalid_records: list[str] = []
    for batch in released:
        batch_id = str(batch.get("batch_id", "unknown"))
        record = quality_map.get(batch_id)
        if record is None:
            missing_records.append(batch_id)
            continue
        approved = str(record.get("approval_status", "")).strip().lower() == "approved"
        passes = all(str(item).strip().lower() == "pass" for item in record.get("test_results", []))
        complete = is_meaningful(record.get("test_parameters")) and is_meaningful(record.get("test_results"))
        if not (approved and passes and complete):
            invalid_records.append(batch_id)

    if not missing_records and not invalid_records:
        return make_result("compliant", "All released batches have approved quality evidence.", evidence=[str(batch["batch_id"]) for batch in released], coverage_ratio=1.0)

    compliant_count = len(released) - len(missing_records) - len(invalid_records)
    if compliant_count > 0:
        return make_result(
            "partial",
            "Some released batches are missing complete approved quality evidence.",
            evidence=missing_records + invalid_records,
            missing=["test_parameters", "test_results", "approval_status"],
            failing=["test_results", "approval_status"],
            coverage_ratio=round(compliant_count / len(released), 2),
        )
    return make_result(
        "non_compliant",
        "Released batches lack complete approved quality evidence.",
        evidence=missing_records + invalid_records,
        missing=["test_parameters", "test_results", "approval_status"],
        failing=["test_results", "approval_status"],
        coverage_ratio=0.0,
    )


def evaluate_vendor_qualification(company_data: dict[str, Any]) -> dict[str, Any]:
    vendors = company_data.get("raw_materials_and_vendors", [])
    if not vendors:
        return make_result("non_compliant", "No raw material or vendor qualification data found.", missing=["supplier_name", "approval_status", "specifications"])

    compliant_count = 0
    issues: list[str] = []
    for vendor in vendors:
        supplier = str(vendor.get("supplier_name", "unknown"))
        approved = str(vendor.get("approval_status", "")).strip().lower() == "approved"
        specs = is_meaningful(vendor.get("specifications"))
        if approved and specs:
            compliant_count += 1
        else:
            issues.append(supplier)

    if compliant_count == len(vendors):
        return make_result("compliant", "All vendors are approved with specifications.", evidence=[str(v.get("supplier_name")) for v in vendors], coverage_ratio=1.0)
    if compliant_count > 0:
        return make_result("partial", "Some vendors are not fully qualified or lack specifications.", evidence=issues, failing=["approval_status", "specifications"], coverage_ratio=round(compliant_count / len(vendors), 2))
    return make_result("non_compliant", "No vendor appears fully qualified against the visible records.", evidence=issues, failing=["approval_status", "specifications"], coverage_ratio=0.0)


def evaluate_equipment_calibration(company_data: dict[str, Any]) -> dict[str, Any]:
    records = company_data.get("equipment_records", [])
    if not records:
        return make_result("non_compliant", "No equipment calibration records found.", missing=["equipment_id", "last_calibration_date", "next_due_date"])

    compliant = 0
    issues: list[str] = []
    for item in records:
        equipment_id = str(item.get("equipment_id", "unknown"))
        next_due = parse_date(str(item.get("next_due_date", "")))
        last_done = parse_date(str(item.get("last_calibration_date", "")))
        maintenance_status = str(item.get("maintenance_status", "")).strip().lower()
        if next_due and last_done and next_due >= REFERENCE_DATE and "overdue" not in maintenance_status:
            compliant += 1
        else:
            issues.append(equipment_id)

    if compliant == len(records):
        return make_result("compliant", "All equipment records appear calibrated and in-date.", evidence=[str(item.get("equipment_id")) for item in records], coverage_ratio=1.0)
    if compliant > 0:
        return make_result("partial", "Some equipment records are overdue or incomplete.", evidence=issues, failing=["last_calibration_date", "next_due_date"], coverage_ratio=round(compliant / len(records), 2))
    return make_result("non_compliant", "No visible equipment record is clearly in calibration.", evidence=issues, failing=["last_calibration_date", "next_due_date"], coverage_ratio=0.0)


def evaluate_capa_closure(company_data: dict[str, Any]) -> dict[str, Any]:
    deviations = company_data.get("deviations_and_capa", [])
    if not deviations:
        return make_result("insufficient_data", "No deviation or CAPA records found.", missing=["issue", "root_cause", "corrective_action", "closure_status"])

    closed = 0
    issues: list[str] = []
    for item in deviations:
        issue = str(item.get("issue", "unknown"))
        complete = all(is_meaningful(item.get(field)) for field in ("issue", "root_cause", "corrective_action", "closure_status"))
        status = str(item.get("closure_status", "")).strip().lower()
        if complete and status in {"closed", "completed"}:
            closed += 1
        else:
            issues.append(issue)

    if closed == len(deviations):
        return make_result("compliant", "All deviations have complete CAPA records and are closed.", evidence=[str(item.get("issue")) for item in deviations], coverage_ratio=1.0)
    if closed > 0:
        return make_result("partial", "Some deviations remain open or incompletely documented.", evidence=issues, failing=["closure_status"], coverage_ratio=round(closed / len(deviations), 2))
    return make_result("non_compliant", "No deviation record is fully closed with complete CAPA evidence.", evidence=issues, failing=["closure_status"], coverage_ratio=0.0)


def evaluate_distribution_traceability(company_data: dict[str, Any]) -> dict[str, Any]:
    released = released_batches(company_data)
    if not released:
        return make_result("insufficient_data", "No released batches found to assess distribution traceability.", missing=["batch_id", "distributor", "dispatch_details"])
    incomplete = [
        str(batch.get("batch_id", "unknown"))
        for batch in released
        if not all(is_meaningful(batch.get(field)) for field in ("batch_id", "distributor", "dispatch_details"))
    ]
    if not incomplete:
        return make_result("compliant", "Released batches have distributor and dispatch traceability.", evidence=[str(batch.get("batch_id")) for batch in released], coverage_ratio=1.0)
    if len(incomplete) < len(released):
        return make_result("partial", "Some released batches have incomplete distribution records.", evidence=incomplete, missing=["distributor", "dispatch_details"], coverage_ratio=round((len(released) - len(incomplete)) / len(released), 2))
    return make_result("non_compliant", "Released batches lack usable distribution traceability.", evidence=incomplete, missing=["distributor", "dispatch_details"], coverage_ratio=0.0)


def evaluate_audit_trail(company_data: dict[str, Any], require_document_link: bool = False) -> dict[str, Any]:
    logs = company_data.get("audit_trail_logs", [])
    documents = company_data.get("documents", [])
    log_ok = all(all(is_meaningful(item.get(field)) for field in ("user_id", "action", "timestamp", "record_changes")) for item in logs) if logs else False
    doc_ok = all(all(is_meaningful(item.get(field)) for field in ("document_id", "document_version")) for item in documents) if documents else False

    if log_ok and (doc_ok or not require_document_link):
        return make_result("compliant", "Audit trail and document-control evidence is present.", evidence=["audit_trail_logs", "documents"], coverage_ratio=1.0)
    if log_ok or doc_ok:
        missing = []
        if not log_ok:
            missing.extend(["user_id", "action", "timestamp", "record_changes"])
        if require_document_link and not doc_ok:
            missing.extend(["document_id", "document_version"])
        return make_result("partial", "Only part of the expected data-integrity evidence is present.", missing=missing, coverage_ratio=0.5)
    missing = ["user_id", "action", "timestamp", "record_changes"]
    if require_document_link:
        missing.extend(["document_id", "document_version"])
    return make_result("non_compliant", "No usable audit-trail evidence was found.", missing=missing, coverage_ratio=0.0)


def evaluate_nppa_ceiling(company_data: dict[str, Any]) -> dict[str, Any]:
    products = company_data.get("products", [])
    if not products:
        return make_result("non_compliant", "No product pricing data found.", missing=["product_name", "nppa_ceiling_price", "mrp"])

    compliant = 0
    issues: list[str] = []
    for item in products:
        name = str(item.get("product_name", "unknown"))
        ceiling = item.get("nppa_ceiling_price")
        mrp = item.get("mrp")
        wpi = item.get("wpi_adjustment", 0)
        if not isinstance(ceiling, (int, float)) or not isinstance(mrp, (int, float)):
            issues.append(name)
            continue
        allowed = ceiling + float(wpi)
        if mrp <= allowed:
            compliant += 1
        else:
            issues.append(name)

    if compliant == len(products):
        return make_result("compliant", "All products are within NPPA ceiling after the configured adjustment.", evidence=[str(item.get("product_name")) for item in products], coverage_ratio=1.0)
    if compliant > 0:
        return make_result("partial", "Some products exceed the allowed NPPA ceiling price.", evidence=issues, failing=["nppa_ceiling_price", "mrp", "wpi_adjustment"], coverage_ratio=round(compliant / len(products), 2))
    return make_result("non_compliant", "All visible products breach or fail to prove NPPA ceiling compliance.", evidence=issues, failing=["nppa_ceiling_price", "mrp", "wpi_adjustment"], coverage_ratio=0.0)


def evaluate_nppa_trade(company_data: dict[str, Any]) -> dict[str, Any]:
    products = company_data.get("products", [])
    sold_batches = [batch for batch in company_data.get("batches", []) if is_meaningful(batch.get("invoice_id"))]
    if not products or not sold_batches:
        return make_result("insufficient_data", "Pricing or sold-batch trade records are incomplete.", missing=["price_to_retailer", "sale_date", "invoice_id", "customer_type"])

    product_ok = all(isinstance(item.get("price_to_retailer"), (int, float)) and item.get("price_to_retailer", 0) > 0 for item in products)
    batch_ok = all(all(is_meaningful(batch.get(field)) for field in ("sale_date", "invoice_id", "customer_type")) for batch in sold_batches)
    if product_ok and batch_ok:
        return make_result("compliant", "Trade pricing and sold-batch traceability are present.", evidence=[str(item.get("batch_id")) for item in sold_batches], coverage_ratio=1.0)
    if product_ok or batch_ok:
        return make_result("partial", "Trade records are only partially complete.", missing=["price_to_retailer", "sale_date", "invoice_id", "customer_type"], coverage_ratio=0.5)
    return make_result("non_compliant", "Trade pricing and sold-batch traceability are not proven.", missing=["price_to_retailer", "sale_date", "invoice_id", "customer_type"], coverage_ratio=0.0)


def evaluate_nppa_batch_traceability(company_data: dict[str, Any]) -> dict[str, Any]:
    sold_batches = [batch for batch in company_data.get("batches", []) if is_meaningful(batch.get("invoice_id"))]
    manufacturer = is_meaningful(company_data.get("manufacturer_name"))
    if not sold_batches:
        return make_result("insufficient_data", "No sold batch records found for NPPA traceability.", missing=["batch_id", "sale_date", "invoice_id"])
    complete = [batch for batch in sold_batches if all(is_meaningful(batch.get(field)) for field in ("batch_id", "sale_date", "invoice_id", "product_name"))]
    if len(complete) == len(sold_batches) and manufacturer:
        return make_result("compliant", "Sold product records are traceable to batch and manufacturer.", evidence=[str(batch.get("batch_id")) for batch in sold_batches], coverage_ratio=1.0)
    if complete:
        return make_result("partial", "Some sold product records are not fully traceable.", evidence=[str(batch.get("batch_id")) for batch in sold_batches if batch not in complete], missing=["manufacturer_name", "batch_id", "sale_date", "invoice_id"], coverage_ratio=round(len(complete) / len(sold_batches), 2))
    return make_result("non_compliant", "Sold product records are not fully traceable to batch and manufacturer.", missing=["manufacturer_name", "batch_id", "sale_date", "invoice_id"], coverage_ratio=0.0)


def evaluate_inspection_records(company_data: dict[str, Any]) -> dict[str, Any]:
    records = company_data.get("inspection_records", [])
    if not records:
        return make_result("non_compliant", "No inspection records found.", missing=["inspection_date", "inspector_name", "inspection_observation"])
    complete = [item for item in records if all(is_meaningful(item.get(field)) for field in ("inspection_date", "inspector_name", "inspection_observation"))]
    if len(complete) == len(records):
        return make_result("compliant", "Inspection records contain date, inspector, and observations.", evidence=[str(item.get("inspection_date")) for item in records], coverage_ratio=1.0)
    if complete:
        return make_result("partial", "Some inspection records are incomplete.", missing=["inspection_date", "inspector_name", "inspection_observation"], coverage_ratio=round(len(complete) / len(records), 2))
    return make_result("non_compliant", "Inspection records are too incomplete to support compliance.", missing=["inspection_date", "inspector_name", "inspection_observation"], coverage_ratio=0.0)


def evaluate_inspection_status(company_data: dict[str, Any]) -> dict[str, Any]:
    records = company_data.get("inspection_records", [])
    if not records:
        return make_result("insufficient_data", "No inspection status records found.", missing=["compliance_status"])
    statuses = [str(item.get("compliance_status", "")).strip().lower() for item in records if is_meaningful(item.get("compliance_status"))]
    if not statuses:
        return make_result("insufficient_data", "Inspection records do not include compliance status.", missing=["compliance_status"])
    if all(status in {"compliant", "satisfactory", "acceptable"} for status in statuses):
        return make_result("compliant", "Inspection status is acceptable across visible records.", evidence=statuses, coverage_ratio=1.0)
    if any(status in {"minor observations", "conditional", "partially compliant"} for status in statuses):
        return make_result("partial", "Inspection records show minor observations or conditional status.", evidence=statuses, failing=["compliance_status"], coverage_ratio=0.5)
    return make_result("non_compliant", "Inspection records show non-compliant or adverse status.", evidence=statuses, failing=["compliance_status"], coverage_ratio=0.0)


def evaluate_storage_controls(company_data: dict[str, Any]) -> dict[str, Any]:
    records = company_data.get("storage_records", [])
    if not records:
        return make_result("non_compliant", "No storage records found.", missing=["storage_temperature", "storage_temperature_range", "monitoring_system"])
    complete = 0
    issues: list[str] = []
    for item in records:
        batch_id = str(item.get("batch_id", "unknown"))
        ready = all(is_meaningful(item.get(field)) for field in ("storage_temperature", "storage_temperature_range", "monitoring_system"))
        logs = is_meaningful(item.get("temperature_logs"))
        if ready and logs:
            complete += 1
        else:
            issues.append(batch_id)
    if complete == len(records):
        return make_result("compliant", "All storage records show monitored controlled storage.", evidence=[str(item.get("batch_id")) for item in records], coverage_ratio=1.0)
    if complete > 0:
        return make_result("partial", "Some storage records are missing range, monitoring, or logs.", evidence=issues, missing=["storage_temperature", "storage_temperature_range", "monitoring_system"], failing=["temperature_logs"], coverage_ratio=round(complete / len(records), 2))
    return make_result("non_compliant", "No storage record clearly proves controlled monitored storage.", evidence=issues, missing=["storage_temperature", "storage_temperature_range", "monitoring_system"], failing=["temperature_logs"], coverage_ratio=0.0)


def evaluate_document_control(company_data: dict[str, Any]) -> dict[str, Any]:
    documents = company_data.get("documents", [])
    if not documents:
        return make_result("non_compliant", "No controlled document records found.", missing=["document_id", "document_version"])
    complete = [item for item in documents if all(is_meaningful(item.get(field)) for field in ("document_id", "document_version"))]
    if len(complete) == len(documents):
        return make_result("compliant", "Controlled documents are versioned and identifiable.", evidence=[str(item.get("document_id")) for item in documents], coverage_ratio=1.0)
    if complete:
        return make_result("partial", "Some documents are missing ID or version traceability.", missing=["document_id", "document_version"], coverage_ratio=round(len(complete) / len(documents), 2))
    return make_result("non_compliant", "Document control records are incomplete.", missing=["document_id", "document_version"], coverage_ratio=0.0)


def default_attribute_evaluation(requirement: dict[str, Any], company_data: dict[str, Any]) -> dict[str, Any]:
    matched, missing = build_attribute_summary(company_data, requirement["required_company_attributes"])
    present_count = len(matched)
    total = len(requirement["required_company_attributes"])
    if total == 0:
        return make_result("insufficient_data", "Requirement has no mapped attributes.", coverage_ratio=0.0)
    if present_count == total:
        return make_result("compliant", "All mapped attributes are present.", coverage_ratio=1.0)
    if present_count > 0:
        return make_result("partial", "Only some mapped attributes are present.", missing=missing, coverage_ratio=round(present_count / total, 2))
    return make_result("non_compliant", "Mapped attributes are not present in company data.", missing=missing, coverage_ratio=0.0)


RULES: dict[str, AssessmentFn] = {
    "CDSCO-001": lambda req, data: valid_license_check(data),
    "CDSCO-002": lambda req, data: evaluate_batch_records(data),
    "CDSCO-003": lambda req, data: evaluate_quality_release(data),
    "CDSCO-004": lambda req, data: evaluate_vendor_qualification(data),
    "CDSCO-005": lambda req, data: evaluate_equipment_calibration(data),
    "CDSCO-006": lambda req, data: evaluate_capa_closure(data),
    "CDSCO-007": lambda req, data: evaluate_distribution_traceability(data),
    "CDSCO-008": lambda req, data: evaluate_audit_trail(data),
    "GMP-001": lambda req, data: evaluate_batch_records(data),
    "GMP-002": lambda req, data: evaluate_quality_release(data),
    "GMP-003": lambda req, data: evaluate_equipment_calibration(data),
    "GMP-004": lambda req, data: evaluate_vendor_qualification(data),
    "GMP-005": lambda req, data: evaluate_capa_closure(data),
    "GMP-006": lambda req, data: evaluate_audit_trail(data),
    "NPPA-001": lambda req, data: evaluate_nppa_ceiling(data),
    "NPPA-002": lambda req, data: evaluate_nppa_ceiling(data),
    "NPPA-003": lambda req, data: evaluate_nppa_trade(data),
    "NPPA-004": lambda req, data: evaluate_nppa_batch_traceability(data),
    "SLA-001": lambda req, data: valid_license_check(data, authority_hint="fda"),
    "SLA-002": lambda req, data: evaluate_inspection_records(data),
    "SLA-003": lambda req, data: evaluate_inspection_status(data),
    "SLA-004": lambda req, data: evaluate_batch_records(data),
    "SLA-005": lambda req, data: evaluate_storage_controls(data),
    "SLA-006": lambda req, data: evaluate_document_control(data),
    "SLA-007": lambda req, data: evaluate_audit_trail(data, require_document_link=True),
}


def build_assessment(requirement: dict[str, Any], company_data: dict[str, Any]) -> dict[str, Any]:
    matched_attributes, derived_missing = build_attribute_summary(company_data, requirement["required_company_attributes"])
    evaluator = RULES.get(requirement["requirement_id"], default_attribute_evaluation)
    rule_result = evaluator(requirement, company_data)
    missing_attributes = sorted(set(derived_missing + rule_result.get("missing_attributes", [])))
    failing_attributes = sorted(set(rule_result.get("failing_attributes", [])))
    coverage_ratio = rule_result.get("coverage_ratio")
    if coverage_ratio is None:
        required = len(requirement["required_company_attributes"])
        coverage_ratio = round(len(matched_attributes) / required, 2) if required else 0.0

    return {
        "requirement_id": requirement["requirement_id"],
        "regulatory_body": requirement["regulatory_body"],
        "domain": requirement["domain"],
        "requirement_text": requirement["requirement_text"],
        "severity": requirement["severity"],
        "status": rule_result["status"],
        "coverage_ratio": coverage_ratio,
        "matched_attributes": matched_attributes,
        "missing_attributes": missing_attributes,
        "failing_attributes": failing_attributes,
        "evaluation_reason": rule_result["reason"],
        "evaluation_evidence": rule_result.get("evidence", []),
        "source_document": requirement["source_document"],
        "source_page": requirement["source_page"],
        "source_excerpt": requirement["source_excerpt"],
    }


def main() -> None:
    requirements = load_json(REQUIREMENTS_PATH)
    company_data = load_json(COMPANY_DATA_PATH)
    assessments = [build_assessment(requirement, company_data) for requirement in requirements]
    payload = {
        "company_data_source": str(COMPANY_DATA_PATH),
        "reference_date": REFERENCE_DATE.isoformat(),
        "total_requirements": len(assessments),
        "status_counts": {
            "compliant": sum(item["status"] == "compliant" for item in assessments),
            "partial": sum(item["status"] == "partial" for item in assessments),
            "non_compliant": sum(item["status"] == "non_compliant" for item in assessments),
            "insufficient_data": sum(item["status"] == "insufficient_data" for item in assessments),
        },
        "assessments": assessments,
    }
    save_json(OUTPUT_PATH, payload)
    print(f"Saved compliance assessment to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
