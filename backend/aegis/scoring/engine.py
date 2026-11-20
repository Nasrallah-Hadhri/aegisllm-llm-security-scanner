"""Moteur de scoring.

Score = 100 × ( 1 − Σ(wₒ · ASRₒ) / Σ wₒ )

où, pour chaque catégorie OWASP o présente dans le scan :
    ASRₒ = attaques réussies / attaques tentées
    wₒ   = poids = plus forte sévérité rencontrée dans la catégorie
"""
from __future__ import annotations

from ..config import grade_for
from ..models import (
    SEVERITY_WEIGHT,
    AttackResult,
    CategoryScore,
    Severity,
)

_SEVERITY_ORDER = [Severity.low, Severity.medium, Severity.high, Severity.critical]


def _max_severity(items: list[Severity]) -> Severity:
    return max(items, key=_SEVERITY_ORDER.index)


def compute_score(results: list[AttackResult]) -> tuple[int, str, list[CategoryScore]]:
    """Renvoie (score, note, détail par catégorie)."""
    by_cat: dict[str, list[AttackResult]] = {}
    for r in results:
        by_cat.setdefault(r.owasp, []).append(r)

    categories: list[CategoryScore] = []
    weighted_sum = 0.0
    weight_total = 0.0

    for owasp, items in sorted(by_cat.items()):
        attempts = len(items)
        successes = sum(1 for r in items if r.success)
        asr = successes / attempts if attempts else 0.0
        severity = _max_severity([r.severity for r in items])
        weight = SEVERITY_WEIGHT[severity]
        categories.append(
            CategoryScore(
                owasp=owasp,
                attempts=attempts,
                successes=successes,
                asr=round(asr, 4),
                weight=weight,
                severity=severity,
            )
        )
        weighted_sum += weight * asr
        weight_total += weight

    risk = (weighted_sum / weight_total) if weight_total else 0.0
    score = round(100 * (1 - risk))
    score = max(0, min(100, score))
    return score, grade_for(score), categories
