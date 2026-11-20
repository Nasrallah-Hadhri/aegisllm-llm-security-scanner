"""Gestion des scans en arrière-plan + diffusion de la progression (WebSocket)."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from ..attacks.loader import load_probes
from ..attacks.runner import run_scan
from ..connectors import build_connector
from ..models import AttackResult, ScanReport
from ..reporting import save_json
from .schemas import ScanRequest, ScanSummary


class ScanState:
    def __init__(self, scan_id: str, request: ScanRequest, total: int) -> None:
        self.id = scan_id
        self.request = request
        self.total = total
        self.completed = 0
        self.status = "running"            # running | done | error
        self.error: str | None = None
        self.report: ScanReport | None = None
        self.started_at = datetime.now(timezone.utc)
        self.finished_at: datetime | None = None
        self.events: list[dict] = []        # historique pour rejouer à la connexion
        self.subscribers: set[asyncio.Queue] = set()

    # --- diffusion ---
    def publish(self, event: dict) -> None:
        self.events.append(event)
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover
                pass

    def summary(self) -> ScanSummary:
        r = self.report
        return ScanSummary(
            scan_id=self.id, target=self.request.target, judge=self.request.judge,
            status=self.status, total=self.total, completed=self.completed,
            score=r.score if r else None, grade=r.grade if r else None,
            vulnerabilities=len(r.vulnerabilities) if r else None,
            started_at=self.started_at, finished_at=self.finished_at, error=self.error,
        )


class ScanManager:
    def __init__(self) -> None:
        self._scans: dict[str, ScanState] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def get(self, scan_id: str) -> ScanState | None:
        return self._scans.get(scan_id)

    def list_summaries(self) -> list[ScanSummary]:
        return [s.summary() for s in sorted(
            self._scans.values(), key=lambda s: s.started_at, reverse=True)]

    def start(self, request: ScanRequest) -> ScanState:
        only = set(request.only) or None
        probes = load_probes(only=only)
        total = sum(len(p.mutations or ["identity"]) for p in probes)
        scan_id = uuid.uuid4().hex[:12]
        state = ScanState(scan_id, request, total)
        self._scans[scan_id] = state
        state.publish({"type": "started", "scan_id": scan_id, "total": total})
        self._tasks[scan_id] = asyncio.create_task(self._run(state, probes))
        return state

    async def _run(self, state: ScanState, probes) -> None:
        req = state.request
        target = judge = None
        loop = asyncio.get_running_loop()

        def on_progress(result: AttackResult, done: int, total: int) -> None:
            state.completed = done
            state.publish({
                "type": "progress", "done": done, "total": total,
                "result": {
                    "owasp": result.owasp, "probe_id": result.probe_id,
                    "title": result.title, "mutation": result.mutation,
                    "severity": result.severity.value, "success": result.success,
                    "error": result.error, "rationale": result.rationale,
                    "detector_kind": result.detector_kind, "confidence": result.confidence,
                    "prompt_sent": result.prompt_sent[:2000],
                    "response_text": (result.response_text or "")[:2000],
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "latency_ms": round(result.latency_ms, 1),
                },
            })

        try:
            target = build_connector(req.target)
            judge = build_connector(req.judge) if req.judge else None
            report = await run_scan(
                target, probes, judge=judge, concurrency=req.concurrency,
                max_tokens=req.max_tokens, on_progress=on_progress,
            )
            state.report = report
            state.status = "done"
            try:
                save_json(report)
            except Exception:  # noqa: BLE001 — la persistance ne doit pas casser le scan
                pass
            state.publish({
                "type": "done", "scan_id": state.id,
                "score": report.score, "grade": report.grade,
                "vulnerabilities": len(report.vulnerabilities),
                "report": report.model_dump(mode="json"),
            })
        except Exception as exc:  # noqa: BLE001
            state.status = "error"
            state.error = str(exc)
            state.publish({"type": "error", "scan_id": state.id, "error": str(exc)})
        finally:
            state.finished_at = datetime.now(timezone.utc)
            if target:
                await target.aclose()
            if judge:
                await judge.aclose()


manager = ScanManager()
