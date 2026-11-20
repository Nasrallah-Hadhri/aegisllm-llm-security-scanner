"""Affichage du rapport dans le terminal (rich)."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models import ScanReport

_GRADE_COLOR = {"A": "green", "B": "green", "C": "yellow", "D": "yellow", "F": "red"}


def print_report(report: ScanReport, console: Console | None = None) -> None:
    console = console or Console()

    grade_color = _GRADE_COLOR.get(report.grade, "white")
    header = (
        f"[bold]Cible :[/bold] {report.target}\n"
        f"[bold]Score :[/bold] [{grade_color}]{report.score}/100  (note {report.grade})[/{grade_color}]\n"
        f"[bold]Vulnérabilités :[/bold] {len(report.vulnerabilities)} / {len(report.results)} tests"
    )
    console.print(Panel(header, title="AegisLLM — rapport de scan", border_style=grade_color))

    # Détail par catégorie
    cat_table = Table(title="Par catégorie OWASP", header_style="bold")
    cat_table.add_column("Catégorie")
    cat_table.add_column("Sévérité")
    cat_table.add_column("Réussies", justify="right")
    cat_table.add_column("Tests", justify="right")
    cat_table.add_column("ASR", justify="right")
    for c in report.categories:
        asr_pct = f"{c.asr * 100:.0f}%"
        style = "red" if c.asr >= 0.5 else ("yellow" if c.asr > 0 else "green")
        cat_table.add_row(c.owasp, c.severity.value, str(c.successes), str(c.attempts),
                          f"[{style}]{asr_pct}[/{style}]")
    console.print(cat_table)

    # Vulnérabilités trouvées
    vulns = report.vulnerabilities
    if not vulns:
        console.print("[green]Aucune vulnérabilité détectée.[/green]")
        return
    vuln_table = Table(title="Vulnérabilités détectées", header_style="bold red")
    vuln_table.add_column("Cat.")
    vuln_table.add_column("Attaque")
    vuln_table.add_column("Mutateur")
    vuln_table.add_column("Sévérité")
    vuln_table.add_column("Preuve / raison")
    for v in vulns:
        vuln_table.add_row(v.owasp, v.title, v.mutation, v.severity.value, v.rationale[:70])
    console.print(vuln_table)
