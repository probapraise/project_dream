import json
from pathlib import Path

from project_dream.infra.store import FileRunRepository


def _sample_sim_result() -> dict:
    return {
        "rounds": [{"round": 1, "persona_id": "P1", "text": "t", "community_id": "COM-PLZ-001"}],
        "gate_logs": [{"round": 1, "persona_id": "P1", "gates": [{"gate_name": "safety", "passed": True}]}],
        "action_logs": [{"round": 1, "action_type": "POST_COMMENT"}],
    }


def _sample_report() -> dict:
    return {
        "schema_version": "report.v1",
        "seed_id": "SEED-STORE-001",
        "title": "제목",
        "summary": "요약",
        "lens_summaries": [{"community_id": "COM-PLZ-001", "summary": "s"}],
        "highlights_top10": [{"round": 1, "text": "h"}],
        "conflict_map": {
            "claim_a": "a",
            "claim_b": "b",
            "third_interest": "c",
            "mediation_points": ["m1"],
        },
        "dialogue_candidates": [{"speaker": "p", "line": "l"}],
        "foreshadowing": ["f1"],
        "risk_checks": [{"category": "rule", "severity": "low", "details": "ok"}],
    }


def test_file_run_repository_persists_run_and_eval(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    run_dir = repo.persist_run(_sample_sim_result(), _sample_report())

    assert run_dir.exists()
    assert (run_dir / "runlog.jsonl").exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.md").exists()

    eval_result = {"schema_version": "eval.v1", "run_id": run_dir.name, "seed_id": "SEED-STORE-001"}
    eval_path = repo.persist_eval(run_dir, eval_result)
    assert eval_path.exists()
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "eval.v1"


def test_file_run_repository_finds_latest_and_by_id(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    run_dir = repo.persist_run(_sample_sim_result(), _sample_report())

    latest = repo.find_latest_run()
    same = repo.get_run(run_dir.name)

    assert latest == run_dir
    assert same == run_dir
