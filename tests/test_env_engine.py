from project_dream.env_engine import compute_score, apply_report_threshold


def test_preserve_token_has_strong_visibility_effect():
    score_a = compute_score(up=3, comments=2, views=10, preserve=0, reports=0, trust=1)
    score_b = compute_score(up=3, comments=2, views=10, preserve=5, reports=0, trust=1)
    assert score_b > score_a


def test_report_threshold_transitions_to_hidden():
    state = apply_report_threshold(status="visible", reports=12, threshold=10)
    assert state == "hidden"


def test_evidence_grade_and_countdown_affect_score():
    baseline = compute_score(
        up=3,
        comments=2,
        views=10,
        preserve=1,
        reports=1,
        trust=1,
        evidence_grade="B",
        evidence_hours_left=72,
    )
    degraded = compute_score(
        up=3,
        comments=2,
        views=10,
        preserve=1,
        reports=1,
        trust=1,
        evidence_grade="C",
        evidence_hours_left=6,
    )
    assert degraded < baseline


def test_board_emotion_and_dial_interaction_affect_score():
    common = {
        "up": 6,
        "comments": 3,
        "views": 80,
        "preserve": 2,
        "reports": 1,
        "trust": 2,
        "board_emotion": "냉소",
    }
    score_h = compute_score(**common, dial_dominant_axis="H")
    score_e = compute_score(**common, dial_dominant_axis="E")
    assert score_h > score_e
