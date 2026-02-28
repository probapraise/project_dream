import json
from pathlib import Path

from project_dream.infra.store import FileRunRepository


def _sample_sim_result() -> dict:
    return {
        "thread_candidates": [
            {
                "candidate_id": "TC-1",
                "thread_template_id": "T1",
                "comment_flow_id": "P1",
                "score": 0.9,
                "text": "후보 1",
            }
        ],
        "selected_thread": {
            "candidate_id": "TC-1",
            "thread_template_id": "T1",
            "comment_flow_id": "P1",
            "score": 0.9,
            "text": "후보 1",
        },
        "rounds": [{"round": 1, "persona_id": "P1", "text": "t", "community_id": "COM-PLZ-001"}],
        "gate_logs": [{"round": 1, "persona_id": "P1", "gates": [{"gate_name": "safety", "passed": True}]}],
        "action_logs": [{"round": 1, "action_type": "POST_COMMENT"}],
        "round_summaries": [
            {
                "round": 1,
                "participant_count": 1,
                "report_events": 0,
                "policy_events": 0,
                "status": "visible",
                "max_score": 1.0,
            }
        ],
        "end_condition": {
            "termination_reason": "round_limit",
            "ended_round": 1,
            "ended_early": False,
            "status": "visible",
        },
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


def test_file_run_repository_persists_context_row_when_present(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    sim_result = _sample_sim_result()
    sim_result["context_bundle"] = {
        "task": "거래 사기 의혹",
        "seed": "중계망 장애",
        "board_id": "B07",
        "zone_id": "D",
        "persona_ids": ["P07"],
        "sections": {"evidence": [], "policy": [], "organization": [], "hierarchy": []},
    }
    sim_result["context_corpus"] = ["ctx-B07-D-1", "ctx-B07-D-2"]

    run_dir = repo.persist_run(sim_result, _sample_report())

    rows = [
        json.loads(line)
        for line in (run_dir / "runlog.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    assert rows[0]["type"] == "context"
    assert rows[0]["bundle"]["board_id"] == "B07"
    assert rows[0]["corpus"] == ["ctx-B07-D-1", "ctx-B07-D-2"]


def test_file_run_repository_persists_thread_rows_when_present(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    sim_result = _sample_sim_result()
    run_dir = repo.persist_run(sim_result, _sample_report())

    rows = [
        json.loads(line)
        for line in (run_dir / "runlog.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    row_types = [row.get("type") for row in rows]

    assert "thread_candidate" in row_types
    assert "thread_selected" in row_types

    selected = next(row for row in rows if row.get("type") == "thread_selected")
    assert selected["candidate_id"] == "TC-1"

    round_summary = next(row for row in rows if row.get("type") == "round_summary")
    assert round_summary["round"] == 1
    assert round_summary["participant_count"] == 1

    end_condition = next(row for row in rows if row.get("type") == "end_condition")
    assert end_condition["termination_reason"] == "round_limit"
