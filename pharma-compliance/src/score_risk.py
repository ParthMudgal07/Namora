"""Calculate rule-based compliance risk scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
ASSESSMENT_PATH = BASE_DIR / "data" / "processed" / "compliance_assessment.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "risk_report.json"

STATUS_BASE_SCORE = {
    "compliant": 0,
    "partial": 50,
    "non_compliant": 100,
    "insufficient_data": 70,
}

SEVERITY_WEIGHT = {
    "Low": 1.0,
    "Medium": 1.25,
    "High": 1.5,
}

RISK_BANDS = ((75, "High"), (40, "Medium"), (0, "Low"))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def classify(score: float) -> str:
    for threshold, label in RISK_BANDS:
        if score >= threshold:
            return label
    return "Low"


def weighted_average(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    total_weight = sum(float(item.get("severity_weight", 1.0)) for item in items)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(float(item["risk_score"]) * float(item.get("severity_weight", 1.0)) for item in items)
    return round(weighted_sum / total_weight, 2)


def calculate_requirement_risk(assessment: dict[str, Any]) -> dict[str, Any]:
    status = assessment["status"]
    severity = assessment["severity"]
    base_score = STATUS_BASE_SCORE.get(status, 70)
    weight = SEVERITY_WEIGHT.get(severity, 1.0)
    risk_score = clamp_score(base_score * weight)
    return {
        "requirement_id": assessment["requirement_id"],
        "regulatory_body": assessment["regulatory_body"],
        "domain": assessment["domain"],
        "severity": severity,
        "status": status,
        "base_score": base_score,
        "severity_weight": weight,
        "risk_score": risk_score,
        "risk_band": classify(risk_score),
        "requirement_text": assessment["requirement_text"],
        "evaluation_reason": assessment.get("evaluation_reason", ""),
        "evaluation_evidence": assessment.get("evaluation_evidence", []),
        "missing_attributes": assessment.get("missing_attributes", []),
        "failing_attributes": assessment.get("failing_attributes", []),
        "source_document": assessment["source_document"],
        "source_page": assessment["source_page"],
    }


def build_group_summary(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item[key], []).append(item)
    summary: dict[str, Any] = {}
    for group_name, group_items in grouped.items():
        group_score = weighted_average(group_items)
        summary[group_name] = {
            "average_score": group_score,
            "risk_band": classify(group_score),
            "requirement_count": len(group_items),
            "status_counts": {
                "compliant": sum(entry["status"] == "compliant" for entry in group_items),
                "partial": sum(entry["status"] == "partial" for entry in group_items),
                "non_compliant": sum(entry["status"] == "non_compliant" for entry in group_items),
                "insufficient_data": sum(entry["status"] == "insufficient_data" for entry in group_items),
            },
        }
    return summary


def build_top_risk_drivers(items: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    sorted_items = sorted(items, key=lambda item: (item["risk_score"], item["severity"] == "High"), reverse=True)
    drivers = []
    for item in sorted_items[:limit]:
        drivers.append(
            {
                "requirement_id": item["requirement_id"],
                "regulatory_body": item["regulatory_body"],
                "domain": item["domain"],
                "risk_score": item["risk_score"],
                "risk_band": item["risk_band"],
                "status": item["status"],
                "requirement_text": item["requirement_text"],
                "evaluation_reason": item["evaluation_reason"],
                "evaluation_evidence": item["evaluation_evidence"],
                "missing_attributes": item["missing_attributes"],
                "failing_attributes": item["failing_attributes"],
            }
        )
    return drivers


def build_risk_report(assessment_data: dict[str, Any]) -> dict[str, Any]:
    requirement_scores = [calculate_requirement_risk(item) for item in assessment_data["assessments"]]
    overall_score = weighted_average(requirement_scores)
    return {
        "company_data_source": assessment_data.get("company_data_source", "in_memory"),
        "total_requirements": assessment_data["total_requirements"],
        "overall_risk_score": overall_score,
        "overall_risk_band": classify(overall_score),
        "status_counts": assessment_data["status_counts"],
        "risk_by_regulatory_body": build_group_summary(requirement_scores, "regulatory_body"),
        "risk_by_domain": build_group_summary(requirement_scores, "domain"),
        "top_risk_drivers": build_top_risk_drivers(requirement_scores),
        "requirement_scores": requirement_scores,
    }


def main() -> None:
    assessment_data = load_json(ASSESSMENT_PATH)
    payload = build_risk_report(assessment_data)
    save_json(OUTPUT_PATH, payload)
    print(f"Saved risk report to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
