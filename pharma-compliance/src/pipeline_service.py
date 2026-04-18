"""Service helpers for running the compliance pipeline in memory."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

try:
    from .copilot import answer_question_with_context
    from .generate_recommendations import build_recommendations
    from .match_requirements import (
        REQUIREMENTS_PATH,
        REFERENCE_DATE,
        build_assessment,
        load_json,
    )
    from .score_risk import build_risk_report
except ImportError:  # pragma: no cover - direct script fallback
    from copilot import answer_question_with_context
    from generate_recommendations import build_recommendations
    from match_requirements import (
        REQUIREMENTS_PATH,
        REFERENCE_DATE,
        build_assessment,
        load_json,
    )
    from score_risk import build_risk_report


def analyze_company_data(
    company_data: dict[str, Any],
    *,
    selected_guidelines: list[str] | None = None,
) -> dict[str, Any]:
    """Run compliance assessment, risk scoring, and recommendations in memory."""
    requirements = load_json(REQUIREMENTS_PATH)
    selected = {item.upper() for item in (selected_guidelines or []) if str(item).strip()}
    if selected:
        requirements = [
            requirement
            for requirement in requirements
            if requirement["regulatory_body"].upper() in selected
        ]

    normalized_company_data = deepcopy(company_data)
    normalized_company_data["regulatory_scope"] = sorted(selected) if selected else normalized_company_data.get("regulatory_scope", [])

    assessments = [build_assessment(requirement, normalized_company_data) for requirement in requirements]
    assessment_data = {
        "company_data_source": "api_submission",
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

    risk_report = build_risk_report(assessment_data)
    recommendations = build_recommendations(assessment_data, risk_report)

    return {
        "company_data": normalized_company_data,
        "assessment": assessment_data,
        "risk_report": risk_report,
        "recommendations": recommendations,
    }


def answer_copilot_question(
    question: str,
    company_data: dict[str, Any],
    *,
    selected_guidelines: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze the company submission and answer a copilot question against live results."""
    analysis = analyze_company_data(company_data, selected_guidelines=selected_guidelines)
    answer = answer_question_with_context(
        question,
        analysis["assessment"],
        analysis["risk_report"],
        analysis["recommendations"],
    )
    return {
        "question": question,
        "answer": answer,
        "analysis": analysis,
    }
