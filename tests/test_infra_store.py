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

    moderation = next(row for row in rows if row.get("type") == "moderation_decision")
    assert moderation["action_type"] == "NO_OP"
    assert moderation["status_after"] == "visible"

    end_condition = next(row for row in rows if row.get("type") == "end_condition")
    assert end_condition["termination_reason"] == "round_limit"

    graph_nodes = [row for row in rows if row.get("type") == "graph_node"]
    assert len(graph_nodes) == 4
    assert [row["node_id"] for row in graph_nodes] == [
        "thread_candidate",
        "round_loop",
        "moderation",
        "end_condition",
    ]

    graph_node_attempts = [row for row in rows if row.get("type") == "graph_node_attempt"]
    assert len(graph_node_attempts) == 4
    moderation_attempt = next(row for row in graph_node_attempts if row.get("node_id") == "moderation")
    assert moderation_attempt["attempts"] == 2

    stage_checkpoints = [row for row in rows if row.get("type") == "stage_checkpoint"]
    assert len(stage_checkpoints) == 5
    assert any(row.get("outcome") == "retry" for row in stage_checkpoints)

    runlog_payload = repo.load_runlog(run_dir.name)
    assert "summary" in runlog_payload
    assert runlog_payload["summary"]["row_counts"]["graph_node"] == 4
    assert runlog_payload["summary"]["row_counts"]["graph_node_attempt"] == 4
    assert runlog_payload["summary"]["row_counts"]["stage_checkpoint"] == 5
    assert runlog_payload["summary"]["stage"]["retry_count"] == 1
    assert runlog_payload["summary"]["stage"]["failure_count"] == 0
    assert runlog_payload["summary"]["stage"]["max_attempts"] == 2


def test_file_run_repository_persists_meme_flow_rows_when_present(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    sim_result = _sample_sim_result()
    sim_result["meme_flow_logs"] = [
        {
            "round": 1,
            "meme_seed_id": "MM-001",
            "meme_decay_profile": "explosive",
            "phase": "hub_to_factory",
            "from_board_id": "B07",
            "to_board_id": "B16",
            "meme_heat": 1.0,
        }
    ]

    run_dir = repo.persist_run(sim_result, _sample_report())
    rows = [
        json.loads(line)
        for line in (run_dir / "runlog.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    meme_rows = [row for row in rows if row.get("type") == "meme_flow"]

    assert len(meme_rows) == 1
    assert meme_rows[0]["meme_seed_id"] == "MM-001"
    assert meme_rows[0]["meme_decay_profile"] == "explosive"


def test_file_run_repository_lists_runs_with_filters_and_pagination(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")

    sim_first = _sample_sim_result()
    sim_first["rounds"][0]["board_id"] = "B07"
    sim_first["end_condition"]["status"] = "visible"
    report_first = _sample_report()
    report_first["seed_id"] = "SEED-FILE-LIST-1"
    report_first["report_gate"] = {"pass_fail": True}

    sim_second = _sample_sim_result()
    sim_second["rounds"][0]["board_id"] = "B08"
    sim_second["end_condition"]["status"] = "locked"
    report_second = _sample_report()
    report_second["seed_id"] = "SEED-FILE-LIST-2"
    report_second["report_gate"] = {"pass_fail": False}

    run_first = repo.persist_run(sim_first, report_first)
    run_second = repo.persist_run(sim_second, report_second)

    listed = repo.list_runs()
    assert listed["count"] == 2
    assert listed["total"] == 2
    assert listed["limit"] == 20
    assert listed["offset"] == 0
    listed_ids = [row["run_id"] for row in listed["items"]]
    assert set(listed_ids) == {run_first.name, run_second.name}
    by_id = {row["run_id"]: row for row in listed["items"]}
    assert by_id[run_first.name]["stage_retry_count"] == 1
    assert by_id[run_first.name]["stage_failure_count"] == 0
    assert by_id[run_first.name]["max_stage_attempts"] == 2

    filtered_seed = repo.list_runs(seed_id="SEED-FILE-LIST-1")
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
    assert paged["items"][0]["run_id"] == listed["items"][1]["run_id"]


def test_file_run_repository_lists_regressions_with_filters_and_pagination(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    regressions_dir = tmp_path / "runs" / "regressions"
    regressions_dir.mkdir(parents=True, exist_ok=True)

    first_path = regressions_dir / "regression-20260228-000000-000001.json"
    second_path = regressions_dir / "regression-20260228-000001-000001.json"

    first_path.write_text(
        json.dumps(
            {
                "schema_version": "regression.v1",
                "metric_set": "v1",
                "generated_at_utc": "2026-02-28T00:00:00+00:00",
                "pass_fail": True,
                "totals": {"seed_runs": 2},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    second_path.write_text(
        json.dumps(
            {
                "schema_version": "regression.v1",
                "metric_set": "v2",
                "generated_at_utc": "2026-02-28T00:01:00+00:00",
                "pass_fail": False,
                "totals": {"seed_runs": 1},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    listed = repo.list_regression_summaries()
    assert listed["count"] == 2
    assert listed["total"] == 2
    assert listed["offset"] == 0
    assert listed["items"][0]["summary_id"] == second_path.name

    filtered_metric = repo.list_regression_summaries(metric_set="v1")
    assert filtered_metric["count"] == 1
    assert filtered_metric["items"][0]["summary_id"] == first_path.name

    filtered_pass = repo.list_regression_summaries(pass_fail=False)
    assert filtered_pass["count"] == 1
    assert filtered_pass["items"][0]["summary_id"] == second_path.name

    paged = repo.list_regression_summaries(limit=1, offset=1)
    assert paged["count"] == 1
    assert paged["total"] == 2
    assert paged["limit"] == 1
    assert paged["offset"] == 1
    assert paged["items"][0]["summary_id"] == first_path.name
