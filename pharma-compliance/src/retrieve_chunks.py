"""Retrieve the most relevant indexed chunks for a question."""

from __future__ import annotations

import os
import sys

try:
    from .rag_core import INDEX_DIR, load_json, sparse_cosine_similarity, tfidf_weights, tokenize
except ImportError:  # pragma: no cover - direct script fallback
    from rag_core import INDEX_DIR, load_json, sparse_cosine_similarity, tfidf_weights, tokenize


INDEX_PATH = INDEX_DIR / "vector_index.json"


def retrieve(question: str, top_k: int = 5) -> list[dict[str, object]]:
    """Retrieve the top-k most similar chunks for a question."""
    index_payload = load_json(INDEX_PATH)
    index_records = index_payload["records"]
    idf_map = index_payload["metadata"]["idf"]
    query_weights = tfidf_weights(tokenize(question), idf_map)
    scored: list[dict[str, object]] = []

    for item in index_records:
        score = sparse_cosine_similarity(query_weights, item["weights"])
        scored.append(
            {
                **{key: value for key, value in item.items() if key != "weights"},
                "score": score,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        os.environ["PYTHONIOENCODING"] = "utf-8"

    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Ask a retrieval question: ").strip()

    results = retrieve(question)
    if not results:
        print("No chunks retrieved.")
        return

    for item in results:
        print(f"[{item['score']}] {item['chunk_id']} | {item['source_name']} | page={item.get('page')}")
        print(item["text"][:500])
        print("-" * 80)


if __name__ == "__main__":
    main()
