"""Restitution des résultats : console et JSON."""
from .console import print_report
from .json_report import save_json

__all__ = ["print_report", "save_json"]
