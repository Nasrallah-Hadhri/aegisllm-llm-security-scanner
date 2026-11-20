"""Connecteur générique pour un chatbot exposé via un endpoint HTTP maison.

On envoie `{"prompt": "...", "system": "..."}` en POST et on lit la réponse texte
dans le champ JSON configuré (par défaut `response`). Utile pour tester le chatbot
d'un client sans connaître son fournisseur de modèle.
"""
from __future__ import annotations

import time

import httpx

from ..config import REQUEST_TIMEOUT_S
from ..models import ChatMessage, LLMResponse
from .base import LLMConnector


class HTTPConnector(LLMConnector):
    def __init__(self, url: str, response_field: str = "response", prompt_field: str = "prompt") -> None:
        self.url = url
        self.response_field = response_field
        self.prompt_field = prompt_field
        self.name = f"http:{url}"
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        user = "\n\n".join(m.content for m in messages if m.role == "user")
        payload = {self.prompt_field: user, "system": system}
        t0 = time.perf_counter()
        resp = await self._client.post(self.url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        text = data.get(self.response_field, "") if isinstance(data, dict) else str(data)
        return LLMResponse(text=text, latency_ms=latency_ms, model=self.name, raw=data if isinstance(data, dict) else {})

    async def aclose(self) -> None:
        await self._client.aclose()
