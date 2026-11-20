"""Arène IA vs IA : une IA attaquante tente de contourner une IA cible, arbitrée par un juge."""
from .match import run_match
from .models import MatchResult, MatchRound

__all__ = ["run_match", "MatchResult", "MatchRound"]
