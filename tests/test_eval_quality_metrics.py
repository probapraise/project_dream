import json
from pathlib import Path

from project_dream.eval_suite import evaluate_run


def _write_quality_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    runlog_rows = [
        {"type": "context", "bundle": {"board_id": "B01", "zone_id": "A"}, "corpus": ["ctx-1"]},
        {"type": "thread_candidate", "candidate_id": "TC-1", "thread_template_id": "T1"},
        {"type": "thread_selected", "candidate_id": "TC-1", "thread_template_id": "T1"},
        {
            "type": "round_summary",
            "round": 1,
            "participant_count": 1,
            "report_events": 1,
            "policy_events": 1,
            "status": "hidden",
            "max_score": 1.0,
        },
        {
            "type": "moderation_decision",
            "round": 1,
            "action_type": "HIDE_PREVIEW",
            "reason_rule_id": "RULE-PLZ-MOD-01",
            "status_before": "visible",
            "status_after": "hidden",
            "report_total": 2,
        },
        {
            "type": "end_condition",
            "termination_reason": "round_limit",
            "ended_round": 3,
            "ended_early": False,
            "status": "locked",
        },
        {
            "type": "round",
            "round": 1,
            "community_id": "COM-PLZ-001",
            "comment_flow_id": "P2",
            "sort_tab": "evidence_first",
            "dial_target_flow_id": "P2",
            "dial_target_sort_tab": "evidence_first",
            "dial_dominant_axis": "E",
            "board_emotion": "정밀",
            "culture_weight_multiplier": 1.05,
        },
        {
            "type": "round",
            "round": 2,
            "community_id": "COM-PLZ-002",
            "comment_flow_id": "P2",
            "sort_tab": "evidence_first",
            "dial_target_flow_id": "P2",
            "dial_target_sort_tab": "evidence_first",
            "dial_dominant_axis": "E",
            "board_emotion": "정밀",
            "culture_weight_multiplier": 1.05,
        },
        {
            "type": "round",
            "round": 3,
            "community_id": "COM-PLZ-002",
            "comment_flow_id": "P2",
            "sort_tab": "evidence_first",
            "dial_target_flow_id": "P2",
            "dial_target_sort_tab": "evidence_first",
            "dial_dominant_axis": "E",
            "board_emotion": "정밀",
            "culture_weight_multiplier": 1.05,
        },
        {"type": "gate", "round": 1, "gates": [{"gate_name": "safety", "passed": False}]},
        {"type": "gate", "round": 2, "gates": [{"gate_name": "lore", "passed": True}]},
        {"type": "action", "round": 1, "action_type": "REPORT"},
        {"type": "action", "round": 2, "action_type": "HIDE_PREVIEW"},
        {"type": "action", "round": 3, "action_type": "LOCK_THREAD"},
    ]
    (run_dir / "runlog.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in runlog_rows),
        encoding="utf-8",
    )

    report = {
        "schema_version": "report.v1",
        "seed_id": "SEED-Q-001",
        "title": "품질 지표 테스트",
        "summary": "요약",
        "lens_summaries": [{"community_id": f"COM-PLZ-00{i}", "summary": "s"} for i in range(1, 5)],
        "highlights_top10": [{"round": 1, "text": "t"}],
        "conflict_map": {
            "claim_a": "a",
            "claim_b": "b",
            "third_interest": "c",
            "mediation_points": ["m1"],
        },
        "dialogue_candidates": [
            {"speaker": "x", "line": "l1"},
            {"speaker": "y", "line": "l2"},
            {"speaker": "z", "line": "l3"},
        ],
        "foreshadowing": ["f1"],
        "risk_checks": [{"category": "rule", "severity": "low", "details": "ok"}],
        "story_checklist": {
            "countdown_risk": {"label": "카운트다운", "status": "ok", "details": "expires_in_hours=48"},
            "evidence_grade": {"label": "증거 등급", "status": "ok", "details": "grade=B"},
            "board_migration_clue": {"label": "보드 이동", "status": "risk", "details": "board_ids=['B01','B02']"},
            "meme": {"label": "밈", "status": "ok", "details": "meme_seed_id=MM-001"},
            "event_card": {"label": "이벤트", "status": "ok", "details": "event_card_id=EV-001"},
        },
    }
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def test_eval_quality_v1_metrics_are_present_and_bounded(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-quality"
    _write_quality_run(run_dir)

    result = evaluate_run(run_dir, metric_set="v1")

    assert result["metric_set"] == "v1"
    assert 0.0 <= result["metrics"]["moderation_intervention_rate"] <= 1.0
    assert 0.0 <= result["metrics"]["gate_rewrite_rate"] <= 1.0
    assert 0.0 <= result["metrics"]["community_dispersion"] <= 1.0
    assert 0.0 <= result["metrics"]["stage_trace_coverage_rate"] <= 1.0


def test_eval_quality_v2_metrics_include_v1_and_new_metrics(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-quality-v2"
    _write_quality_run(run_dir)

    result = evaluate_run(run_dir, metric_set="v2")

    assert result["metric_set"] == "v2"
    assert "moderation_intervention_rate" in result["metrics"]
    assert "gate_rewrite_rate" in result["metrics"]
    assert "community_dispersion" in result["metrics"]
    assert "stage_trace_coverage_rate" in result["metrics"]
    assert "lore_pass_rate" in result["metrics"]
    assert "moderation_escalation_depth" in result["metrics"]
    assert "dialogue_speaker_diversity" in result["metrics"]
    assert "dial_flow_alignment_rate" in result["metrics"]
    assert "dial_sort_tab_alignment_rate" in result["metrics"]
    assert "culture_dial_alignment_rate" in result["metrics"]
    assert "culture_weight_avg" in result["metrics"]
    assert 0.0 <= result["metrics"]["lore_pass_rate"] <= 1.0
    assert 0.0 <= result["metrics"]["moderation_escalation_depth"] <= 1.0
    assert 0.0 <= result["metrics"]["dialogue_speaker_diversity"] <= 1.0
    assert result["metrics"]["dial_flow_alignment_rate"] == 1.0
    assert result["metrics"]["dial_sort_tab_alignment_rate"] == 1.0
    assert 0.0 <= result["metrics"]["culture_dial_alignment_rate"] <= 1.0
    assert result["metrics"]["culture_weight_avg"] >= 1.0


def test_eval_quality_unknown_metric_set_raises(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-quality-unknown"
    _write_quality_run(run_dir)

    try:
        evaluate_run(run_dir, metric_set="v99")
    except ValueError as exc:
        assert "Unknown metric_set" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown metric_set")
