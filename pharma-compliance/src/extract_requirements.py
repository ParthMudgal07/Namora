"""Build structured requirement JSON from the compliance matrix and regulation text."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "schemas" / "compliance_matrix.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "requirements.json"


def load_compliance_matrix() -> list[dict[str, str]]:
    """Load all requirement rows from the compliance matrix CSV."""
    with SCHEMA_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]


def load_regulation_text(regulatory_body: str) -> str:
    """Read the extracted text file for a regulatory body."""
    text_path = PROCESSED_DIR / f"{regulatory_body}.txt"
    if not text_path.exists():
        return ""
    return text_path.read_text(encoding="utf-8", errors="ignore")


def split_pages(text: str) -> list[tuple[int, str]]:
    """Split extracted text into page-numbered sections."""
    pages: list[tuple[int, str]] = []
    pattern = re.compile(r"--- PAGE (\d+) ---")
    matches = list(pattern.finditer(text))

    if not matches:
        return [(1, text.strip())] if text.strip() else []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        page_number = int(match.group(1))
        page_text = text[start:end].strip()
        if page_text:
            pages.append((page_number, page_text))

    return pages


def tokenize(value: str) -> set[str]:
    """Convert free text into simple lowercase keywords."""
    return {
        token
        for token in re.findall(r"[a-zA-Z]{4,}", value.lower())
        if token not in {"must", "with", "from", "that", "this", "have", "into", "through"}
    }


def pick_best_source_excerpt(requirement_text: str, pages: list[tuple[int, str]]) -> dict[str, object]:
    """Choose the page whose text best overlaps with the requirement language."""
    requirement_tokens = tokenize(requirement_text)
    best_page_number = None
    best_excerpt = ""
    best_score = -1

    for page_number, page_text in pages:
        page_tokens = tokenize(page_text)
        score = len(requirement_tokens & page_tokens)
        if score > best_score:
            best_score = score
            best_page_number = page_number
            best_excerpt = page_text[:800].strip()

    return {
        "page": best_page_number,
        "excerpt": best_excerpt,
        "match_score": max(best_score, 0),
    }


def build_requirement_record(row: dict[str, str], regulation_text: str) -> dict[str, object]:
    """Build one JSON-friendly requirement record."""
    pages = split_pages(regulation_text)
    source_match = pick_best_source_excerpt(row["requirement_text"], pages) if pages else {
        "page": None,
        "excerpt": "",
        "match_score": 0,
    }

    required_attributes = [
        item.strip() for item in row["required_company_attributes"].split(";") if item.strip()
    ]
    evidence_types = [item.strip() for item in row["evidence_type"].split(";") if item.strip()]

    return {
        "requirement_id": row["requirement_id"],
        "regulatory_body": row["regulatory_body"],
        "domain": row["domain"],
        "requirement_text": row["requirement_text"],
        "required_company_attributes": required_attributes,
        "evidence_type": evidence_types,
        "severity": row["severity"],
        "source_document": f"{row['regulatory_body']}.txt",
        "source_page": source_match["page"],
        "source_excerpt": source_match["excerpt"],
        "source_match_score": source_match["match_score"],
    }


def main() -> None:
    rows = load_compliance_matrix()
    regulation_cache: dict[str, str] = {}
    requirements: list[dict[str, object]] = []

    for row in rows:
        body = row["regulatory_body"]
        if body not in regulation_cache:
            regulation_cache[body] = load_regulation_text(body)

        requirements.append(build_requirement_record(row, regulation_cache[body]))

    OUTPUT_PATH.write_text(json.dumps(requirements, indent=2), encoding="utf-8")
    print(f"Saved {len(requirements)} requirements to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
