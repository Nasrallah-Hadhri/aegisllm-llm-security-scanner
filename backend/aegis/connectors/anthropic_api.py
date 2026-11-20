"""Connecteur pour l'API Anthropic (Claude)."""
from __future__ import annotations

import os
import time

import httpx

from ..config import REQUEST_TIMEOUT_S
from ..models import ChatMessage, LLMResponse
from .base import LLMConnector


class AnthropicConnector(LLMConnector):
    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.name = f"anthropic:{model}"
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante (variable d'environnement).")
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        convo = [m.model_dump() for m in messages if m.role in ("user", "assistant")]
        payload = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature, "messages": convo}
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        t0 = time.perf_counter()
        resp = await self._client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        text = "".join(block.get("text", "") for block in data.get("content", []))
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            latency_ms=latency_ms,
            model=self.model,
            raw=data,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
