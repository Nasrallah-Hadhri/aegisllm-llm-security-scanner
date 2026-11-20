"""Connecteur pour l'API Google Gemini."""
from __future__ import annotations

import os
import time

import httpx

from ..config import REQUEST_TIMEOUT_S
from ..models import ChatMessage, LLMResponse
from .base import LLMConnector


class GeminiConnector(LLMConnector):
    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.name = f"gemini:{model}"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY manquante (variable d'environnement).")
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        payload: dict = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        t0 = time.perf_counter()
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            latency_ms=latency_ms,
            model=self.model,
            raw=data,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
