"""Basic Streamlit UI for the pharma compliance RAG pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from copilot import answer_question  # noqa: E402


ASSESSMENT_PATH = PROCESSED_DIR / "compliance_assessment.json"
RISK_REPORT_PATH = PROCESSED_DIR / "risk_report.json"
RECOMMENDATIONS_PATH = PROCESSED_DIR / "recommendations.json"
COMPANY_DATA_PATH = BASE_DIR / "data" / "company" / "company_data.json"


st.set_page_config(
    page_title="Pharma Compliance RAG",
    page_icon="P",
    layout="wide",
)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file if present."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_pipeline() -> tuple[bool, str]:
    """Run the current end-to-end local pipeline."""
    commands = [
        [sys.executable, str(SRC_DIR / "extract_text.py")],
        [sys.executable, str(SRC_DIR / "extract_requirements.py")],
        [sys.executable, str(SRC_DIR / "chunk_documents.py")],
        [sys.executable, str(SRC_DIR / "build_index.py")],
        [sys.executable, str(SRC_DIR / "match_requirements.py")],
        [sys.executable, str(SRC_DIR / "score_risk.py")],
        [sys.executable, str(SRC_DIR / "generate_recommendations.py")],
    ]

    outputs: list[str] = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip():
            outputs.append(result.stdout.strip())
        if result.returncode != 0:
            error_text = result.stderr.strip() or result.stdout.strip() or "Command failed."
            return False, error_text

    return True, "\n".join(outputs)


def render_metric_cards(risk_report: dict[str, Any], recommendations_data: dict[str, Any]) -> None:
    """Show top-level risk metrics."""
    counts = risk_report.get("status_counts", {})
    recommendation_count = recommendations_data.get("total_recommendations", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Risk Score", risk_report.get("overall_risk_score", "N/A"))
    col2.metric("Risk Band", risk_report.get("overall_risk_band", "N/A"))
    col3.metric("Compliant", counts.get("compliant", 0))
    col4.metric("Non-Compliant", counts.get("non_compliant", 0))
    col5.metric("Recommendations", recommendation_count)


def render_top_risks(risk_report: dict[str, Any]) -> None:
    """Show top risk drivers."""
    st.subheader("Top Risk Drivers")
    items = risk_report.get("top_risk_drivers", [])
    if not items:
        st.info("Run the pipeline to generate risk drivers.")
        return

    for item in items[:5]:
        with st.container(border=True):
            st.markdown(
                f"**{item['requirement_id']}** | {item['regulatory_body']} | {item['domain']} | "
                f"{item['risk_band']} {item['risk_score']}"
            )
            st.write(item["evaluation_reason"])
            if item.get("evaluation_evidence"):
                st.caption("Evidence: " + ", ".join(item["evaluation_evidence"]))


def render_group_tables(risk_report: dict[str, Any]) -> None:
    """Show risk grouped by body and domain."""
    body_rows = []
    for body, details in risk_report.get("risk_by_regulatory_body", {}).items():
        body_rows.append(
            {
                "Regulatory Body": body,
                "Average Score": details["average_score"],
                "Risk Band": details["risk_band"],
                "Compliant": details["status_counts"]["compliant"],
                "Partial": details["status_counts"]["partial"],
                "Non-Compliant": details["status_counts"]["non_compliant"],
            }
        )

    domain_rows = []
    for domain, details in risk_report.get("risk_by_domain", {}).items():
        domain_rows.append(
            {
                "Domain": domain,
                "Average Score": details["average_score"],
                "Risk Band": details["risk_band"],
                "Compliant": details["status_counts"]["compliant"],
                "Partial": details["status_counts"]["partial"],
                "Non-Compliant": details["status_counts"]["non_compliant"],
            }
        )

    left, right = st.columns(2)
    with left:
        st.subheader("Risk by Regulatory Body")
        st.dataframe(body_rows, use_container_width=True)
    with right:
        st.subheader("Risk by Domain")
        st.dataframe(domain_rows, use_container_width=True)


def render_findings(assessment_data: dict[str, Any]) -> None:
    """Render detailed compliance findings."""
    st.subheader("Compliance Findings")
    assessments = assessment_data.get("assessments", [])
    if not assessments:
        st.info("No assessment found yet.")
        return

    body_filter = st.selectbox("Regulatory body", ["All", "CDSCO", "GMP", "NPPA", "SLA"], key="body_filter")
    status_filter = st.selectbox(
        "Status",
        ["All", "non_compliant", "partial", "compliant", "insufficient_data"],
        key="status_filter",
    )

    filtered = [
        item
        for item in assessments
        if (body_filter == "All" or item["regulatory_body"] == body_filter)
        and (status_filter == "All" or item["status"] == status_filter)
    ]

    st.caption(f"{len(filtered)} findings shown")
    for item in filtered:
        with st.expander(f"{item['requirement_id']} | {item['regulatory_body']} | {item['status']}"):
            st.write(item["requirement_text"])
            st.write(f"Reason: {item['evaluation_reason']}")
            st.write(f"Severity: {item['severity']}")
            st.write(f"Coverage: {item['coverage_ratio']}")
            st.write(f"Source: {item['source_document']} page {item['source_page']}")
            if item.get("evaluation_evidence"):
                st.write("Evidence reviewed:")
                for evidence in item["evaluation_evidence"]:
                    st.write(f"- {evidence}")
            if item.get("failing_attributes"):
                st.write("Failing attributes:")
                for attribute in item["failing_attributes"]:
                    st.write(f"- {attribute}")
            if item.get("missing_attributes"):
                st.write("Missing attributes:")
                for attribute in item["missing_attributes"]:
                    st.write(f"- {attribute}")


def render_recommendations(recommendations_data: dict[str, Any]) -> None:
    """Render the recommendation list."""
    st.subheader("Recommendations")
    recommendations = recommendations_data.get("recommendations", [])
    if not recommendations:
        st.info("No recommendations found yet.")
        return

    priority = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="priority_filter")
    filtered = recommendations if priority == "All" else [item for item in recommendations if item["priority"] == priority]

    for item in filtered:
        with st.container(border=True):
            st.markdown(
                f"**{item['priority']}** | {item['requirement_id']} | {item['regulatory_body']} | owner: {item['owner']}"
            )
            st.write(item["recommended_action"])
            st.caption(f"Timeline: {item['timeline']} | Risk Score: {item['risk_score']}")
            st.write(f"Reason: {item['reason']}")


def render_copilot() -> None:
    """Render the basic grounded copilot chat."""
    st.subheader("RAG Copilot")
    st.caption("This uses the local knowledge base from the guideline PDFs, requirement records, company data, and generated outputs.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("Ask about risk, recommendations, or the indexed guideline knowledge base")
    if not prompt:
        return

    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching the knowledge base..."):
            response = answer_question(prompt)
            st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": response})


def render_data(company_data: dict[str, Any]) -> None:
    """Show the company dataset currently used."""
    st.subheader("Company Data")
    st.json(company_data)


def main() -> None:
    st.title("Pharma Compliance RAG Dashboard")
    st.caption("Basic visual layer for the local RAG pipeline, compliance matching, risk scoring, recommendations, and grounded copilot.")

    with st.sidebar:
        st.header("Pipeline")
        if st.button("Run / Refresh Pipeline", use_container_width=True):
            with st.spinner("Running pipeline..."):
                success, message = run_pipeline()
            if success:
                st.success("Pipeline completed.")
                if message:
                    st.code(message)
            else:
                st.error("Pipeline failed.")
                st.code(message)

        st.markdown("**Files in use**")
        st.caption(str(COMPANY_DATA_PATH))
        st.caption(str(ASSESSMENT_PATH))
        st.caption(str(RISK_REPORT_PATH))
        st.caption(str(RECOMMENDATIONS_PATH))

    assessment_data = load_json(ASSESSMENT_PATH)
    risk_report = load_json(RISK_REPORT_PATH)
    recommendations_data = load_json(RECOMMENDATIONS_PATH)
    company_data = load_json(COMPANY_DATA_PATH)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Findings", "Recommendations", "Copilot", "Company Data"]
    )

    with tab1:
        if risk_report:
            render_metric_cards(risk_report, recommendations_data)
            render_group_tables(risk_report)
            render_top_risks(risk_report)
        else:
            st.info("Run the pipeline first to generate the overview.")

    with tab2:
        render_findings(assessment_data)

    with tab3:
        render_recommendations(recommendations_data)

    with tab4:
        render_copilot()

    with tab5:
        render_data(company_data)


if __name__ == "__main__":
    main()
