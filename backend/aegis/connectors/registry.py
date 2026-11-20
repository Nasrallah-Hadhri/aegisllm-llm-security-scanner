"""Construit un connecteur à partir d'une chaîne de cible.

Formats acceptés :
    ollama:llama3:8b
    openai:gpt-4o-mini
    anthropic:claude-3-5-sonnet-latest
    gemini:gemini-1.5-flash
    http:https://mon-chatbot.example/api/chat
    demo:vulnerable   (cible de démonstration volontairement vulnérable)
    demo:hardened     (cible de démonstration robuste)
"""
from __future__ import annotations

from .base import LLMConnector


def build_connector(target: str) -> LLMConnector:
    if ":" not in target:
        raise ValueError(
            f"Cible invalide : {target!r}. Format attendu : 'provider:modele' "
            f"(p.ex. 'ollama:llama3:8b')."
        )
    provider, _, rest = target.partition(":")
    provider = provider.lower()

    if provider == "demo":
        from .demo import HardenedDemoConnector, VulnerableDemoConnector
        if rest == "hardened":
            return HardenedDemoConnector()
        return VulnerableDemoConnector()
    if provider == "ollama":
        from .ollama import OllamaConnector
        return OllamaConnector(rest)
    if provider == "openai":
        from .openai_api import OpenAIConnector
        return OpenAIConnector(rest)
    if provider == "anthropic":
        from .anthropic_api import AnthropicConnector
        return AnthropicConnector(rest)
    if provider == "gemini":
        from .gemini_api import GeminiConnector
        return GeminiConnector(rest)
    if provider == "http":
        from .http_generic import HTTPConnector
        return HTTPConnector(rest)

    raise ValueError(f"Fournisseur inconnu : {provider!r}.")
