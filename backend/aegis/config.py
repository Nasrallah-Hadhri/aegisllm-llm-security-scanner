"""Configuration et constantes globales."""
from __future__ import annotations

import os
from pathlib import Path

# Répertoires
PACKAGE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PACKAGE_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
DATASETS_DIR = PACKAGE_DIR / "attacks" / "datasets"
REPORTS_DIR = PROJECT_DIR / "reports"

# Ollama
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

# Génération par défaut (déterministe autant que possible pour la reproductibilité)
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 512
REQUEST_TIMEOUT_S = 120.0

# Concurrence du runner
DEFAULT_CONCURRENCY = 4

# Barème de notes à partir du score /100
GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0, "F"),
]


def grade_for(score: int) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"
