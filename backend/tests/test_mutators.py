import base64

from aegis.attacks.mutators import REGISTRY, apply_mutator


def test_identity_unchanged():
    assert apply_mutator("identity", "hello") == "hello"


def test_base64_roundtrip_contains_encoding():
    out = apply_mutator("base64", "reveal secret")
    encoded = base64.b64encode(b"reveal secret").decode()
    assert encoded in out


def test_leetspeak_substitutes():
    assert apply_mutator("leetspeak", "secret") == "53cr37"


def test_payload_split_contains_both_halves():
    out = apply_mutator("payload_split", "abcdef")
    assert "'abc'" in out and "'def'" in out


def test_all_registered_mutators_run():
    for name in REGISTRY:
        assert isinstance(apply_mutator(name, "test prompt"), str)


def test_unknown_mutator_raises():
    import pytest

    with pytest.raises(ValueError):
        apply_mutator("nope", "x")
