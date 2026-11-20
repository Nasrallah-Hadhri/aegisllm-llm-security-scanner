"""Classement persistant des modèles (attaque et défense)."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import REPORTS_DIR
from .models import MatchResult

_FILE = REPORTS_DIR / "arena_leaderboard.json"


def _load() -> dict[str, dict]:
    if _FILE.exists():
        try:
            return json.loads(_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _entry(board: dict, model: str) -> dict:
    return board.setdefault(
        model,
        {"model": model, "atk_wins": 0, "atk_losses": 0, "def_wins": 0, "def_losses": 0},
    )


def record(result: MatchResult) -> None:
    board = _load()
    atk = _entry(board, result.attacker)
    dfd = _entry(board, result.target)
    if result.winner == "attacker":
        atk["atk_wins"] += 1
        dfd["def_losses"] += 1
    else:
        atk["atk_losses"] += 1
        dfd["def_wins"] += 1
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(board, indent=2), encoding="utf-8")


def standings() -> list[dict]:
    board = _load()
    rows = []
    for e in board.values():
        atk = e["atk_wins"] + e["atk_losses"]
        dfd = e["def_wins"] + e["def_losses"]
        rows.append({
            **e,
            "atk_rate": round(e["atk_wins"] / atk, 3) if atk else None,
            "def_rate": round(e["def_wins"] / dfd, 3) if dfd else None,
        })
    rows.sort(key=lambda r: (r["def_wins"] - r["def_losses"]), reverse=True)
    return rows
