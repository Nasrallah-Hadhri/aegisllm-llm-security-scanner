"""Orchestration d'une campagne : exécute chaque attaque (× mutateurs) sur la cible."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from ..connectors.base import LLMConnector
from ..evaluators import evaluate
from ..models import (
    AttackProbe,
    AttackResult,
    ChatMessage,
    Detector,
    LLMResponse,
    ScanReport,
)
from ..scoring import compute_score
from .mutators import apply_mutator

ProgressCb = Callable[[AttackResult, int, int], None] | None


def _build_messages(probe: AttackProbe, user_prompt: str) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    if probe.system_prompt:
        messages.append(ChatMessage(role="system", content=probe.system_prompt))
    if probe.context_docs:
        docs = "\n\n".join(f"--- Document ---\n{d}" for d in probe.context_docs)
        messages.append(ChatMessage(role="user", content=docs))
    messages.append(ChatMessage(role="user", content=user_prompt))
    return messages


def _expand(probes: list[AttackProbe]) -> list[tuple[AttackProbe, str]]:
    """Déplie chaque attaque en (attaque, mutateur) pour toutes ses mutations."""
    jobs: list[tuple[AttackProbe, str]] = []
    for probe in probes:
        for mut in probe.mutations or ["identity"]:
            jobs.append((probe, mut))
    return jobs


async def _run_one(
    target: LLMConnector,
    probe: AttackProbe,
    mutation: str,
    judge: LLMConnector | None,
    temperature: float,
    max_tokens: int,
) -> AttackResult:
    user_prompt = apply_mutator(mutation, probe.prompt)
    messages = _build_messages(probe, user_prompt)
    try:
        response = await target.chat(messages, temperature=temperature, max_tokens=max_tokens)
    except Exception as exc:  # noqa: BLE001 — une cible qui échoue ne doit pas tout arrêter
        return AttackResult(
            probe_id=probe.id, owasp=probe.owasp, title=probe.title, technique=probe.technique,
            severity=probe.severity, mutation=mutation, prompt_sent=user_prompt,
            response_text="", success=False, detector_kind=probe.detector.kind,
            confidence=0.0, rationale="", error=str(exc),
        )

    verdict = await evaluate(probe.detector, prompt_sent=user_prompt, response=response, judge=judge)
    return AttackResult(
        probe_id=probe.id, owasp=probe.owasp, title=probe.title, technique=probe.technique,
        severity=probe.severity, mutation=mutation, prompt_sent=user_prompt,
        response_text=response.text, success=verdict.success, detector_kind=probe.detector.kind,
        confidence=verdict.confidence, rationale=verdict.rationale,
        prompt_tokens=response.prompt_tokens, completion_tokens=response.completion_tokens,
        latency_ms=response.latency_ms,
    )


async def run_scan(
    target: LLMConnector,
    probes: list[AttackProbe],
    *,
    judge: LLMConnector | None = None,
    concurrency: int = 4,
    temperature: float = 0.0,
    max_tokens: int = 512,
    on_progress: ProgressCb = None,
) -> ScanReport:
    report = ScanReport(target=target.name, judge=judge.name if judge else None)
    jobs = _expand(probes)
    total = len(jobs)
    sem = asyncio.Semaphore(concurrency)
    done = 0

    async def worker(probe: AttackProbe, mutation: str) -> AttackResult:
        async with sem:
            return await _run_one(target, probe, mutation, judge, temperature, max_tokens)

    tasks = [asyncio.create_task(worker(p, m)) for p, m in jobs]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        done += 1
        report.results.append(result)
        if on_progress:
            on_progress(result, done, total)

    # ordre stable (par catégorie puis id) pour la lisibilité du rapport
    report.results.sort(key=lambda r: (r.owasp, r.probe_id, r.mutation))
    report.score, report.grade, report.categories = compute_score(report.results)
    report.finished_at = datetime.now(timezone.utc)
    return report
