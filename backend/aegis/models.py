"""Modèles de données partagés (Pydantic)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


# Poids de sévérité utilisés dans le scoring.
SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.critical: 10,
    Severity.high: 7,
    Severity.medium: 4,
    Severity.low: 1,
}


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMResponse(BaseModel):
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    model: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class Detector(BaseModel):
    """Déclare comment juger si une attaque a réussi."""
    kind: str  # "canary" | "regex" | "refusal_bypass" | "amplification" | "judge"
    # paramètres selon le type
    canary: str | None = None
    patterns: list[str] = Field(default_factory=list)
    min_tokens: int | None = None
    judge_goal: str | None = None


class AttackProbe(BaseModel):
    """Une attaque unitaire chargée depuis un fichier YAML."""
    id: str
    owasp: str                       # p.ex. "LLM01", "jailbreak"
    title: str
    technique: str = "direct"
    severity: Severity = Severity.medium
    system_prompt: str | None = None
    context_docs: list[str] = Field(default_factory=list)
    prompt: str                      # message utilisateur de base
    detector: Detector
    mutations: list[str] = Field(default_factory=lambda: ["identity"])
    note: str | None = None


class AttackResult(BaseModel):
    probe_id: str
    owasp: str
    title: str
    technique: str
    severity: Severity
    mutation: str
    prompt_sent: str
    response_text: str
    success: bool                    # True => l'attaque a réussi (vulnérabilité)
    detector_kind: str
    confidence: float = 1.0
    rationale: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    error: str | None = None


class CategoryScore(BaseModel):
    owasp: str
    attempts: int
    successes: int
    asr: float                       # Attack Success Rate
    weight: int
    severity: Severity


class ScanReport(BaseModel):
    target: str
    judge: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    score: int = 0
    grade: str = "?"
    categories: list[CategoryScore] = Field(default_factory=list)
    results: list[AttackResult] = Field(default_factory=list)

    @property
    def vulnerabilities(self) -> list[AttackResult]:
        return [r for r in self.results if r.success]
