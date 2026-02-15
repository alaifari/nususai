from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=6000)
    top_k: int | None = Field(default=None, ge=3, le=30)
    max_opinions: int | None = Field(default=None, ge=2, le=8)


class Citation(BaseModel):
    id: str
    book_title_ar: str
    author_ar: str
    source_ref_ar: str
    volume: str | None = None
    page: str | None = None
    snippet_ar: str
    score: float


class Opinion(BaseModel):
    title: str
    summary: str
    citation_ids: list[str]


class ChatResponse(BaseModel):
    answer: str
    language: str
    opinions: list[Opinion]
    citations: list[Citation]
    notes: list[str] = Field(default_factory=list)
