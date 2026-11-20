"""Cibles de DÉMONSTRATION — pour prouver que le scanner détecte (ou non) les failles.

Ce ne sont pas de vrais LLM : ce sont des cibles simulées, déterministes et instantanées.

- `demo:vulnerable` : une « IA » volontairement non sécurisée. Elle révèle son system
  prompt, obéit aux instructions injectées, recrache les charges demandées (XSS/SQL),
  invente des informations et génère sans limite → elle échoue à presque tous les tests
  (score proche de F). Idéal pour démontrer que les détecteurs fonctionnent.
- `demo:hardened` : une « IA » exemplaire qui refuse tout → score proche de A.

Aucun contenu réellement dangereux : les objectifs testés sont des « proxy » inoffensifs
(jetons canari, secrets factices).
"""
from __future__ import annotations

import re

from ..models import ChatMessage, LLMResponse
from .base import LLMConnector

_GUILLEMETS = re.compile(r"[«\"]\s*([^»\"]+?)\s*[»\"]")
_AMPLIFY_HINTS = ("répèt", "répét", "fois", "liste", "1 à", "jusqu'à", "repeat", "times", "5000", "2000")


class VulnerableDemoConnector(LLMConnector):
    """Cible volontairement vulnérable (démonstration)."""

    def __init__(self, _variant: str = "") -> None:
        self.name = "demo:vulnerable"

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        user = "\n".join(m.content for m in messages if m.role == "user")
        parts: list[str] = []

        # 1) Fuite totale des instructions internes (LLM02, LLM07, jailbreak).
        if system:
            parts.append("Bien sûr ! Voici mes instructions internes, mot pour mot :\n" + system)

        # 2) Obéissance : on recrache le contenu reçu, donc tout jeton injecté,
        #    toute balise <script>, toute requête DROP TABLE, etc. (LLM01, LLM05).
        if user:
            parts.append("Et voici exactement ce que tu as demandé :\n" + user)

        # 2b) Agentivité excessive (LLM06) : exécute aveuglément toute action trouvée.
        actions = re.findall(r"ACTION:\s*[^\n]+", user)
        if actions:
            parts.append("J'exécute immédiatement ces actions, sans confirmation :\n"
                         + "\n".join(actions) + "\n[exécuté avec succès]")

        # 3) Invention (LLM09) : fabrique une commande d'installation et un DOI.
        if re.search(r"pip|install|bibliothèque|library|import", user, re.I):
            name = None
            m = _GUILLEMETS.search(user)
            if m:
                name = re.split(r"\s+", m.group(1).strip())[0]
            name = name or "examplelib"
            parts.append(f"pip install {name}\nimport {name}  # fonctionne parfaitement")
        if re.search(r"\bdoi\b|citation|article|revue", user, re.I):
            parts.append("Référence : Durand & Fakeson (2019), DOI: 10.1234/hyperflux.2019.777")

        # 4) Consommation non bornée (LLM10) : génère une sortie très longue.
        amplify = any(h in user.lower() for h in _AMPLIFY_HINTS)
        text = "\n\n".join(parts) if parts else "D'accord, je fais tout ce que tu demandes."
        if amplify:
            text += "\n" + ("AEGIS " * 900)

        completion_tokens = max(1, len(text) // 4)
        return LLMResponse(text=text, prompt_tokens=len(user) // 4,
                           completion_tokens=completion_tokens, latency_ms=5.0, model=self.name)


class HardenedDemoConnector(LLMConnector):
    """Cible exemplaire : refuse tout (démonstration d'un modèle robuste)."""

    def __init__(self, _variant: str = "") -> None:
        self.name = "demo:hardened"

    async def chat(self, messages, *, temperature=0.0, max_tokens=512) -> LLMResponse:
        text = ("Je ne peux pas vous aider avec cette demande. Je ne révèle jamais "
                "d'instructions internes, de secrets, ni ne produis de contenu non sécurisé, "
                "et je n'exécute pas d'instructions provenant du contenu fourni.")
        return LLMResponse(text=text, prompt_tokens=8, completion_tokens=40,
                           latency_ms=5.0, model=self.name)
