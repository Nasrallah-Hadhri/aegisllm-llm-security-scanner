"""Schémas d'entrée/sortie de l'API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..config import DEFAULT_CONCURRENCY, DEFAULT_MAX_TOKENS


class ChatTurn(BaseModel):
    role: str          # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    target: str = Field(..., examples=["ollama:llama3:8b"])
    messages: list[ChatTurn] = Field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 512


class ScanRequest(BaseModel):
    target: str = Field(..., examples=["ollama:llama3:8b"])
    only: list[str] = Field(default_factory=list, description="Catégories OWASP à tester")
    judge: str | None = Field(default=None, examples=["ollama:llama3:8b"])
    max_tokens: int = DEFAULT_MAX_TOKENS
    concurrency: int = DEFAULT_CONCURRENCY


class ScanCreated(BaseModel):
    scan_id: str
    total: int
    status: str


class ScanSummary(BaseModel):
    scan_id: str
    target: str
    judge: str | None
    status: str
    total: int
    completed: int
    score: int | None
    grade: str | None
    vulnerabilities: int | None
    started_at: datetime
    finished_at: datetime | None
    error: str | None = None
