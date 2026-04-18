"""Answer questions from the local RAG index."""

from __future__ import annotations

import os
import sys

try:
    from .rag_core import INDEX_DIR, build_answer, save_json
    from .retrieve_chunks import retrieve
except ImportError:  # pragma: no cover - direct script fallback
    from rag_core import INDEX_DIR, build_answer, save_json
    from retrieve_chunks import retrieve


OUTPUT_PATH = INDEX_DIR / "last_rag_answer.json"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        os.environ["PYTHONIOENCODING"] = "utf-8"

    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Ask a RAG question: ").strip()

    retrieved = retrieve(question)
    answer = build_answer(question, retrieved)
    save_json(OUTPUT_PATH, answer)

    print(f"Answer mode: {answer['answer_mode']}")
    if answer.get("llm_error"):
        print(f"LLM status: {answer['llm_error']}")
        print("Falling back to local extractive answer.\n")

    print(answer["answer"])
    print("\nSources:")
    for source in answer["sources"]:
        print(
            f"- {source['source_name']} | type={source['source_type']} | "
            f"page={source['page']} | score={source['score']}"
        )


if __name__ == "__main__":
    main()
