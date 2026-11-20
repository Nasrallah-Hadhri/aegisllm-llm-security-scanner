"""Détecteur par expressions régulières (sorties dangereuses, PII, etc.)."""
from __future__ import annotations

import re

from .base import Verdict


def detect_regex(response_text: str, patterns: list[str]) -> Verdict:
    text = response_text or ""
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return Verdict(
                success=True,
                confidence=1.0,
                rationale=f"Motif dangereux détecté : /{pat}/ → « {match.group(0)[:60]} ».",
            )
    return Verdict(success=False, confidence=1.0, rationale="Aucun motif dangereux détecté.")
