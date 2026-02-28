import pytest

from project_dream.models import SeedInput


def _seed() -> SeedInput:
    return SeedInput(
        seed_id="SEED-ORCH-001",
        title="오케스트레이터 테스트",
        summary="백엔드 분기 검증",
        board_id="B07",
        zone_id="D",
    )


def test_runtime_manual_backend_delegates(monkeypatch: pytest.MonkeyPatch):
    import project_dream.orchestrator_runtime as runtime

    captured: dict = {}

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        captured["seed_id"] = seed.seed_id
        captured["rounds"] = rounds
        captured["corpus"] = list(corpus)
        return {"rounds": [], "gate_logs": [], "action_logs": []}

    monkeypatch.setattr(runtime, "run_simulation", fake_run_simulation)
    payload = runtime.run_simulation_with_backend(
        seed=_seed(),
        rounds=3,
        corpus=["ctx-1"],
        backend="manual",
    )

    assert payload["rounds"] == []
    assert captured["seed_id"] == "SEED-ORCH-001"
    assert captured["rounds"] == 3
    assert captured["corpus"] == ["ctx-1"]


def test_runtime_rejects_unknown_backend():
    import project_dream.orchestrator_runtime as runtime

    with pytest.raises(ValueError):
        runtime.run_simulation_with_backend(
            seed=_seed(),
            rounds=3,
            corpus=["ctx-1"],
            backend="unknown",
        )


def test_runtime_langgraph_requires_dependency(monkeypatch: pytest.MonkeyPatch):
    import project_dream.orchestrator_runtime as runtime

    def fake_import(name: str):
        raise ImportError("missing dependency")

    monkeypatch.setattr(runtime.importlib, "import_module", fake_import)

    with pytest.raises(RuntimeError, match="langgraph"):
        runtime.run_simulation_with_backend(
            seed=_seed(),
            rounds=3,
            corpus=["ctx-1"],
            backend="langgraph",
        )


def test_runtime_langgraph_backend_delegates_when_available(monkeypatch: pytest.MonkeyPatch):
    import project_dream.orchestrator_runtime as runtime

    captured: dict = {}

    def fake_import(name: str):
        class _FakeModule:
            pass

        return _FakeModule()

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        captured["seed_id"] = seed.seed_id
        return {"rounds": [], "gate_logs": [], "action_logs": []}

    monkeypatch.setattr(runtime.importlib, "import_module", fake_import)
    monkeypatch.setattr(runtime, "run_simulation", fake_run_simulation)

    payload = runtime.run_simulation_with_backend(
        seed=_seed(),
        rounds=3,
        corpus=["ctx-1"],
        backend="langgraph",
    )

    assert payload["rounds"] == []
    assert captured["seed_id"] == "SEED-ORCH-001"
