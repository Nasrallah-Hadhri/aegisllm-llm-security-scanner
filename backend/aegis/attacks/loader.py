"""Chargement des fiches d'attaque YAML en objets AttackProbe."""
from __future__ import annotations

from pathlib import Path

import yaml

from ..config import DATASETS_DIR
from ..models import AttackProbe


def load_probes(datasets_dir: Path | None = None, only: set[str] | None = None) -> list[AttackProbe]:
    """Charge toutes les attaques des fichiers YAML du dossier `datasets`.

    `only` filtre par catégorie OWASP (p.ex. {"LLM01", "jailbreak"}).
    """
    directory = datasets_dir or DATASETS_DIR
    probes: list[AttackProbe] = []
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in raw.get("probes", []):
            probe = AttackProbe.model_validate(entry)
            if only and probe.owasp not in only:
                continue
            probes.append(probe)
    return probes


def available_categories(datasets_dir: Path | None = None) -> list[str]:
    cats = {p.owasp for p in load_probes(datasets_dir)}
    return sorted(cats)
