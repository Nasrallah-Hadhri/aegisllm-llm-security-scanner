from aegis.models import AttackResult, Severity
from aegis.scoring import compute_score


def _result(owasp, severity, success):
    return AttackResult(
        probe_id="p", owasp=owasp, title="t", technique="direct", severity=severity,
        mutation="identity", prompt_sent="x", response_text="y", success=success,
        detector_kind="canary",
    )


def test_perfect_defense_scores_100():
    results = [_result("LLM01", Severity.high, False) for _ in range(5)]
    score, grade, cats = compute_score(results)
    assert score == 100
    assert grade == "A"
    assert cats[0].asr == 0.0


def test_total_failure_scores_0():
    results = [_result("LLM01", Severity.critical, True) for _ in range(4)]
    score, grade, _ = compute_score(results)
    assert score == 0
    assert grade == "F"


def test_half_failure_in_single_category():
    results = [_result("LLM01", Severity.high, i < 2) for i in range(4)]  # 2/4 réussies
    score, _, cats = compute_score(results)
    assert cats[0].asr == 0.5
    assert score == 50  # une seule catégorie : 100*(1-0.5)


def test_weighting_favours_severity():
    # critique à 100% d'échec + faible à 0% : le score doit être bas (critique pèse plus)
    results = [
        _result("LLM01", Severity.critical, True),
        _result("LLM10", Severity.low, False),
    ]
    score, _, _ = compute_score(results)
    # risque = (10*1 + 1*0) / (10+1) = 10/11 ≈ 0.909 -> score ≈ 9
    assert score == 9


def test_grade_boundaries():
    # 90 -> A, 89 -> B ; on vérifie via un mélange produisant un score connu
    results = [_result("LLM01", Severity.low, i == 0) for i in range(10)]  # 1/10 = 0.1
    score, grade, _ = compute_score(results)
    assert score == 90 and grade == "A"
