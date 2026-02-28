from project_dream.env_engine import (
    apply_policy_transition,
    compute_action_cost,
    compute_sanction_level,
    compute_score,
    rank_threads_for_tab,
)


def test_account_type_affects_exposure_and_action_cost():
    base_kwargs = {
        "up": 8,
        "comments": 5,
        "views": 120,
        "preserve": 2,
        "reports": 1,
        "trust": 3,
    }

    score_public = compute_score(**base_kwargs, account_type="public")
    score_alias = compute_score(**base_kwargs, account_type="alias")
    score_mask = compute_score(**base_kwargs, account_type="mask")

    assert score_public > score_alias > score_mask

    cost_public = compute_action_cost("POST_COMMENT", account_type="public", sanction_level=1)
    cost_alias = compute_action_cost("POST_COMMENT", account_type="alias", sanction_level=1)
    cost_mask = compute_action_cost("POST_COMMENT", account_type="mask", sanction_level=1)
    assert cost_public < cost_alias < cost_mask


def test_report_severity_appeal_transition_matrix():
    status, event = apply_policy_transition(
        status="locked",
        reports=24,
        severity=2,
        appeal=False,
        account_type="mask",
        verified=False,
        sanction_level=3,
    )
    assert status == "ghost"
    assert event["action_type"] == "GHOST_THREAD"
    assert event["sanction_level"] == 4

    status, event = apply_policy_transition(
        status="ghost",
        reports=24,
        severity=1,
        appeal=True,
        account_type="mask",
        verified=True,
        sanction_level=4,
    )
    assert status == "locked"
    assert event["action_type"] == "APPEAL"
    assert event["appeal_result"] == "accepted"
    assert event["sanction_level"] == 3

    status, event = apply_policy_transition(
        status="ghost",
        reports=24,
        severity=3,
        appeal=True,
        account_type="alias",
        verified=False,
        sanction_level=4,
    )
    assert status == "ghost"
    assert event["action_type"] == "APPEAL_REJECT"
    assert event["sanction_level"] == 4


def test_sanction_level_progression_l1_to_l5():
    assert compute_sanction_level(reports=6, severity=0, status="visible") == 1
    assert compute_sanction_level(reports=12, severity=0, status="hidden") == 2
    assert compute_sanction_level(reports=19, severity=1, status="locked") == 3
    assert compute_sanction_level(reports=26, severity=2, status="ghost") == 4
    assert compute_sanction_level(reports=32, severity=3, status="sanctioned") == 5


def test_rank_tabs_prioritize_different_top_thread():
    threads = [
        {
            "thread_id": "t-latest",
            "up": 2,
            "comments": 1,
            "views": 40,
            "preserve": 1,
            "reports": 0,
            "trust": 1,
            "evidence": 1,
            "age_hours": 1,
        },
        {
            "thread_id": "t-hot",
            "up": 20,
            "comments": 9,
            "views": 350,
            "preserve": 2,
            "reports": 2,
            "trust": 3,
            "evidence": 2,
            "age_hours": 24,
        },
        {
            "thread_id": "t-evidence",
            "up": 8,
            "comments": 4,
            "views": 130,
            "preserve": 1,
            "reports": 0,
            "trust": 5,
            "evidence": 10,
            "age_hours": 16,
        },
        {
            "thread_id": "t-preserve",
            "up": 6,
            "comments": 3,
            "views": 100,
            "preserve": 12,
            "reports": 1,
            "trust": 2,
            "evidence": 3,
            "age_hours": 30,
        },
    ]

    ranked_latest = rank_threads_for_tab(threads, tab="latest")
    ranked_hot = rank_threads_for_tab(threads, tab="weekly_hot")
    ranked_evidence = rank_threads_for_tab(threads, tab="evidence_first")
    ranked_preserve = rank_threads_for_tab(threads, tab="preserve_first")

    assert ranked_latest[0]["thread_id"] == "t-latest"
    assert ranked_hot[0]["thread_id"] == "t-hot"
    assert ranked_evidence[0]["thread_id"] == "t-evidence"
    assert ranked_preserve[0]["thread_id"] == "t-preserve"
