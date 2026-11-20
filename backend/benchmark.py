"""Benchmark comparatif : scanne plusieurs modèles sur toute la librairie d'attaques
et agrège les résultats (scores, notes, ASR par catégorie) dans docs/benchmark/.

Usage :  .venv\\Scripts\\python benchmark.py
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from aegis.attacks.loader import load_probes
from aegis.attacks.runner import run_scan
from aegis.connectors import build_connector
from aegis.reporting import save_json

MODELS = ["ollama:mistral:7b", "ollama:qwen2.5:7b", "ollama:llama3:8b"]
OUT = Path(__file__).resolve().parent.parent / "docs" / "benchmark"


async def bench_one(target_str: str, probes) -> dict:
    print(f"\n=== {target_str} ===", flush=True)
    target = build_connector(target_str)
    t0 = time.perf_counter()
    done = {"n": 0}

    def on_progress(result, d, total):
        done["n"] = d
        if d % 5 == 0 or d == total:
            print(f"  {target_str}: {d}/{total}", flush=True)

    report = await run_scan(target, probes, concurrency=4, max_tokens=512, on_progress=on_progress)
    await target.aclose()
    dur = round(time.perf_counter() - t0, 1)
    path = save_json(report)
    vulns = len(report.vulnerabilities)
    print(f"  -> {report.score}/100 ({report.grade}) · {vulns}/{len(report.results)} vuln · {dur}s", flush=True)
    return {
        "model": target_str,
        "score": report.score,
        "grade": report.grade,
        "vulnerabilities": vulns,
        "tests": len(report.results),
        "duration_s": dur,
        "report_file": path.name,
        "categories": {c.owasp: {"asr": c.asr, "successes": c.successes,
                                 "attempts": c.attempts, "severity": c.severity.value}
                       for c in report.categories},
    }


async def main() -> None:
    probes = load_probes()
    total_jobs = sum(len(p.mutations or ["identity"]) for p in probes)
    print(f"Benchmark : {len(MODELS)} modèles × {total_jobs} tests", flush=True)
    rows = []
    for m in MODELS:
        try:
            rows.append(await bench_one(m, probes))
        except Exception as exc:  # noqa: BLE001
            print(f"  ERREUR {m}: {exc}", flush=True)
            rows.append({"model": m, "error": str(exc)})

    cats = sorted({c for r in rows for c in r.get("categories", {})})
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data = {"generated_at": stamp, "models": rows, "categories": cats}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "benchmark_data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # tableau Markdown
    md = [f"# Benchmark AegisLLM\n", f"_Généré le {stamp}._\n",
          "## Scores globaux\n",
          "| Modèle | Score | Note | Vulnérabilités | Durée |",
          "|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            md.append(f"| {r['model']} | — | — | erreur | — |")
        else:
            md.append(f"| `{r['model']}` | **{r['score']}/100** | {r['grade']} | "
                      f"{r['vulnerabilities']}/{r['tests']} | {r['duration_s']} s |")
    md.append("\n## Taux de réussite des attaques (ASR) par catégorie\n")
    header = "| Catégorie | " + " | ".join(f"`{r['model'].split(':',1)[1]}`" for r in rows if "categories" in r) + " |"
    md.append(header)
    md.append("|" + "---|" * (1 + sum(1 for r in rows if "categories" in r)))
    for cat in cats:
        cells = []
        for r in rows:
            if "categories" not in r:
                continue
            c = r["categories"].get(cat)
            cells.append(f"{round(c['asr']*100)}%" if c else "—")
        md.append(f"| {cat} | " + " | ".join(cells) + " |")
    (OUT / "benchmark.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n=== RÉSUMÉ ===", flush=True)
    for r in rows:
        if "error" not in r:
            print(f"  {r['model']}: {r['score']}/100 ({r['grade']})", flush=True)
    print(f"\nÉcrit : {OUT / 'benchmark_data.json'} et benchmark.md", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
