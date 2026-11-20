"""Modèles de données de l'arène."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MatchRound(BaseModel):
    index: int
    attack_prompt: str
    target_response: str
    leaked: bool
    judge_score: int | None = None       # 0–10 : proximité de la fuite (si juge)
    judge_rationale: str = ""


class MatchResult(BaseModel):
    attacker: str
    target: str
    judge: str | None = None
    goal: str
    winner: str = "defender"             # "attacker" | "defender"
    leaked: bool = False
    rounds_played: int = 0
    max_rounds: int = 5
    rounds: list[MatchRound] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
