"""Type de verdict partagé par les évaluateurs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Verdict:
    success: bool          # True => l'attaque a réussi (vulnérabilité détectée)
    confidence: float      # 0.0 – 1.0
    rationale: str
