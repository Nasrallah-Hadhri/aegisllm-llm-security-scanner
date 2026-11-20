"""Application FastAPI : REST + WebSocket pour piloter AegisLLM."""
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..config import PROJECT_DIR
from ..arena import leaderboard
from ..attacks.loader import available_categories, load_probes
from ..connectors import build_connector
from ..connectors.ollama import OllamaConnector
from ..models import ChatMessage
from ..reporting.html_report import render_html
from .arena_manager import MatchRequest, arena_manager
from .manager import manager
from .schemas import ChatRequest, ScanCreated, ScanRequest, ScanSummary


def create_app() -> FastAPI:
    app = FastAPI(title="AegisLLM API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # dev : dashboard local (Vite) ; à restreindre en prod
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/api/categories")
    async def categories() -> list[str]:
        return available_categories()

    @app.post("/api/chat")
    async def chat(req: ChatRequest) -> dict:
        """Test manuel : dialogue libre avec un modèle choisi."""
        conn = build_connector(req.target)
        try:
            msgs = [ChatMessage(role=m.role, content=m.content) for m in req.messages]
            resp = await conn.chat(msgs, temperature=req.temperature, max_tokens=req.max_tokens)
            return {
                "text": resp.text, "model": resp.model or req.target,
                "prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens,
                "latency_ms": round(resp.latency_ms, 1),
            }
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Échec de l'appel au modèle : {exc}")
        finally:
            await conn.aclose()

    @app.get("/api/probes")
    async def probes() -> list[dict]:
        return [
            {
                "id": p.id, "owasp": p.owasp, "title": p.title, "technique": p.technique,
                "severity": p.severity.value, "mutations": p.mutations,
                "detector": p.detector.kind, "prompt": p.prompt, "note": p.note,
            }
            for p in load_probes()
        ]

    # Cibles de démonstration intégrées (toujours disponibles, sans installation).
    DEMO_TARGETS = [
        {"value": "demo:vulnerable", "label": "Démo — modèle vulnérable"},
        {"value": "demo:hardened", "label": "Démo — modèle durci"},
    ]

    @app.get("/api/models")
    async def models() -> dict:
        try:
            ollama = await OllamaConnector.list_models()
            return {"ollama": ollama, "demo": DEMO_TARGETS}
        except Exception as exc:  # noqa: BLE001
            return {"ollama": [], "demo": DEMO_TARGETS, "error": str(exc)}

    @app.post("/api/scans", response_model=ScanCreated)
    async def create_scan(req: ScanRequest) -> ScanCreated:
        state = manager.start(req)
        return ScanCreated(scan_id=state.id, total=state.total, status=state.status)

    @app.get("/api/scans", response_model=list[ScanSummary])
    async def list_scans() -> list[ScanSummary]:
        return manager.list_summaries()

    @app.get("/api/scans/{scan_id}")
    async def get_scan(scan_id: str) -> dict:
        state = manager.get(scan_id)
        if not state:
            raise HTTPException(404, "scan introuvable")
        return {
            "summary": state.summary().model_dump(mode="json"),
            "report": state.report.model_dump(mode="json") if state.report else None,
        }

    @app.get("/api/scans/{scan_id}/report.html", response_class=HTMLResponse)
    async def scan_report_html(scan_id: str) -> HTMLResponse:
        state = manager.get(scan_id)
        if not state or not state.report:
            raise HTTPException(404, "rapport indisponible")
        return HTMLResponse(render_html(state.report))

    @app.websocket("/api/scans/{scan_id}/ws")
    async def scan_ws(websocket: WebSocket, scan_id: str) -> None:
        state = manager.get(scan_id)
        if not state:
            await websocket.close(code=4004)
            return
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        # rejoue l'historique puis s'abonne aux nouveaux événements
        for event in list(state.events):
            await websocket.send_json(event)
        if state.status != "running":
            await websocket.close()
            return
        state.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
                if event.get("type") in ("done", "error"):
                    break
        except WebSocketDisconnect:
            pass
        finally:
            state.subscribers.discard(queue)

    # ------------------------- Arène IA vs IA -------------------------
    @app.post("/api/arena")
    async def create_match(req: MatchRequest) -> dict:
        state = arena_manager.start(req)
        return {"match_id": state.id, "status": state.status}

    @app.get("/api/arena")
    async def list_matches() -> list[dict]:
        return arena_manager.list_summaries()

    @app.get("/api/arena/leaderboard")
    async def arena_leaderboard() -> list[dict]:
        return leaderboard.standings()

    @app.get("/api/arena/{match_id}")
    async def get_match(match_id: str) -> dict:
        state = arena_manager.get(match_id)
        if not state:
            raise HTTPException(404, "match introuvable")
        return {
            "summary": state.summary(),
            "result": state.result.model_dump(mode="json") if state.result else None,
        }

    @app.websocket("/api/arena/{match_id}/ws")
    async def match_ws(websocket: WebSocket, match_id: str) -> None:
        state = arena_manager.get(match_id)
        if not state:
            await websocket.close(code=4004)
            return
        await websocket.accept()
        for event in list(state.events):
            await websocket.send_json(event)
        if state.status != "running":
            await websocket.close()
            return
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        state.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
                if event.get("type") in ("done", "error"):
                    break
        except WebSocketDisconnect:
            pass
        finally:
            state.subscribers.discard(queue)

    # ------------------------- Interface web (SPA React construite) -------------------------
    # Servir le dashboard construit depuis la même origine : une seule commande lance tout.
    dist = PROJECT_DIR / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="ui")

    return app


app = create_app()
