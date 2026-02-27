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
        "seed_id": "SEED-001",
        "title": "테스트",
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


def test_evaluate_run_passes_on_valid_structure(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-1"
    _write_valid_run(run_dir)

    result = evaluate_run(run_dir)

    assert result["pass_fail"] is True
    assert result["seed_id"] == "SEED-001"
    assert result["checks"]


def test_evaluate_run_fails_on_missing_required_sections(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run-2"
    _write_valid_run(run_dir)

    broken = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    broken.pop("conflict_map")
    (run_dir / "report.json").write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")

    result = evaluate_run(run_dir)

    assert result["pass_fail"] is False
    assert any(c["name"] == "report.required_sections" and c["passed"] is False for c in result["checks"])
