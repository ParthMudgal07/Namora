"""Chunk extracted regulation text, requirement records, and company data for retrieval."""

from __future__ import annotations

import re
from pathlib import Path

from rag_core import BASE_DIR, PROCESSED_DIR, chunk_text, load_json, save_json


PAGE_PATTERN = re.compile(r"--- PAGE (\d+) ---")
OUTPUT_PATH = PROCESSED_DIR / "rag_chunks.json"
COMPANY_DATA_PATH = BASE_DIR / "data" / "company" / "company_data.json"
SECTION_HINTS = {
    "licenses": "Relevant to CDSCO and SLA licensing compliance, manufacturing license validity, issue date, expiry date, and issuing authority.",
    "products": "Relevant to NPPA pricing compliance, ceiling price, MRP, price to retailer, formulation type, dosage strength, and price revision evidence.",
    "batches": "Relevant to CDSCO and GMP batch manufacturing records, product release, distributor traceability, and batch-level evidence.",
    "quality_records": "Relevant to CDSCO and GMP quality control evidence, COA records, test results, and approval status.",
    "raw_materials_and_vendors": "Relevant to CDSCO and GMP raw material qualification, vendor approval, and material specifications.",
    "equipment_records": "Relevant to GMP and CDSCO equipment calibration, maintenance status, last calibration date, and next due date.",
    "deviations_and_capa": "Relevant to CDSCO and GMP deviation management, root cause analysis, CAPA, and closure status.",
    "inspection_records": "Relevant to SLA and CDSCO inspection observations, compliance status, and regulator review evidence.",
    "storage_records": "Relevant to SLA, CDSCO, and GMP storage compliance, monitored temperature control, storage range, and logs.",
    "documents": "Relevant to document control, version traceability, and compliance evidence management.",
    "audit_trail_logs": "Relevant to data integrity, audit trail, user actions, timestamps, and regulated record changes."
}


def chunk_regulation_text(text_path: Path) -> list[dict[str, object]]:
    """Chunk one extracted regulation text file."""
    raw_text = text_path.read_text(encoding="utf-8", errors="ignore")
    matches = list(PAGE_PATTERN.finditer(raw_text))
    page_sections: list[tuple[int, str]] = []

    if matches:
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
            page_number = int(match.group(1))
            page_text = raw_text[start:end].strip()
            if page_text:
                page_sections.append((page_number, page_text))
    elif raw_text.strip():
        page_sections.append((1, raw_text.strip()))

    chunks: list[dict[str, object]] = []
    for page_number, page_text in page_sections:
        for index, chunk in enumerate(chunk_text(page_text), start=1):
            chunks.append(
                {
                    "chunk_id": f"{text_path.stem.lower()}-page-{page_number}-chunk-{index}",
                    "source_type": "regulation_text",
                    "source_name": text_path.name,
                    "page": page_number,
                    "text": chunk,
                }
            )
    return chunks


def chunk_requirement_records() -> list[dict[str, object]]:
    """Turn structured requirements into retrieval chunks."""
    requirements_path = PROCESSED_DIR / "requirements.json"
    if not requirements_path.exists():
        return []

    requirements = load_json(requirements_path)
    chunks: list[dict[str, object]] = []
    for item in requirements:
        summary = (
            f"Requirement {item['requirement_id']} from {item['regulatory_body']} in domain {item['domain']}. "
            f"{item['requirement_text']} Evidence types: {', '.join(item['evidence_type'])}. "
            f"Required company attributes: {', '.join(item['required_company_attributes'])}."
        )
        chunks.append(
            {
                "chunk_id": f"requirement-{item['requirement_id'].lower()}",
                "source_type": "requirement_record",
                "source_name": "requirements.json",
                "page": item.get("source_page"),
                "text": summary,
                "requirement_id": item["requirement_id"],
                "regulatory_body": item["regulatory_body"],
                "domain": item["domain"],
            }
        )
    return chunks


def format_scalar(value: object) -> str:
    """Render a scalar or list value into compact text."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value).strip()


def chunk_company_data() -> list[dict[str, object]]:
    """Turn structured company data into retrieval chunks."""
    if not COMPANY_DATA_PATH.exists():
        return []

    company_data = load_json(COMPANY_DATA_PATH)
    company_name = company_data.get("company_name") or "Unknown company"
    chunks: list[dict[str, object]] = []

    for section_name, records in company_data.items():
        if section_name in {"company_name", "manufacturer_name", "regulatory_scope"}:
            continue
        if not isinstance(records, list):
            continue

        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue

            details = []
            for key, value in record.items():
                rendered = format_scalar(value)
                if rendered:
                    details.append(f"{key}: {rendered}")

            if not details:
                continue

            summary = (
                f"Company evidence record for {company_name}. Section {section_name}. "
                f"{SECTION_HINTS.get(section_name, '')} "
                + " ".join(details)
            )

            chunks.append(
                {
                    "chunk_id": f"company-{section_name}-{index}",
                    "source_type": "company_record",
                    "source_name": "company_data.json",
                    "page": None,
                    "text": summary,
                    "section": section_name,
                }
            )

    return chunks


def main() -> None:
    regulation_chunks: list[dict[str, object]] = []
    for text_path in sorted(PROCESSED_DIR.glob("*.txt")):
        regulation_chunks.extend(chunk_regulation_text(text_path))

    requirement_chunks = chunk_requirement_records()
    company_chunks = chunk_company_data()
    all_chunks = regulation_chunks + requirement_chunks + company_chunks
    save_json(OUTPUT_PATH, all_chunks)
    print(f"Saved {len(all_chunks)} chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
