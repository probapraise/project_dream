from pathlib import Path

from project_dream.infra.store import FileRunRepository
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
    assert len(listed["items"]) == 2
    assert listed["items"][0]["summary_id"] == latest_id
    assert listed["items"][0]["summary_path"].endswith(latest_id)
    assert listed["items"][0]["metric_set"] in {"v1", "v2"}
    assert isinstance(listed["items"][0]["pass_fail"], bool)

    limited = api.list_regression_summaries(limit=1)
    assert limited["count"] == 1
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
