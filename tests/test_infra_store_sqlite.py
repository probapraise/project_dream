import json
from pathlib import Path

from project_dream.infra.store import SQLiteRunRepository


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
        "moderation_decisions": [
            {
                "round": 1,
                "action_type": "NO_OP",
                "reason_rule_id": "RULE-PLZ-UI-01",
                "status_before": "visible",
                "status_after": "visible",
                "report_total": 0,
            }
        ],
        "end_condition": {
            "termination_reason": "round_limit",
            "ended_round": 1,
            "ended_early": False,
            "status": "visible",
        },
        "graph_node_trace": {
            "schema_version": "graph_node_trace.v1",
            "backend": "manual",
            "nodes": [
                {"node_id": "thread_candidate", "event_type": "thread_candidate", "event_count": 1},
                {"node_id": "round_loop", "event_type": "round_summary", "event_count": 1},
                {"node_id": "moderation", "event_type": "moderation_decision", "event_count": 1},
                {"node_id": "end_condition", "event_type": "end_condition", "event_count": 1},
            ],
        },
    }


def _sample_report() -> dict:
    return {
        "schema_version": "report.v1",
        "seed_id": "SEED-STORE-SQLITE-001",
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
        "report_gate": {"schema_version": "report_gate.v1", "pass_fail": True, "checks": [], "failed_checks": []},
    }


def test_sqlite_run_repository_persists_and_reads_run_artifacts(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")
    run_dir = repo.persist_run(_sample_sim_result(), _sample_report())

    assert run_dir.exists()
    assert (tmp_path / "runs" / "runs.sqlite3").exists()

    report = repo.load_report(run_dir.name)
    runlog = repo.load_runlog(run_dir.name)
    assert report["schema_version"] == "report.v1"
    assert runlog["run_id"] == run_dir.name
    assert runlog["rows"]
    graph_nodes = [row for row in runlog["rows"] if row.get("type") == "graph_node"]
    assert len(graph_nodes) == 4


def test_sqlite_run_repository_updates_eval_and_latest_lookup(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")
    run_dir = repo.persist_run(_sample_sim_result(), _sample_report())
    eval_result = {"schema_version": "eval.v1", "run_id": run_dir.name, "seed_id": "SEED-STORE-SQLITE-001", "pass_fail": True}
    eval_path = repo.persist_eval(run_dir, eval_result)

    assert eval_path.exists()
    assert repo.find_latest_run() == run_dir
    loaded_eval = repo.load_eval(run_dir.name)
    assert loaded_eval["schema_version"] == "eval.v1"


def test_sqlite_run_repository_get_run_raises_for_missing_id(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")
    try:
        repo.get_run("run-does-not-exist")
    except FileNotFoundError:
        return
    assert False, "expected FileNotFoundError"
