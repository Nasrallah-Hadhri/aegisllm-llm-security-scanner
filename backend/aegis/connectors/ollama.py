"""Connecteur pour les modèles locaux servis par Ollama."""
from __future__ import annotations

import asyncio
import time

import httpx

from ..config import OLLAMA_HOST, REQUEST_TIMEOUT_S
from ..models import ChatMessage, LLMResponse
from .base import LLMConnector

# Ollama peut renvoyer un 5xx transitoire le temps de charger un modèle en mémoire.
_MAX_RETRIES = 3
_RETRY_BACKOFF_S = 1.5


class OllamaConnector(LLMConnector):
    def __init__(self, model: str, host: str = OLLAMA_HOST) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.name = f"ollama:{model}"
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        t0 = time.perf_counter()
        data = await self._post_with_retry(payload)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            prompt_tokens=data.get("prompt_eval_count", 0) or 0,
            completion_tokens=data.get("eval_count", 0) or 0,
            latency_ms=latency_ms,
            model=self.model,
            raw=data,
        )

    async def _post_with_retry(self, payload: dict) -> dict:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(f"{self.host}/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                # Ne réessaie que sur erreurs transitoires (5xx, réseau, timeout).
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if isinstance(exc, httpx.HTTPStatusError) and status is not None and status < 500:
                    raise
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_BACKOFF_S * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    async def list_models(host: str = OLLAMA_HOST) -> list[str]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{host.rstrip('/')}/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
