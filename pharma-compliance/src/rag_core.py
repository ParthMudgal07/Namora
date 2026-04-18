"""Core utilities for a lightweight local RAG pipeline."""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INDEX_DIR = BASE_DIR / "data" / "index"
ENV_PATH = BASE_DIR / ".env"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9\-_/]*")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "will",
    "with",
}


def load_dotenv(path: Path = ENV_PATH) -> None:
    """Load simple KEY=VALUE pairs from a local .env file without extra dependencies."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


def load_json(path: Path) -> Any:
    """Load JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    """Persist JSON with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def tokenize(text: str) -> list[str]:
    """Tokenize text into normalized keywords."""
    tokens = [token.lower() for token in TEXT_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def split_sentences(text: str) -> list[str]:
    """Split text into simple sentences."""
    sentences = [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(text) if part.strip()]
    return sentences if sentences else [text.strip()]


def dense_hash_embedding(text: str, dimensions: int = 256) -> list[float]:
    """Create a lightweight local embedding by hashing tokens into a dense vector."""
    vector = [0.0] * dimensions
    tokens = tokenize(text)

    if not tokens:
        return vector

    for token in tokens:
        slot = hash(token) % dimensions
        sign = 1.0 if hash(f"{token}:sign") % 2 == 0 else -1.0
        vector[slot] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for normalized vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0
    return round(sum(a * b for a, b in zip(left, right)), 6)


def term_frequency(tokens: list[str]) -> dict[str, float]:
    """Build normalized term frequency values."""
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return {}
    return {token: count / total for token, count in counts.items()}


def tfidf_weights(tokens: list[str], idf_map: dict[str, float]) -> dict[str, float]:
    """Create normalized sparse TF-IDF weights."""
    tf_map = term_frequency(tokens)
    weights = {token: tf * idf_map.get(token, 0.0) for token, tf in tf_map.items()}
    norm = math.sqrt(sum(value * value for value in weights.values()))
    if norm == 0:
        return {}
    return {token: round(value / norm, 6) for token, value in weights.items()}


def sparse_cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    """Compute cosine similarity for normalized sparse vectors."""
    if not left or not right:
        return 0.0

    shared = set(left) & set(right)
    if not shared:
        return 0.0
    return round(sum(left[token] * right[token] for token in shared), 6)


def chunk_text(
    text: str,
    *,
    chunk_word_target: int = 170,
    chunk_word_overlap: int = 35,
) -> list[str]:
    """Chunk long text into overlapping word windows while preserving sentence boundaries."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current_sentences: list[str] = []
    current_words = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_sentences and current_words + word_count > chunk_word_target:
            chunks.append(" ".join(current_sentences).strip())

            overlap_sentences: list[str] = []
            overlap_words = 0
            for existing in reversed(current_sentences):
                overlap_sentences.insert(0, existing)
                overlap_words += len(existing.split())
                if overlap_words >= chunk_word_overlap:
                    break

            current_sentences = overlap_sentences
            current_words = sum(len(item.split()) for item in current_sentences)

        current_sentences.append(sentence)
        current_words += word_count

    if current_sentences:
        chunks.append(" ".join(current_sentences).strip())

    return [chunk for chunk in chunks if chunk]


def _extractive_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    """Create a grounded extractive answer from retrieved chunks without an external LLM."""
    question_terms = set(tokenize(question))
    cited_sentences: list[str] = []

    for chunk in retrieved_chunks:
        sentences = split_sentences(chunk["text"])
        scored_sentences: list[tuple[int, str]] = []
        for sentence in sentences:
            overlap = len(question_terms & set(tokenize(sentence)))
            if overlap > 0:
                scored_sentences.append((overlap, sentence))

        scored_sentences.sort(key=lambda item: item[0], reverse=True)
        if scored_sentences:
            cited_sentences.append(scored_sentences[0][1])
        elif sentences:
            cited_sentences.append(sentences[0])

    if not cited_sentences:
        return (
            "I could not find relevant grounded context in the indexed knowledge base for that question."
        )
    return " ".join(cited_sentences[:4]).strip()


def _build_sources(retrieved_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize retrieved chunk metadata into source citations."""
    return [
        {
            "source_type": chunk["source_type"],
            "source_name": chunk["source_name"],
            "page": chunk.get("page"),
            "chunk_id": chunk["chunk_id"],
            "score": chunk["score"],
        }
        for chunk in retrieved_chunks
    ]


def _build_llm_messages(question: str, retrieved_chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build a grounded prompt for OpenRouter answer generation."""
    context_blocks = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"source_name: {chunk['source_name']}",
                    f"source_type: {chunk['source_type']}",
                    f"page: {chunk.get('page')}",
                    f"score: {chunk['score']}",
                    "content:",
                    chunk["text"],
                ]
            )
        )

    system_prompt = (
        "You are a pharma compliance RAG assistant. "
        "Answer only from the provided retrieved context. "
        "If the context is insufficient, clearly say that the knowledge base does not contain enough evidence. "
        "Do not invent regulations, citations, pages, or company facts. "
        "Prefer concise, accurate, compliance-oriented answers."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Retrieved context:\n\n{chr(10).join(context_blocks)}\n\n"
        "Return a direct answer grounded in this context."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _openrouter_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Generate a final answer from retrieved chunks using OpenRouter, when configured."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("OPENROUTER_MODEL", "").strip()
    if not api_key or not model or not retrieved_chunks:
        return "", None

    payload = {
        "model": model,
        "messages": _build_llm_messages(question, retrieved_chunks),
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        OPENROUTER_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/pharma-compliance-rag",
            "X-Title": "Pharma Compliance RAG",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover - defensive fallback
            error_body = str(exc)
        return "", f"OpenRouter HTTP {exc.code}: {error_body}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return "", f"OpenRouter request failed: {exc}"

    choices = body.get("choices", [])
    if not choices:
        return "", "OpenRouter returned no choices."

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        content = "\n".join(part.strip() for part in parts if part.strip())

    content = str(content).strip()
    if not content:
        return "", "OpenRouter returned an empty answer."
    return content, None


def build_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a grounded answer from retrieved chunks, optionally using OpenRouter."""
    sources = _build_sources(retrieved_chunks)
    llm_answer, llm_error = _openrouter_answer(question, retrieved_chunks)
    if llm_answer:
        answer_text = llm_answer
        answer_mode = "openrouter"
    else:
        answer_text = _extractive_answer(question, retrieved_chunks)
        answer_mode = "extractive"

    return {
        "question": question,
        "answer": answer_text,
        "answer_mode": answer_mode,
        "llm_error": llm_error,
        "sources": sources,
    }
