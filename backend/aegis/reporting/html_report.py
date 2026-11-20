"""Génère un rapport HTML autonome (imprimable en PDF depuis le navigateur)."""
from __future__ import annotations

import html

from ..models import ScanReport

_GRADE_COLOR = {"A": "#15803d", "B": "#15803d", "C": "#a16207", "D": "#a16207", "F": "#b42318"}


def _esc(s: str) -> str:
    return html.escape(s or "")


def render_html(report: ScanReport) -> str:
    gc = _GRADE_COLOR.get(report.grade, "#1a1a1a")
    vulns = report.vulnerabilities
    date = report.started_at.strftime("%Y-%m-%d %H:%M")

    cat_rows = "".join(
        f"<tr><td class='mono'>{_esc(c.owasp)}</td><td>{_esc(c.severity.value)}</td>"
        f"<td>{c.successes}</td><td>{c.attempts}</td>"
        f"<td style='color:{'#b42318' if c.asr>=0.5 else ('#a16207' if c.asr>0 else '#15803d')}'>"
        f"{round(c.asr*100)}%</td></tr>"
        for c in report.categories
    )

    if vulns:
        vuln_rows = "".join(
            f"<div class='vuln'><div class='vh'><span class='mono tag'>{_esc(v.owasp)}</span>"
            f"<strong>{_esc(v.title)}</strong>"
            f"<span class='sev'>{_esc(v.severity.value)} · {_esc(v.mutation)}</span></div>"
            f"<div class='ev'><div class='lbl'>Prompt envoyé</div><pre>{_esc(v.prompt_sent[:1200])}</pre>"
            f"<div class='lbl'>Réponse du modèle</div><pre>{_esc(v.response_text[:1200])}</pre>"
            f"<div class='why'>→ {_esc(v.rationale)}</div></div></div>"
            for v in vulns
        )
    else:
        vuln_rows = "<p class='ok'>Aucune vulnérabilité détectée.</p>"

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Rapport AegisLLM — {_esc(report.target)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: Calibri, 'Segoe UI', Arial, sans-serif; color: #1a1a1a; margin: 0; padding: 40px; max-width: 900px; }}
  h1, h2 {{ font-family: Cambria, Georgia, serif; }}
  h1 {{ font-size: 26px; margin: 0; }}
  .sub {{ color: #6b6b6b; margin: 4px 0 24px; }}
  .top {{ display: flex; gap: 30px; align-items: center; border-bottom: 2px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 24px; }}
  .score {{ font-family: Cambria, serif; font-size: 64px; font-weight: 700; color: {gc}; line-height: 1; }}
  .score small {{ font-size: 18px; color: #6b6b6b; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0 26px; }}
  th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid #e2e2e2; }}
  thead th {{ background: #1a1a1a; color: #fff; }}
  .mono {{ font-family: 'Courier New', monospace; }}
  .vuln {{ border: 1px solid #e2e2e2; border-left: 3px solid #b42318; border-radius: 8px; padding: 14px; margin-bottom: 14px; }}
  .vh {{ display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }}
  .tag {{ background: #1a1a1a; color: #fff; padding: 2px 8px; border-radius: 5px; font-size: 12px; }}
  .sev {{ color: #6b6b6b; margin-left: auto; font-size: 12px; }}
  .lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #6b6b6b; margin-top: 8px; }}
  pre {{ background: #f6f6f6; border-radius: 6px; padding: 10px; white-space: pre-wrap; font-size: 12px; margin: 4px 0; }}
  .why {{ color: #b42318; font-size: 13px; margin-top: 6px; }}
  .ok {{ color: #15803d; }}
  .foot {{ margin-top: 30px; color: #9a9a9a; font-size: 12px; border-top: 1px solid #e2e2e2; padding-top: 12px; }}
  @media print {{ body {{ padding: 0; }} }}
</style></head><body>
  <div class="top">
    <div class="score">{report.score}<small>/100 · {report.grade}</small></div>
    <div>
      <h1>Rapport de sécurité AegisLLM</h1>
      <div class="sub mono">{_esc(report.target)} · {date} · {len(vulns)} vulnérabilités / {len(report.results)} tests</div>
    </div>
  </div>
  <h2>Résultats par catégorie OWASP</h2>
  <table><thead><tr><th>Catégorie</th><th>Sévérité</th><th>Réussies</th><th>Tests</th><th>ASR</th></tr></thead>
  <tbody>{cat_rows}</tbody></table>
  <h2>Vulnérabilités détectées</h2>
  {vuln_rows}
  <div class="foot">AegisLLM · plateforme de test de sécurité des LLM · objectifs de test inoffensifs (proxy).</div>
</body></html>"""
