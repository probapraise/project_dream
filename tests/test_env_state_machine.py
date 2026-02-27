from project_dream.env_engine import apply_policy_transition


def test_reports_escalate_visible_to_hidden_and_locked():
    status, event = apply_policy_transition("visible", reports=10, severity=0, appeal=False)
    assert status == "hidden"
    assert event["action_type"] == "HIDE_PREVIEW"
    assert event["reason_rule_id"] == "RULE-PLZ-MOD-01"

    status, event = apply_policy_transition("hidden", reports=20, severity=0, appeal=False)
    assert status == "locked"
    assert event["action_type"] == "LOCK_THREAD"


def test_high_severity_can_ghost_or_sanction():
    status, event = apply_policy_transition("locked", reports=25, severity=2, appeal=False)
    assert status == "ghost"
    assert event["action_type"] == "GHOST_THREAD"

    status, event = apply_policy_transition("ghost", reports=30, severity=3, appeal=False)
    assert status == "sanctioned"
    assert event["action_type"] == "SANCTION_USER"


def test_appeal_can_step_back_once():
    status, event = apply_policy_transition("locked", reports=5, severity=0, appeal=True)
    assert status == "hidden"
    assert event["action_type"] == "APPEAL"
