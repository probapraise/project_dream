import json
from pathlib import Path

from project_dream.eval_suite import evaluate_run


def _write_valid_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    runlog = run_dir / "runlog.jsonl"
    rows = [
        {"type": "round", "round": 1, "community_id": "COM-PLZ-001"},
        {"type": "gate", "round": 1, "gates": [{"gate_name": "safety", "passed": True}]},
        {"type": "action", "round": 1, "action_type": "REPORT"},
    ]
    runlog.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    report = {
        "schema_version": "report.v1",
        "seed_id": "SEED-RQ-001",
        "title": "리포트 품질 체크",
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


def test_evaluate_includes_report_quality_checks(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-rq-pass"
    _write_valid_run(run_dir)

    result = evaluate_run(run_dir, metric_set="v1")

    checks = {c["name"]: c["passed"] for c in result["checks"]}
    assert "report.conflict_map.mediation_points_count" in checks
    assert "report.foreshadowing_count" in checks
    assert "report.dialogue_candidate_fields" in checks
    assert "report.risk_checks.severity_values" in checks
    assert checks["report.conflict_map.mediation_points_count"] is True
    assert checks["report.foreshadowing_count"] is True
    assert checks["report.dialogue_candidate_fields"] is True
    assert checks["report.risk_checks.severity_values"] is True


def test_evaluate_fails_when_risk_severity_is_invalid(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-rq-fail"
    _write_valid_run(run_dir)

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report["risk_checks"][0]["severity"] = "critical"
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

    result = evaluate_run(run_dir, metric_set="v1")
    checks = {c["name"]: c["passed"] for c in result["checks"]}

    assert result["pass_fail"] is False
    assert checks["report.risk_checks.severity_values"] is False
