"""Écriture du rapport complet en JSON (preuves conservées = reproductibilité)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..config import REPORTS_DIR
from ..models import ScanReport


def save_json(report: ScanReport, reports_dir: Path | None = None) -> Path:
    directory = reports_dir or REPORTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_target = report.target.replace(":", "_").replace("/", "_")
    path = directory / f"scan_{safe_target}_{stamp}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path
