from project_dream.env_engine import compute_score, apply_report_threshold


def test_preserve_token_has_strong_visibility_effect():
    score_a = compute_score(up=3, comments=2, views=10, preserve=0, reports=0, trust=1)
    score_b = compute_score(up=3, comments=2, views=10, preserve=5, reports=0, trust=1)
    assert score_b > score_a


def test_report_threshold_transitions_to_hidden():
    state = apply_report_threshold(status="visible", reports=12, threshold=10)
    assert state == "hidden"
