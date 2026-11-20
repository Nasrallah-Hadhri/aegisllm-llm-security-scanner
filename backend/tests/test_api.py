import httpx
import pytest
from fastapi.testclient import TestClient

from aegis.api.app import create_app
from aegis.config import OLLAMA_HOST


@pytest.fixture
def client():
    return TestClient(create_app())


def _ollama_up() -> bool:
    try:
        httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=2.0).raise_for_status()
        return True
    except Exception:
        return False


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_categories(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    assert "jailbreak" in r.json()


def test_unknown_scan_404(client):
    assert client.get("/api/scans/nope").status_code == 404


def test_scans_list_empty_ok(client):
    r = client.get("/api/scans")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.skipif(not _ollama_up(), reason="Ollama non disponible")
def test_live_scan_via_websocket(client):
    # LLM10 = 2 attaques rapides ; on suit la progression par WebSocket.
    resp = client.post("/api/scans", json={"target": "ollama:qwen2.5:7b", "only": ["LLM10"]})
    assert resp.status_code == 200
    scan_id = resp.json()["scan_id"]

    final = None
    with client.websocket_connect(f"/api/scans/{scan_id}/ws") as ws:
        for _ in range(200):
            event = ws.receive_json()
            if event["type"] in ("done", "error"):
                final = event
                break
    assert final and final["type"] == "done"
    assert "score" in final

    full = client.get(f"/api/scans/{scan_id}").json()
    assert full["report"]["score"] >= 0
