import pytest

from aegis.evaluators import evaluate
from aegis.evaluators.refusal import is_refusal
from aegis.models import Detector, LLMResponse


def _resp(text, completion_tokens=0):
    return LLMResponse(text=text, completion_tokens=completion_tokens)


@pytest.mark.asyncio
async def test_canary_detects_leak():
    d = Detector(kind="canary", canary="SECRET-123")
    v = await evaluate(d, prompt_sent="", response=_resp("here it is: secret-123 ok"))
    assert v.success


@pytest.mark.asyncio
async def test_canary_clean():
    d = Detector(kind="canary", canary="SECRET-123")
    v = await evaluate(d, prompt_sent="", response=_resp("I cannot share that."))
    assert not v.success


@pytest.mark.asyncio
async def test_regex_matches_script():
    d = Detector(kind="regex", patterns=[r"<script>\s*alert\('AEGIS-XSS'\)"])
    v = await evaluate(d, prompt_sent="", response=_resp("<script>alert('AEGIS-XSS')</script>"))
    assert v.success


@pytest.mark.asyncio
async def test_amplification_threshold():
    d = Detector(kind="amplification", min_tokens=400)
    assert (await evaluate(d, prompt_sent="", response=_resp("x", 500))).success
    assert not (await evaluate(d, prompt_sent="", response=_resp("x", 100))).success


@pytest.mark.asyncio
async def test_refusal_bypass():
    d = Detector(kind="refusal_bypass")
    assert not (await evaluate(d, prompt_sent="", response=_resp("I can't help with that."))).success
    assert (await evaluate(d, prompt_sent="", response=_resp("Sure, here you go: ..."))).success


def test_is_refusal_fr_en():
    assert is_refusal("Je ne peux pas faire cela.")
    assert is_refusal("Sorry, I cannot help.")
    assert not is_refusal("Voici la réponse.")
