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

    def fake_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured["seed_id"] = seed.seed_id
        captured["rounds"] = rounds
        captured["corpus"] = corpus
        captured["backend"] = backend
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

    monkeypatch.setattr(
        app_service,
        "run_simulation_with_backend",
        fake_run_simulation_with_backend,
    )
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
    assert captured["backend"] == "manual"
    assert any("장터기둥" in row or "B07" in row for row in captured["corpus"])


def test_simulate_and_persist_merges_ingested_corpus(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict = {}

    def fake_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured["corpus"] = list(corpus)
        captured["backend"] = backend
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

    monkeypatch.setattr(
        app_service,
        "run_simulation_with_backend",
        fake_run_simulation_with_backend,
    )
    monkeypatch.setattr(
        app_service,
        "build_report_v1",
        lambda seed, sim_result, packs: {"schema_version": "report.v1", "seed_id": seed.seed_id},
    )
    monkeypatch.setattr(
        app_service,
        "retrieve_context",
        lambda index, **kwargs: {"bundle": {}, "corpus": ["ctx-retrieved"]},
        raising=False,
    )

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "reference.jsonl").write_text(
        '{"text":"ctx-reference"}\n{"text":"ctx-retrieved"}\n',
        encoding="utf-8",
    )
    (corpus_dir / "refined.jsonl").write_text('{"text":"ctx-refined"}\n', encoding="utf-8")
    (corpus_dir / "generated.jsonl").write_text("", encoding="utf-8")

    seed = SeedInput(
        seed_id="SEED-KB-002",
        title="장터 분쟁",
        summary="거래 사기 의혹이 확산되는 사건",
        board_id="B07",
        zone_id="D",
    )
    repo = _FakeRepository(tmp_path / "runs")

    app_service.simulate_and_persist(
        seed=seed,
        rounds=3,
        packs_dir=Path("packs"),
        repository=repo,
        corpus_dir=corpus_dir,
    )

    assert captured["corpus"] == ["ctx-retrieved", "ctx-reference", "ctx-refined"]
    assert captured["backend"] == "manual"


def test_simulate_and_persist_forwards_orchestrator_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict = {}

    def fake_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured["backend"] = backend
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

    monkeypatch.setattr(app_service, "run_simulation_with_backend", fake_run_simulation_with_backend, raising=False)
    monkeypatch.setattr(
        app_service,
        "build_report_v1",
        lambda seed, sim_result, packs: {"schema_version": "report.v1", "seed_id": seed.seed_id},
    )

    seed = SeedInput(
        seed_id="SEED-KB-003",
        title="장터 분쟁",
        summary="거래 사기 의혹이 확산되는 사건",
        board_id="B07",
        zone_id="D",
    )
    repo = _FakeRepository(tmp_path / "runs")

    app_service.simulate_and_persist(
        seed=seed,
        rounds=3,
        packs_dir=Path("packs"),
        repository=repo,
        orchestrator_backend="langgraph",
    )

    assert captured["backend"] == "langgraph"


def test_simulate_and_persist_forwards_vector_backend_to_build_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict = {}

    def fake_build_index(packs, corpus_dir=None, *, vector_backend="memory", vector_db_path=None):
        captured["vector_backend"] = vector_backend
        captured["vector_db_path"] = vector_db_path
        return {"fake": "index"}

    def fake_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
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

    monkeypatch.setattr(app_service, "build_index", fake_build_index, raising=False)
    monkeypatch.setattr(
        app_service,
        "retrieve_context",
        lambda index, **kwargs: {"bundle": {}, "corpus": ["ctx-B07-D"]},
        raising=False,
    )
    monkeypatch.setattr(app_service, "run_simulation_with_backend", fake_run_simulation_with_backend, raising=False)
    monkeypatch.setattr(
        app_service,
        "build_report_v1",
        lambda seed, sim_result, packs: {"schema_version": "report.v1", "seed_id": seed.seed_id},
    )

    seed = SeedInput(
        seed_id="SEED-KB-004",
        title="장터 분쟁",
        summary="거래 사기 의혹이 확산되는 사건",
        board_id="B07",
        zone_id="D",
    )
    repo = _FakeRepository(tmp_path / "runs")
    vector_db_path = tmp_path / "vectors.sqlite3"

    app_service.simulate_and_persist(
        seed=seed,
        rounds=3,
        packs_dir=Path("packs"),
        repository=repo,
        vector_backend="sqlite",
        vector_db_path=vector_db_path,
    )

    assert captured["vector_backend"] == "sqlite"
    assert captured["vector_db_path"] == vector_db_path
