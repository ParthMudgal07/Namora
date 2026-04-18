"""Grounded pharma compliance copilot using the local RAG index."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from .rag_core import build_answer, load_json as load_core_json, save_json
    from .retrieve_chunks import retrieve
except ImportError:  # pragma: no cover - direct script fallback
    from rag_core import build_answer, load_json as load_core_json, save_json
    from retrieve_chunks import retrieve


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ASSESSMENT_PATH = PROCESSED_DIR / "compliance_assessment.json"
RISK_REPORT_PATH = PROCESSED_DIR / "risk_report.json"
RECOMMENDATIONS_PATH = PROCESSED_DIR / "recommendations.json"
OUTPUT_PATH = BASE_DIR / "data" / "index" / "last_copilot_answer.json"
KNOWN_BODIES = ("CDSCO", "GMP", "NPPA", "SLA")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def detect_body(question: str) -> str | None:
    upper = question.upper()
    for body in KNOWN_BODIES:
        if body in upper:
            return body
    return None


def format_bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def answer_summary(risk_report: dict[str, Any]) -> str:
    if not risk_report:
        return "Risk report is not available yet."
    counts = risk_report["status_counts"]
    body_lines = []
    for body, details in risk_report["risk_by_regulatory_body"].items():
        body_lines.append(
            f"{body}: score {details['average_score']} ({details['risk_band']}), compliant {details['status_counts']['compliant']}, partial {details['status_counts']['partial']}, non-compliant {details['status_counts']['non_compliant']}"
        )
    return (
        f"Overall risk score is {risk_report['overall_risk_score']} ({risk_report['overall_risk_band']}).\n"
        f"Status counts: compliant {counts['compliant']}, partial {counts['partial']}, non-compliant {counts['non_compliant']}, insufficient data {counts['insufficient_data']}.\n"
        f"By regulatory body:\n{format_bullets(body_lines)}"
    )


def answer_fix_first(recommendations_data: dict[str, Any]) -> str:
    recommendations = recommendations_data.get("recommendations", [])
    if not recommendations:
        return "Recommendations are not available yet."
    lines = []
    for item in recommendations[:5]:
        lines.append(
            f"{item['priority']} - {item['requirement_id']} ({item['regulatory_body']}): {item['recommended_action']} [reason: {item['reason']}]"
        )
    return "Fix these first:\n" + format_bullets(lines)


def answer_body_question(body: str, assessments: list[dict[str, Any]], risk_report: dict[str, Any], recommendations: list[dict[str, Any]]) -> str:
    body_assessments = [item for item in assessments if item["regulatory_body"] == body]
    if not body_assessments:
        return f"No assessment data found for {body}."
    risk_info = risk_report.get("risk_by_regulatory_body", {}).get(body, {})
    lines = []
    if risk_info:
        lines.append(
            f"{body} score is {risk_info['average_score']} ({risk_info['risk_band']}). Status counts: compliant {risk_info['status_counts']['compliant']}, partial {risk_info['status_counts']['partial']}, non-compliant {risk_info['status_counts']['non_compliant']}."
        )
    failing = [item for item in body_assessments if item["status"] != "compliant"]
    if failing:
        lines.append("Main issues:")
        lines.extend(f"{item['requirement_id']}: {item['status']} because {item['evaluation_reason']}" for item in failing[:5])
    body_recommendations = [item for item in recommendations if item["regulatory_body"] == body]
    if body_recommendations:
        lines.append("Recommended next actions:")
        lines.extend(f"{item['priority']}: {item['recommended_action']} (owner: {item['owner']}, timeline: {item['timeline']})" for item in body_recommendations[:3])
    return "\n".join(lines)


def answer_rag(question: str) -> str:
    retrieved = retrieve(question, top_k=5)
    answer = build_answer(question, retrieved)
    save_json(OUTPUT_PATH, answer)
    lines = []
    if answer.get("answer_mode") == "openrouter":
        lines.append("Mode: OpenRouter grounded answer")
    else:
        lines.append("Mode: Local extractive answer")
        if answer.get("llm_error"):
            lines.append(f"LLM unavailable: {answer['llm_error']}")
    lines.extend([answer["answer"], "", "Sources:"])
    for source in answer["sources"]:
        lines.append(
            f"- {source['source_name']} | type={source['source_type']} | page={source['page']} | score={source['score']}"
        )
    return "\n".join(lines)


def answer_question_with_context(
    question: str,
    assessment_data: dict[str, Any],
    risk_report: dict[str, Any],
    recommendations_data: dict[str, Any],
) -> str:
    normalized = question.strip().lower()
    assessments = assessment_data.get("assessments", [])
    recommendations = recommendations_data.get("recommendations", [])

    if not normalized:
        return (
            "Ask something like:\n"
            "- What are our top 5 compliance risks?\n"
            "- What should we fix first?\n"
            "- Give me a compliance summary.\n"
            "- What does NPPA require for ceiling price compliance?"
        )

    if "summary" in normalized or "overall" in normalized:
        return answer_summary(risk_report)

    if "fix first" in normalized or "what should we fix" in normalized or "recommend" in normalized:
        return answer_fix_first(recommendations_data)

    if "top" in normalized and "risk" in normalized:
        drivers = risk_report.get("top_risk_drivers", [])
        if not drivers:
            return "Risk report is not available yet."
        lines = [
            f"{item['requirement_id']} ({item['regulatory_body']}, {item['domain']}): {item['risk_band']} risk {item['risk_score']} because {item['evaluation_reason']}"
            for item in drivers[:5]
        ]
        return "Top risk drivers:\n" + format_bullets(lines)

    body = detect_body(question)
    if body and assessments:
        return answer_body_question(body, assessments, risk_report, recommendations)

    return answer_rag(question)


def answer_question(question: str) -> str:
    assessment_data = load_json(ASSESSMENT_PATH)
    risk_report = load_json(RISK_REPORT_PATH)
    recommendations_data = load_json(RECOMMENDATIONS_PATH)
    return answer_question_with_context(question, assessment_data, risk_report, recommendations_data)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        os.environ["PYTHONIOENCODING"] = "utf-8"

    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Ask the compliance copilot: ").strip()
    print(answer_question(question))


if __name__ == "__main__":
    main()
