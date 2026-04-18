"""Build a lightweight local vector index for regulation retrieval."""

from __future__ import annotations

import math

from rag_core import INDEX_DIR, PROCESSED_DIR, load_json, save_json, tfidf_weights, tokenize


CHUNKS_PATH = PROCESSED_DIR / "rag_chunks.json"
INDEX_PATH = INDEX_DIR / "vector_index.json"


def main() -> None:
    chunks = load_json(CHUNKS_PATH)
    document_frequency: dict[str, int] = {}
    indexed_chunks = []

    for chunk in chunks:
        tokens = tokenize(chunk["text"])
        unique_tokens = set(tokens)
        for token in unique_tokens:
            document_frequency[token] = document_frequency.get(token, 0) + 1
        indexed_chunks.append({**chunk, "tokens": tokens})

    total_documents = len(indexed_chunks)
    idf_map = {
        token: round(math.log((total_documents + 1) / (count + 1)) + 1.0, 6)
        for token, count in document_frequency.items()
    }

    index_records = []

    for chunk in indexed_chunks:
        index_records.append(
            {
                **{key: value for key, value in chunk.items() if key != "tokens"},
                "weights": tfidf_weights(chunk["tokens"], idf_map),
            }
        )

    payload = {
        "metadata": {
            "method": "tfidf_sparse",
            "document_count": total_documents,
            "vocabulary_size": len(idf_map),
            "idf": idf_map,
        },
        "records": index_records,
    }
    save_json(INDEX_PATH, payload)
    print(f"Saved {len(index_records)} indexed chunks to {INDEX_PATH}")


if __name__ == "__main__":
    main()
