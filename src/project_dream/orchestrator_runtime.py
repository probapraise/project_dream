import importlib

from project_dream.sim_orchestrator import run_simulation


_SUPPORTED_ORCHESTRATOR_BACKENDS = {"manual", "langgraph"}


def _normalize_backend(backend: str) -> str:
    name = str(backend).strip().lower()
    if name not in _SUPPORTED_ORCHESTRATOR_BACKENDS:
        allowed = ", ".join(sorted(_SUPPORTED_ORCHESTRATOR_BACKENDS))
        raise ValueError(f"Unknown orchestrator backend: {backend} (allowed: {allowed})")
    return name


def _ensure_langgraph_available() -> None:
    try:
        importlib.import_module("langgraph")
    except ImportError as exc:
        raise RuntimeError(
            "LangGraph backend requires the 'langgraph' package. Install with `pip install langgraph`."
        ) from exc


def _graph_node_trace_template(sim_result: dict, *, backend: str) -> dict:
    thread_candidate_count = len(sim_result.get("thread_candidates", []))
    round_loop_count = len(sim_result.get("round_summaries", []))
    if round_loop_count <= 0:
        round_loop_count = len(sim_result.get("rounds", []))
    moderation_count = len(sim_result.get("moderation_decisions", []))
    end_condition_count = 1 if sim_result.get("end_condition") is not None else 0

    return {
        "schema_version": "graph_node_trace.v1",
        "backend": backend,
        "nodes": [
            {
                "node_id": "thread_candidate",
                "event_type": "thread_candidate",
                "event_count": thread_candidate_count,
            },
            {
                "node_id": "round_loop",
                "event_type": "round_summary",
                "event_count": round_loop_count,
            },
            {
                "node_id": "moderation",
                "event_type": "moderation_decision",
                "event_count": moderation_count,
            },
            {
                "node_id": "end_condition",
                "event_type": "end_condition",
                "event_count": end_condition_count,
            },
        ],
    }


def run_simulation_with_backend(
    *,
    seed,
    rounds: int,
    corpus: list[str],
    max_retries: int = 2,
    packs=None,
    backend: str = "manual",
) -> dict:
    selected = _normalize_backend(backend)
    if selected == "langgraph":
        _ensure_langgraph_available()

    sim_result = run_simulation(
        seed=seed,
        rounds=rounds,
        corpus=corpus,
        max_retries=max_retries,
        packs=packs,
    )
    sim_result["graph_node_trace"] = _graph_node_trace_template(sim_result, backend=selected)
    return sim_result
