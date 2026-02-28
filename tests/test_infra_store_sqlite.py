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
            "node_attempts": {
                "thread_candidate": 1,
                "round_loop": 1,
                "moderation": 2,
                "end_condition": 1,
            },
            "stage_checkpoints": [
                {"node_id": "thread_candidate", "attempt": 1, "outcome": "success"},
                {"node_id": "round_loop", "attempt": 1, "outcome": "success"},
                {"node_id": "moderation", "attempt": 1, "outcome": "retry", "error": "transient"},
                {"node_id": "moderation", "attempt": 2, "outcome": "success"},
                {"node_id": "end_condition", "attempt": 1, "outcome": "success"},
            ],
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
    graph_node_attempts = [row for row in runlog["rows"] if row.get("type") == "graph_node_attempt"]
    assert len(graph_node_attempts) == 4
    stage_checkpoints = [row for row in runlog["rows"] if row.get("type") == "stage_checkpoint"]
    assert len(stage_checkpoints) == 5


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


def test_sqlite_run_repository_lists_runs_with_filters_and_pagination(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")

    sim_first = _sample_sim_result()
    sim_first["thread_state"] = {
        "board_id": "B07",
        "zone_id": "D",
        "status": "visible",
        "termination_reason": "round_limit",
        "total_reports": 0,
    }
    report_first = _sample_report()
    report_first["seed_id"] = "SEED-SQLITE-LIST-1"
    report_first["report_gate"] = {"pass_fail": True}

    sim_second = _sample_sim_result()
    sim_second["thread_state"] = {
        "board_id": "B08",
        "zone_id": "D",
        "status": "locked",
        "termination_reason": "moderation_lock",
        "total_reports": 3,
    }
    report_second = _sample_report()
    report_second["seed_id"] = "SEED-SQLITE-LIST-2"
    report_second["report_gate"] = {"pass_fail": False}

    run_first = repo.persist_run(sim_first, report_first)
    run_second = repo.persist_run(sim_second, report_second)

    listed = repo.list_runs()
    assert listed["count"] == 2
    assert listed["total"] == 2
    assert listed["limit"] == 20
    assert listed["offset"] == 0
    assert [row["run_id"] for row in listed["items"]] == [run_second.name, run_first.name]
    by_id = {row["run_id"]: row for row in listed["items"]}
    assert by_id[run_first.name]["stage_retry_count"] == 1
    assert by_id[run_first.name]["stage_failure_count"] == 0
    assert by_id[run_first.name]["max_stage_attempts"] == 2

    filtered_seed = repo.list_runs(seed_id="SEED-SQLITE-LIST-1")
    assert filtered_seed["count"] == 1
    assert filtered_seed["items"][0]["run_id"] == run_first.name

    filtered_board = repo.list_runs(board_id="B08")
    assert filtered_board["count"] == 1
    assert filtered_board["items"][0]["run_id"] == run_second.name

    filtered_status = repo.list_runs(status="locked")
    assert filtered_status["count"] == 1
    assert filtered_status["items"][0]["run_id"] == run_second.name

    paged = repo.list_runs(limit=1, offset=1)
    assert paged["count"] == 1
    assert paged["total"] == 2
    assert paged["limit"] == 1
    assert paged["offset"] == 1
    assert paged["items"][0]["run_id"] == run_first.name


def test_sqlite_run_repository_uses_indexed_regression_summaries_when_file_missing(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")
    regressions_dir = tmp_path / "runs" / "regressions"
    regressions_dir.mkdir(parents=True, exist_ok=True)

    summary_path = regressions_dir / "regression-20260228-000000-000001.json"
    summary = {
        "schema_version": "regression.v1",
        "metric_set": "v2",
        "generated_at_utc": "2026-02-28T00:00:00+00:00",
        "pass_fail": True,
        "totals": {"seed_runs": 2},
        "gates": {"format_missing_zero": True},
        "runs": [],
        "summary_path": str(summary_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    repo.persist_regression_summary(summary)

    summary_path.unlink()

    listed = repo.list_regression_summaries()
    assert listed["count"] == 1
    assert listed["items"][0]["summary_id"] == summary_path.name
    assert listed["items"][0]["metric_set"] == "v2"
    assert listed["items"][0]["seed_runs"] == 2

    latest = repo.load_latest_regression_summary()
    assert latest["schema_version"] == "regression.v1"
    assert latest["metric_set"] == "v2"
    assert latest["summary_path"].endswith(summary_path.name)

    loaded = repo.load_regression_summary(summary_path.stem)
    assert loaded["schema_version"] == "regression.v1"
    assert loaded["totals"]["seed_runs"] == 2


def test_sqlite_run_repository_lists_regressions_with_filters_and_pagination(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")

    summary_first = {
        "schema_version": "regression.v1",
        "metric_set": "v1",
        "generated_at_utc": "2026-02-28T00:00:00+00:00",
        "pass_fail": True,
        "totals": {"seed_runs": 2},
        "summary_path": str(tmp_path / "runs" / "regressions" / "regression-20260228-000000-000001.json"),
    }
    summary_second = {
        "schema_version": "regression.v1",
        "metric_set": "v2",
        "generated_at_utc": "2026-02-28T00:01:00+00:00",
        "pass_fail": False,
        "totals": {"seed_runs": 1},
        "summary_path": str(tmp_path / "runs" / "regressions" / "regression-20260228-000001-000001.json"),
    }
    repo.persist_regression_summary(summary_first)
    repo.persist_regression_summary(summary_second)

    listed = repo.list_regression_summaries()
    assert listed["count"] == 2
    assert listed["total"] == 2
    assert listed["offset"] == 0
    assert listed["items"][0]["summary_id"].endswith("000001-000001.json")

    filtered_metric = repo.list_regression_summaries(metric_set="v1")
    assert filtered_metric["count"] == 1
    assert filtered_metric["items"][0]["metric_set"] == "v1"

    filtered_pass = repo.list_regression_summaries(pass_fail=False)
    assert filtered_pass["count"] == 1
    assert filtered_pass["items"][0]["pass_fail"] is False

    paged = repo.list_regression_summaries(limit=1, offset=1)
    assert paged["count"] == 1
    assert paged["total"] == 2
    assert paged["limit"] == 1
    assert paged["offset"] == 1
