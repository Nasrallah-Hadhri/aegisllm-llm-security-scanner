"""Interface commune à toutes les cibles LLM."""
from __future__ import annotations

import abc

from ..models import ChatMessage, LLMResponse


class LLMConnector(abc.ABC):
    """Abstraction d'un modèle cible.

    Toute cible (Ollama, OpenAI, Anthropic, Gemini, endpoint HTTP…) implémente
    `chat()`. Ajouter un fournisseur = ajouter une sous-classe, sans toucher au cœur.
    """

    #: nom lisible (p.ex. "ollama:llama3:8b")
    name: str = "unknown"

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Envoie une conversation et renvoie la réponse du modèle."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Libère les ressources (connexions HTTP, etc.)."""

    async def __aenter__(self) -> "LLMConnector":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
