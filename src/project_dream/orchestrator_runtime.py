import importlib

from project_dream.sim_orchestrator import (
    SIMULATION_STAGE_NODE_ORDER,
    assemble_sim_result_from_stage_payloads,
    extract_stage_payloads,
    run_simulation,
)


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


def _load_langgraph_primitives() -> tuple[type, object, object]:
    try:
        graph_module = importlib.import_module("langgraph.graph")
    except ImportError as exc:
        raise RuntimeError(
            "LangGraph backend requires 'langgraph.graph' with StateGraph/START/END."
        ) from exc

    missing = [name for name in ("StateGraph", "START", "END") if not hasattr(graph_module, name)]
    if missing:
        raise RuntimeError(
            "LangGraph backend requires langgraph.graph StateGraph API "
            f"(missing: {', '.join(missing)})."
        )

    return graph_module.StateGraph, graph_module.START, graph_module.END


def _run_langgraph_stage_pipeline(stage_payloads: dict[str, dict]) -> tuple[list[str], dict[str, dict]]:
    StateGraph, START, END = _load_langgraph_primitives()

    graph = StateGraph(dict)

    for node_id in SIMULATION_STAGE_NODE_ORDER:
        stage_payload = stage_payloads[node_id]

        def _node(state: dict, *, _node_id: str = node_id, _stage_payload: dict = stage_payload) -> dict:
            executed = list(state.get("executed_nodes", []))
            executed.append(_node_id)
            return {
                "executed_nodes": executed,
                _node_id: dict(_stage_payload),
            }

        graph.add_node(node_id, _node)

    graph.add_edge(START, SIMULATION_STAGE_NODE_ORDER[0])
    for src, dst in zip(SIMULATION_STAGE_NODE_ORDER, SIMULATION_STAGE_NODE_ORDER[1:]):
        graph.add_edge(src, dst)
    graph.add_edge(SIMULATION_STAGE_NODE_ORDER[-1], END)

    compiled = graph.compile()
    final_state = compiled.invoke({"executed_nodes": []})
    executed_nodes = list(final_state.get("executed_nodes", []))
    resolved_payloads: dict[str, dict] = {}
    for node_id in SIMULATION_STAGE_NODE_ORDER:
        node_payload = final_state.get(node_id, stage_payloads[node_id])
        resolved_payloads[node_id] = dict(node_payload) if isinstance(node_payload, dict) else {}
    return executed_nodes, resolved_payloads


def _graph_node_trace_template(
    sim_result: dict,
    *,
    backend: str,
    execution_mode: str,
    executed_nodes: list[str] | None = None,
) -> dict:
    thread_candidate_count = len(sim_result.get("thread_candidates", []))
    round_loop_count = len(sim_result.get("round_summaries", []))
    if round_loop_count <= 0:
        round_loop_count = len(sim_result.get("rounds", []))
    moderation_count = len(sim_result.get("moderation_decisions", []))
    end_condition_count = 1 if sim_result.get("end_condition") is not None else 0

    return {
        "schema_version": "graph_node_trace.v1",
        "backend": backend,
        "execution_mode": execution_mode,
        "node_order": list(SIMULATION_STAGE_NODE_ORDER),
        "executed_nodes": list(executed_nodes or []),
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
    raw_result = run_simulation(
        seed=seed,
        rounds=rounds,
        corpus=corpus,
        max_retries=max_retries,
        packs=packs,
    )
    stage_payloads = extract_stage_payloads(raw_result)

    if selected == "langgraph":
        _ensure_langgraph_available()
        executed_nodes, resolved_payloads = _run_langgraph_stage_pipeline(stage_payloads)
        execution_mode = "stategraph"
    else:
        resolved_payloads = stage_payloads
        executed_nodes = list(SIMULATION_STAGE_NODE_ORDER)
        execution_mode = "manual"

    sim_result = assemble_sim_result_from_stage_payloads(resolved_payloads)
    for key, value in raw_result.items():
        if key not in sim_result:
            sim_result[key] = value

    sim_result["graph_node_trace"] = _graph_node_trace_template(
        sim_result,
        backend=selected,
        execution_mode=execution_mode,
        executed_nodes=executed_nodes,
    )
    return sim_result
