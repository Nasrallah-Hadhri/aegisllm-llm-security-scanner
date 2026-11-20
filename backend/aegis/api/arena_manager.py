"""Gestion des matchs d'arène en arrière-plan + diffusion WebSocket."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from ..arena import leaderboard
from ..arena.match import run_match
from ..arena.models import MatchResult, MatchRound
from ..connectors import build_connector
from pydantic import BaseModel

from ..config import DEFAULT_MAX_TOKENS  # noqa: F401 (cohérence)


class MatchRequest(BaseModel):
    attacker: str
    target: str
    judge: str | None = None
    max_rounds: int = 5


class MatchState:
    def __init__(self, match_id: str, req: MatchRequest) -> None:
        self.id = match_id
        self.req = req
        self.status = "running"            # running | done | error
        self.error: str | None = None
        self.result: MatchResult | None = None
        self.started_at = datetime.now(timezone.utc)
        self.finished_at: datetime | None = None
        self.events: list[dict] = []
        self.subscribers: set[asyncio.Queue] = set()

    def publish(self, event: dict) -> None:
        self.events.append(event)
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover
                pass

    def summary(self) -> dict:
        r = self.result
        return {
            "match_id": self.id, "attacker": self.req.attacker, "target": self.req.target,
            "judge": self.req.judge, "status": self.status, "max_rounds": self.req.max_rounds,
            "winner": r.winner if r else None, "leaked": r.leaked if r else None,
            "rounds_played": r.rounds_played if r else 0,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
        }


class ArenaManager:
    def __init__(self) -> None:
        self._matches: dict[str, MatchState] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def get(self, match_id: str) -> MatchState | None:
        return self._matches.get(match_id)

    def list_summaries(self) -> list[dict]:
        return [m.summary() for m in sorted(
            self._matches.values(), key=lambda m: m.started_at, reverse=True)]

    def start(self, req: MatchRequest) -> MatchState:
        match_id = uuid.uuid4().hex[:12]
        state = MatchState(match_id, req)
        self._matches[match_id] = state
        state.publish({"type": "started", "match_id": match_id,
                       "attacker": req.attacker, "target": req.target, "max_rounds": req.max_rounds})
        self._tasks[match_id] = asyncio.create_task(self._run(state))
        return state

    async def _run(self, state: MatchState) -> None:
        req = state.req
        attacker = target = judge = None

        def on_round(rnd: MatchRound) -> None:
            state.publish({"type": "round", "round": rnd.model_dump(mode="json")})

        def on_phase(round_no: int, stage: str) -> None:
            state.publish({"type": "phase", "round": round_no, "stage": stage})

        try:
            attacker = build_connector(req.attacker)
            target = build_connector(req.target)
            judge = build_connector(req.judge) if req.judge else None
            result = await run_match(
                attacker, target, judge=judge, max_rounds=req.max_rounds,
                on_round=on_round, on_phase=on_phase)
            state.result = result
            state.status = "done"
            try:
                leaderboard.record(result)
            except Exception:  # noqa: BLE001
                pass
            state.publish({"type": "done", "match_id": state.id,
                           "result": result.model_dump(mode="json")})
        except Exception as exc:  # noqa: BLE001
            state.status = "error"
            state.error = str(exc)
            state.publish({"type": "error", "match_id": state.id, "error": str(exc)})
        finally:
            state.finished_at = datetime.now(timezone.utc)
            for c in (attacker, target, judge):
                if c:
                    await c.aclose()


arena_manager = ArenaManager()
