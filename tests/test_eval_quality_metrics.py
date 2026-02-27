import json
from pathlib import Path

from project_dream.eval_suite import evaluate_run


def _write_quality_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    runlog_rows = [
        {"type": "round", "round": 1, "community_id": "COM-PLZ-001"},
        {"type": "round", "round": 2, "community_id": "COM-PLZ-002"},
        {"type": "round", "round": 3, "community_id": "COM-PLZ-002"},
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


def test_eval_quality_unknown_metric_set_raises(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-quality-unknown"
    _write_quality_run(run_dir)

    try:
        evaluate_run(run_dir, metric_set="v2")
    except ValueError as exc:
        assert "Unknown metric_set" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown metric_set")
