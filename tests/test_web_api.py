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
