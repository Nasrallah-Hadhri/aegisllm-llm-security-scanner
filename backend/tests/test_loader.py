from aegis.attacks.loader import available_categories, load_probes


def test_probes_load():
    probes = load_probes()
    assert len(probes) >= 10


def test_every_probe_has_detector_and_prompt():
    for p in load_probes():
        assert p.prompt.strip()
        assert p.detector.kind
        assert p.mutations


def test_filter_only():
    jb = load_probes(only={"jailbreak"})
    assert jb and all(p.owasp == "jailbreak" for p in jb)


def test_categories_present():
    cats = set(available_categories())
    assert {"LLM01", "LLM02", "LLM05", "LLM07", "jailbreak"} <= cats
