from pathlib import Path

import pytest

import project_dream.app_service as app_service
from project_dream.models import SeedInput


class _FakeRepository:
    def __init__(self, root: Path):
        self.runs_dir = root

    def persist_run(self, sim_result: dict, report: dict) -> Path:
        run_dir = self.runs_dir / "run-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


def test_simulate_and_persist_passes_retrieved_corpus(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict = {}

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        captured["seed_id"] = seed.seed_id
        captured["rounds"] = rounds
        captured["corpus"] = corpus
        return {
            "rounds": [],
            "gate_logs": [],
            "action_logs": [],
            "thread_state": {
                "board_id": seed.board_id,
                "community_id": "COM-PLZ-004",
                "thread_template_id": "T1",
                "comment_flow_id": "P1",
                "status": "visible",
                "total_reports": 0,
            },
        }

    monkeypatch.setattr(app_service, "run_simulation", fake_run_simulation)
    monkeypatch.setattr(
        app_service,
        "build_report_v1",
        lambda seed, sim_result, packs: {"schema_version": "report.v1", "seed_id": seed.seed_id},
    )

    seed = SeedInput(
        seed_id="SEED-KB-001",
        title="장터 분쟁",
        summary="거래 사기 의혹이 확산되는 사건",
        board_id="B07",
        zone_id="D",
    )
    repo = _FakeRepository(tmp_path / "runs")

    run_dir = app_service.simulate_and_persist(
        seed=seed,
        rounds=3,
        packs_dir=Path("packs"),
        repository=repo,
    )

    assert run_dir.name == "run-001"
    assert captured["seed_id"] == "SEED-KB-001"
    assert captured["rounds"] == 3
    assert captured["corpus"]
    assert any("장터기둥" in row or "B07" in row for row in captured["corpus"])
