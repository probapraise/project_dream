from pathlib import Path

import pytest

from project_dream.infra.store import FileRunRepository, SQLiteRunRepository
from project_dream.infra.web_api import ProjectDreamAPI


def test_web_api_health():
    api = ProjectDreamAPI(repository=FileRunRepository(Path("runs")), packs_dir=Path("packs"))
    health = api.health()
    assert health["status"] == "ok"


def test_web_api_simulate_and_evaluate(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    sim_res = api.simulate(
        {
            "seed_id": "SEED-API-001",
            "title": "api 시뮬",
            "summary": "api 요약",
            "board_id": "B07",
            "zone_id": "D",
        },
        rounds=3,
    )
    assert sim_res["run_id"].startswith("run-")

    eval_res = api.evaluate(run_id=sim_res["run_id"], metric_set="v2")
    assert eval_res["schema_version"] == "eval.v1"
    assert eval_res["metric_set"] == "v2"


def test_web_api_regress(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    summary = api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=3,
        metric_set="v2",
    )
    assert summary["schema_version"] == "regression.v1"
    assert summary["metric_set"] == "v2"
    assert summary["totals"]["seed_runs"] == 3


def test_web_api_latest_regression_summary(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=2,
        metric_set="v2",
    )
    latest_summary = api.latest_regression_summary()

    assert latest_summary["schema_version"] == "regression.v1"
    assert latest_summary["metric_set"] == "v2"
    assert latest_summary["totals"]["seed_runs"] == 2
    assert latest_summary["summary_path"].endswith(".json")


def test_web_api_regression_summary_by_id(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    created = api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=2,
        metric_set="v2",
    )
    summary_id = Path(created["summary_path"]).name
    summary_id_stem = summary_id.removesuffix(".json")

    loaded_with_filename = api.get_regression_summary(summary_id)
    loaded_with_stem = api.get_regression_summary(summary_id_stem)

    assert loaded_with_filename["schema_version"] == "regression.v1"
    assert loaded_with_filename["metric_set"] == "v2"
    assert loaded_with_filename["summary_path"].endswith(summary_id)
    assert loaded_with_stem["summary_path"].endswith(summary_id)


def test_web_api_list_regression_summaries(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=2,
        metric_set="v1",
    )
    api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=2,
        metric_set="v2",
    )

    listed = api.list_regression_summaries()
    latest = api.latest_regression_summary()
    latest_id = Path(latest["summary_path"]).name

    assert listed["count"] == 2
    assert listed["total"] == 2
    assert listed["offset"] == 0
    assert len(listed["items"]) == 2
    assert listed["items"][0]["summary_id"] == latest_id
    assert listed["items"][0]["summary_path"].endswith(latest_id)
    assert listed["items"][0]["metric_set"] in {"v1", "v2"}
    assert isinstance(listed["items"][0]["pass_fail"], bool)

    filtered_metric = api.list_regression_summaries(metric_set="v1")
    assert filtered_metric["count"] == 1
    assert filtered_metric["items"][0]["metric_set"] == "v1"

    filtered_pass = api.list_regression_summaries(pass_fail=True)
    assert filtered_pass["count"] >= 1
    assert all(item["pass_fail"] is True for item in filtered_pass["items"])

    limited = api.list_regression_summaries(limit=1, offset=1)
    assert limited["count"] == 1
    assert limited["total"] == 2
    assert limited["limit"] == 1
    assert limited["offset"] == 1
    assert len(limited["items"]) == 1


def test_web_api_read_endpoints(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    sim_res = api.simulate(
        {
            "seed_id": "SEED-API-READ-001",
            "title": "api read",
            "summary": "api read summary",
            "board_id": "B07",
            "zone_id": "D",
        },
        rounds=3,
    )
    api.evaluate(run_id=sim_res["run_id"], metric_set="v2")

    latest = api.latest_run()
    report = api.get_report(sim_res["run_id"])
    eva = api.get_eval(sim_res["run_id"])
    runlog = api.get_runlog(sim_res["run_id"])

    assert latest["run_id"] == sim_res["run_id"]
    assert report["schema_version"] == "report.v1"
    assert eva["schema_version"] == "eval.v1"
    assert runlog["run_id"] == sim_res["run_id"]
    assert runlog["rows"]
    assert any(row.get("type") == "context" for row in runlog["rows"])
    assert runlog["summary"]["row_counts"]["graph_node"] >= 4
    assert runlog["summary"]["row_counts"]["stage_checkpoint"] >= 4
    assert "retry_count" in runlog["summary"]["stage"]
    assert "failure_count" in runlog["summary"]["stage"]
    assert "max_attempts" in runlog["summary"]["stage"]


def test_web_api_list_runs_with_filters_and_pagination(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    run_first = api.simulate(
        {
            "seed_id": "SEED-API-LIST-001",
            "title": "api list 1",
            "summary": "api list summary 1",
            "board_id": "B07",
            "zone_id": "D",
        },
        rounds=3,
    )["run_id"]
    run_second = api.simulate(
        {
            "seed_id": "SEED-API-LIST-002",
            "title": "api list 2",
            "summary": "api list summary 2",
            "board_id": "B07",
            "zone_id": "D",
        },
        rounds=3,
    )["run_id"]

    listed = api.list_runs()
    assert listed["count"] == 2
    assert listed["total"] == 2
    listed_ids = [row["run_id"] for row in listed["items"]]
    assert set(listed_ids) == {run_first, run_second}
    first_item = listed["items"][0]
    assert "stage_retry_count" in first_item
    assert "stage_failure_count" in first_item
    assert "max_stage_attempts" in first_item

    filtered_seed = api.list_runs(seed_id="SEED-API-LIST-001")
    assert filtered_seed["count"] == 1
    assert filtered_seed["items"][0]["run_id"] == run_first

    paged = api.list_runs(limit=1, offset=1)
    assert paged["count"] == 1
    assert paged["total"] == 2
    assert paged["items"][0]["run_id"] == listed["items"][1]["run_id"]


def test_web_api_kb_query_methods(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    searched = api.search_knowledge(
        query="illegal_trade",
        filters={"kind": "board", "board_id": "B07"},
        top_k=3,
    )
    assert searched["count"] >= 1
    assert searched["items"][0]["item_id"] == "B07"

    board = api.get_pack_item("board", "B07")
    assert board["id"] == "B07"
    assert board["name"] == "장터기둥"

    ctx = api.retrieve_context_bundle(
        task="거래 사기 의혹",
        seed="중계망 장애",
        board_id="B07",
        zone_id="D",
        persona_ids=["P07"],
        top_k=2,
    )
    assert "bundle" in ctx
    assert "corpus" in ctx
    assert ctx["bundle"]["board_id"] == "B07"
    assert ctx["corpus"]


def test_web_api_kb_query_uses_ingested_corpus(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "reference.jsonl").write_text(
        '{"board_id":"B07","zone_id":"D","doc_id":"DOC-API-001","source_type":"reference","text":"API-INGEST-CTX-B07"}\n',
        encoding="utf-8",
    )
    (corpus_dir / "refined.jsonl").write_text("", encoding="utf-8")
    (corpus_dir / "generated.jsonl").write_text("", encoding="utf-8")

    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"), corpus_dir=corpus_dir)

    searched = api.search_knowledge(
        query="API-INGEST-CTX-B07",
        filters={"kind": "corpus", "board_id": "B07"},
        top_k=3,
    )
    assert searched["count"] >= 1
    assert searched["items"][0]["kind"] == "corpus"
    assert searched["items"][0]["source_type"] == "reference"

    ctx = api.retrieve_context_bundle(
        task="거래 사기 의혹",
        seed="중계망 장애",
        board_id="B07",
        zone_id="D",
        persona_ids=["P07"],
        top_k=3,
    )
    assert any("API-INGEST-CTX-B07" in text for text in ctx["corpus"])


def test_web_api_for_local_filesystem_supports_sqlite_backend(tmp_path: Path):
    db_path = tmp_path / "custom-runs.sqlite3"
    vector_db_path = tmp_path / "custom-vectors.sqlite3"
    api = ProjectDreamAPI.for_local_filesystem(
        runs_dir=tmp_path / "runs",
        packs_dir=Path("packs"),
        repository_backend="sqlite",
        sqlite_db_path=db_path,
        vector_backend="sqlite",
        vector_db_path=vector_db_path,
    )

    assert isinstance(api.repository, SQLiteRunRepository)
    assert api.repository.db_path == db_path
    assert api.vector_backend == "sqlite"
    assert api.vector_db_path == vector_db_path


def test_web_api_for_local_filesystem_rejects_unknown_backend(tmp_path: Path):
    with pytest.raises(ValueError):
        ProjectDreamAPI.for_local_filesystem(
            runs_dir=tmp_path / "runs",
            packs_dir=Path("packs"),
            repository_backend="unknown",
        )


def test_web_api_for_local_filesystem_rejects_unknown_vector_backend(tmp_path: Path):
    with pytest.raises(ValueError):
        ProjectDreamAPI.for_local_filesystem(
            runs_dir=tmp_path / "runs",
            packs_dir=Path("packs"),
            vector_backend="unknown",
        )


def test_web_api_sqlite_regression_summary_index_survives_file_deletion(tmp_path: Path):
    repo = SQLiteRunRepository(tmp_path / "runs")
    api = ProjectDreamAPI(repository=repo, packs_dir=Path("packs"))

    summary = api.regress(
        seeds_dir=Path("examples/seeds/regression"),
        rounds=3,
        max_seeds=1,
        metric_set="v2",
        min_community_coverage=1,
        min_conflict_frame_runs=0,
        min_moderation_hook_runs=0,
        min_validation_warning_runs=0,
    )
    summary_path = Path(summary["summary_path"])
    summary_id = summary_path.name
    summary_path.unlink()

    listed = api.list_regression_summaries()
    assert listed["count"] >= 1
    assert any(item["summary_id"] == summary_id for item in listed["items"])

    latest = api.latest_regression_summary()
    assert latest["schema_version"] == "regression.v1"
    assert latest["summary_path"].endswith(summary_id)

    loaded = api.get_regression_summary(summary_id.removesuffix(".json"))
    assert loaded["schema_version"] == "regression.v1"
    assert loaded["summary_path"].endswith(summary_id)
