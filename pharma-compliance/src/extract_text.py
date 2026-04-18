"""Extract text from regulatory PDF documents into plain text files."""

from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:
    fitz = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


BASE_DIR = Path(__file__).resolve().parents[1]
REGULATIONS_DIR = BASE_DIR / "data" / "regulations"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def extract_pdf_text(pdf_path: Path) -> str:
    """Read all pages from a PDF and return one combined text string."""
    parts: list[str] = []

    if fitz is not None:
        with fitz.open(pdf_path) as document:
            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text("text").strip()
                if not page_text:
                    continue

                parts.append(f"--- PAGE {page_number} ---")
                parts.append(page_text)
        return "\n\n".join(parts).strip()

    if PdfReader is not None:
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue

            parts.append(f"--- PAGE {page_number} ---")
            parts.append(page_text)
        return "\n\n".join(parts).strip()

    raise ImportError(
        "No PDF reader available. Install either 'PyMuPDF' or 'pypdf' in your Python environment."
    )


def save_text_output(source_pdf: Path, text: str) -> Path:
    """Save extracted text next to other processed outputs."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"{source_pdf.stem}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def main() -> None:
    pdf_files = sorted(REGULATIONS_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {REGULATIONS_DIR}")
        return

    for pdf_file in pdf_files:
        extracted_text = extract_pdf_text(pdf_file)
        output_path = save_text_output(pdf_file, extracted_text)
        print(f"Extracted: {pdf_file.name} -> {output_path.name}")


if __name__ == "__main__":
    main()
