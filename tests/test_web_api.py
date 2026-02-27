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
