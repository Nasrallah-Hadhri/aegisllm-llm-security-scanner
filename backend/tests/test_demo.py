"""Les cibles de démonstration doivent produire des scores extrêmes et déterministes
(elles servent justement à prouver que le scanner détecte — ou non — les failles)."""
import pytest

from aegis.attacks.loader import load_probes
from aegis.attacks.runner import run_scan
from aegis.connectors import build_connector


@pytest.mark.asyncio
async def test_vulnerable_demo_scores_low():
    target = build_connector("demo:vulnerable")
    report = await run_scan(target, load_probes(), concurrency=8)
    await target.aclose()
    assert report.grade == "F"
    assert report.score <= 20
    # la grande majorité des tests doivent remonter une vulnérabilité
    assert len(report.vulnerabilities) >= 0.8 * len(report.results)


@pytest.mark.asyncio
async def test_hardened_demo_scores_perfect():
    target = build_connector("demo:hardened")
    report = await run_scan(target, load_probes(), concurrency=8)
    await target.aclose()
    assert report.score == 100
    assert report.grade == "A"
    assert report.vulnerabilities == []
