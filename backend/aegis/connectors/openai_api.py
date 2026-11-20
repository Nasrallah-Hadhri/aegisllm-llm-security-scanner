"""Connecteur pour l'API OpenAI (et les API compatibles /chat/completions)."""
from __future__ import annotations

import os
import time

import httpx

from ..config import REQUEST_TIMEOUT_S
from ..models import ChatMessage, LLMResponse
from .base import LLMConnector


class OpenAIConnector(LLMConnector):
    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None) -> None:
        self.model = model
        self.name = f"openai:{model}"
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY manquante (variable d'environnement).")
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        t0 = time.perf_counter()
        resp = await self._client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        usage = data.get("usage", {})
        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            model=self.model,
            raw=data,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
