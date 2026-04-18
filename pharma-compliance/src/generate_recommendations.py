"""Generate prioritized compliance recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
ASSESSMENT_PATH = BASE_DIR / "data" / "processed" / "compliance_assessment.json"
RISK_REPORT_PATH = BASE_DIR / "data" / "processed" / "risk_report.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "recommendations.json"


RECOMMENDATION_LIBRARY: dict[str, dict[str, str]] = {
    "CDSCO-003": {
        "action": "Investigate failed quality results, hold the released batch, and complete approved QA release evidence.",
        "owner": "Quality Control",
        "timeline": "24 hours",
    },
    "CDSCO-004": {
        "action": "Complete vendor qualification for all raw material and packaging suppliers before further procurement.",
        "owner": "Procurement QA",
        "timeline": "7 days",
    },
    "CDSCO-005": {
        "action": "Review overdue calibration items immediately and recalibrate or quarantine affected equipment.",
        "owner": "Engineering and QA",
        "timeline": "48 hours",
    },
    "CDSCO-006": {
        "action": "Close open deviations with documented CAPA effectiveness checks and QA approval.",
        "owner": "Quality Assurance",
        "timeline": "48 hours",
    },
    "GMP-002": {
        "action": "Block release for affected batches until QC evidence is approved and all failed tests are dispositioned.",
        "owner": "Quality Control",
        "timeline": "24 hours",
    },
    "GMP-003": {
        "action": "Bring all production and QC equipment back into calibration and document impact assessments.",
        "owner": "Engineering and QC",
        "timeline": "72 hours",
    },
    "GMP-004": {
        "action": "Approve or suspend suppliers that do not yet have complete qualification and specification evidence.",
        "owner": "Procurement QA",
        "timeline": "7 days",
    },
    "GMP-005": {
        "action": "Track all deviation CAPAs to closure and block affected processes until closure criteria are met.",
        "owner": "Quality Assurance",
        "timeline": "48 hours",
    },
    "NPPA-001": {
        "action": "Revise product MRPs to stay within NPPA ceiling price plus permitted adjustment and document the revision.",
        "owner": "Commercial Compliance",
        "timeline": "24 hours",
    },
    "NPPA-002": {
        "action": "Freeze dispatch of products priced above the allowed ceiling until pricing is corrected.",
        "owner": "Commercial Compliance",
        "timeline": "24 hours",
    },
    "SLA-003": {
        "action": "Address inspection observations and update readiness evidence before the next state inspection.",
        "owner": "Site Quality Head",
        "timeline": "5 days",
    },
    "SLA-005": {
        "action": "Complete monitored storage controls for all batches, including range, monitoring system, and logs.",
        "owner": "Warehouse and QA",
        "timeline": "72 hours",
    },
}


DOMAIN_FALLBACKS: dict[str, dict[str, str]] = {
    "licensing": {"action": "Update license evidence and confirm current approval status with the issuing authority.", "owner": "Regulatory Affairs", "timeline": "3 days"},
    "quality": {"action": "Complete missing QA release evidence and verify approved QC documentation for all relevant batches.", "owner": "Quality Control", "timeline": "2 days"},
    "equipment": {"action": "Review equipment maintenance and calibration records, then close any overdue actions.", "owner": "Engineering", "timeline": "3 days"},
    "deviation": {"action": "Close deviations, complete CAPA effectiveness checks, and document QA approval.", "owner": "Quality Assurance", "timeline": "2 days"},
    "pricing": {"action": "Reconcile commercial pricing against the latest notified ceiling and document any required revision.", "owner": "Commercial Compliance", "timeline": "2 days"},
    "storage": {"action": "Document controlled storage conditions and verify active monitoring logs for all stored batches.", "owner": "Warehouse Operations", "timeline": "3 days"},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def derive_priority(status: str, severity: str, risk_score: float) -> str:
    if status == "non_compliant" or risk_score >= 85:
        return "Critical"
    if severity == "High" or risk_score >= 60:
        return "High"
    if status == "partial" or risk_score >= 35:
        return "Medium"
    return "Low"


def recommendation_template(requirement_id: str, domain: str) -> dict[str, str]:
    if requirement_id in RECOMMENDATION_LIBRARY:
        return RECOMMENDATION_LIBRARY[requirement_id]
    if domain in DOMAIN_FALLBACKS:
        return DOMAIN_FALLBACKS[domain]
    return {
        "action": "Review the failed requirement, gather missing evidence, and implement a documented corrective action plan.",
        "owner": "Compliance Team",
        "timeline": "5 days",
    }


def build_recommendations(assessment_data: dict[str, Any], risk_data: dict[str, Any]) -> dict[str, Any]:
    risk_map = {item["requirement_id"]: item for item in risk_data.get("requirement_scores", [])}
    actionable = [
        item
        for item in assessment_data.get("assessments", [])
        if item["status"] in {"partial", "non_compliant", "insufficient_data"}
    ]

    recommendations = []
    for item in actionable:
        risk_item = risk_map.get(item["requirement_id"])
        if risk_item is None:
            continue
        template = recommendation_template(item["requirement_id"], item["domain"])
        recommendations.append(
            {
                "requirement_id": item["requirement_id"],
                "regulatory_body": item["regulatory_body"],
                "domain": item["domain"],
                "status": item["status"],
                "severity": item["severity"],
                "risk_score": risk_item["risk_score"],
                "priority": derive_priority(item["status"], item["severity"], risk_item["risk_score"]),
                "issue": item["requirement_text"],
                "reason": item["evaluation_reason"],
                "recommended_action": template["action"],
                "owner": template["owner"],
                "timeline": template["timeline"],
                "evidence_reviewed": item.get("evaluation_evidence", []),
                "missing_attributes": item.get("missing_attributes", []),
                "failing_attributes": item.get("failing_attributes", []),
                "source_document": item["source_document"],
                "source_page": item["source_page"],
            }
        )

    recommendations.sort(
        key=lambda item: (
            item["priority"] != "Critical",
            item["priority"] != "High",
            item["priority"] != "Medium",
            -float(item["risk_score"]),
        )
    )

    return {
        "company_data_source": assessment_data.get("company_data_source", "in_memory"),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
    }


def main() -> None:
    assessment_data = load_json(ASSESSMENT_PATH)
    risk_data = load_json(RISK_REPORT_PATH)
    payload = build_recommendations(assessment_data, risk_data)
    save_json(OUTPUT_PATH, payload)
    print(f"Saved recommendations to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
