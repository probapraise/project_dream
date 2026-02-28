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


def _fake_sim_result() -> dict:
    return {
        "thread_candidates": [
            {"candidate_id": "TC-1", "thread_template_id": "T1", "comment_flow_id": "P1", "score": 0.9}
        ],
        "selected_thread": {"candidate_id": "TC-1", "thread_template_id": "T1", "comment_flow_id": "P1"},
        "rounds": [
            {"round": 1, "persona_id": "P1", "text": "r1"},
            {"round": 2, "persona_id": "P2", "text": "r2"},
        ],
        "gate_logs": [
            {"round": 1, "persona_id": "P1", "gates": [{"gate_name": "safety", "passed": True}]},
            {"round": 2, "persona_id": "P2", "gates": [{"gate_name": "safety", "passed": True}]},
        ],
        "action_logs": [
            {"round": 1, "action_type": "POST_COMMENT"},
            {"round": 2, "action_type": "POST_COMMENT"},
        ],
        "round_summaries": [
            {"round": 1, "participant_count": 1, "report_events": 0, "policy_events": 0, "status": "visible"},
            {"round": 2, "participant_count": 1, "report_events": 0, "policy_events": 0, "status": "visible"},
        ],
        "moderation_decisions": [
            {"round": 1, "action_type": "NO_OP", "reason_rule_id": "RULE-PLZ-UI-01"},
            {"round": 2, "action_type": "NO_OP", "reason_rule_id": "RULE-PLZ-UI-01"},
        ],
        "end_condition": {
            "termination_reason": "round_limit",
            "ended_round": 2,
            "ended_early": False,
            "status": "visible",
        },
        "thread_state": {"status": "visible", "total_reports": 0},
    }


def _fake_langgraph_graph_module():
    class _CompiledGraph:
        def __init__(self, nodes: dict[str, object]):
            self._nodes = nodes

        def invoke(self, state: dict) -> dict:
            current = dict(state)
            for node_id in ("thread_candidate", "round_loop", "moderation", "end_condition"):
                update = self._nodes[node_id](current)
                if isinstance(update, dict):
                    current.update(update)
            return current

    class _StateGraph:
        def __init__(self, _state_type):
            self._nodes: dict[str, object] = {}

        def add_node(self, node_id: str, node_fn):
            self._nodes[node_id] = node_fn

        def add_edge(self, _src, _dst):
            return None

        def compile(self):
            return _CompiledGraph(self._nodes)

    class _FakeGraphModule:
        StateGraph = _StateGraph
        START = "__start__"
        END = "__end__"

    return _FakeGraphModule()


def test_runtime_manual_backend_delegates(monkeypatch: pytest.MonkeyPatch):
    import project_dream.orchestrator_runtime as runtime

    captured: dict = {}

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        captured["seed_id"] = seed.seed_id
        captured["rounds"] = rounds
        captured["corpus"] = list(corpus)
        return _fake_sim_result()

    monkeypatch.setattr(runtime, "run_simulation", fake_run_simulation)
    payload = runtime.run_simulation_with_backend(
        seed=_seed(),
        rounds=3,
        corpus=["ctx-1"],
        backend="manual",
    )

    assert payload["rounds"]
    assert captured["seed_id"] == "SEED-ORCH-001"
    assert captured["rounds"] == 3
    assert captured["corpus"] == ["ctx-1"]
    assert payload["graph_node_trace"]["backend"] == "manual"
    node_ids = [node["node_id"] for node in payload["graph_node_trace"]["nodes"]]
    assert node_ids == ["thread_candidate", "round_loop", "moderation", "end_condition"]
    assert payload["graph_node_trace"]["nodes"][0]["event_count"] == 1
    assert payload["graph_node_trace"]["nodes"][1]["event_count"] == 2
    assert payload["graph_node_trace"]["nodes"][2]["event_count"] == 2
    assert payload["graph_node_trace"]["nodes"][3]["event_count"] == 1
    assert payload["graph_node_trace"]["execution_mode"] == "manual"


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
    imported_modules: list[str] = []

    def fake_import(name: str):
        imported_modules.append(name)
        if name == "langgraph":
            return object()
        if name == "langgraph.graph":
            return _fake_langgraph_graph_module()
        raise ImportError(name)

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        captured["seed_id"] = seed.seed_id
        return _fake_sim_result()

    monkeypatch.setattr(runtime.importlib, "import_module", fake_import)
    monkeypatch.setattr(runtime, "run_simulation", fake_run_simulation)

    payload = runtime.run_simulation_with_backend(
        seed=_seed(),
        rounds=3,
        corpus=["ctx-1"],
        backend="langgraph",
    )

    assert payload["rounds"]
    assert captured["seed_id"] == "SEED-ORCH-001"
    assert payload["graph_node_trace"]["backend"] == "langgraph"
    assert payload["graph_node_trace"]["execution_mode"] == "stategraph"
    assert "langgraph" in imported_modules
    assert "langgraph.graph" in imported_modules


def test_runtime_manual_and_langgraph_are_equivalent_except_backend(monkeypatch: pytest.MonkeyPatch):
    import project_dream.orchestrator_runtime as runtime

    def fake_import(name: str):
        if name == "langgraph":
            return object()
        if name == "langgraph.graph":
            return _fake_langgraph_graph_module()
        raise ImportError(name)

    def fake_run_simulation(*, seed, rounds, corpus, max_retries=2, packs=None):
        return _fake_sim_result()

    monkeypatch.setattr(runtime.importlib, "import_module", fake_import)
    monkeypatch.setattr(runtime, "run_simulation", fake_run_simulation)

    manual = runtime.run_simulation_with_backend(seed=_seed(), rounds=3, corpus=["ctx-1"], backend="manual")
    langgraph = runtime.run_simulation_with_backend(seed=_seed(), rounds=3, corpus=["ctx-1"], backend="langgraph")

    assert manual["thread_state"] == langgraph["thread_state"]
    assert manual["selected_thread"] == langgraph["selected_thread"]
    assert manual["end_condition"] == langgraph["end_condition"]
    assert len(manual["rounds"]) == len(langgraph["rounds"])
    assert len(manual["gate_logs"]) == len(langgraph["gate_logs"])
    assert len(manual["action_logs"]) == len(langgraph["action_logs"])

    manual_nodes = manual["graph_node_trace"]["nodes"]
    langgraph_nodes = langgraph["graph_node_trace"]["nodes"]
    assert [node["node_id"] for node in manual_nodes] == [node["node_id"] for node in langgraph_nodes]
    assert [node["event_count"] for node in manual_nodes] == [node["event_count"] for node in langgraph_nodes]
    assert manual["graph_node_trace"]["backend"] == "manual"
    assert langgraph["graph_node_trace"]["backend"] == "langgraph"
    assert manual["graph_node_trace"]["execution_mode"] == "manual"
    assert langgraph["graph_node_trace"]["execution_mode"] == "stategraph"
