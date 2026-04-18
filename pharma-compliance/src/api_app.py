"""FastAPI backend for the pharma compliance RAG pipeline."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .pipeline_service import analyze_company_data, answer_copilot_question
except ImportError:  # pragma: no cover - direct script fallback
    from pipeline_service import analyze_company_data, answer_copilot_question


class AnalyzeRequest(BaseModel):
    company_data: dict[str, Any] = Field(..., description="Company payload collected from the frontend")
    selected_guidelines: list[str] = Field(default_factory=list)


class ChatRequest(AnalyzeRequest):
    question: str = Field(..., min_length=1)


app = FastAPI(title="Nomora Compliance API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    return analyze_company_data(
        request.company_data,
        selected_guidelines=request.selected_guidelines,
    )


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    return answer_copilot_question(
        request.question,
        request.company_data,
        selected_guidelines=request.selected_guidelines,
    )
