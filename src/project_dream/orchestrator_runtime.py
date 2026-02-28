import importlib
from typing import Callable

from project_dream.sim_orchestrator import (
    SIMULATION_STAGE_NODE_ORDER,
    assemble_sim_result_from_stage_payloads,
    extract_stage_payloads,
    run_stage_node_end_condition,
    run_stage_node_moderation,
    run_stage_node_round_loop,
    run_stage_node_thread_candidate,
    run_simulation,
)


_SUPPORTED_ORCHESTRATOR_BACKENDS = {"manual", "langgraph"}


class StageNodeExecutionError(RuntimeError):
    def __init__(self, *, node_id: str, attempts: int, cause: Exception):
        self.node_id = str(node_id)
        self.attempts = max(1, int(attempts))
        self.cause = cause
        message = (
            f"Stage node '{self.node_id}' failed after {self.attempts} attempt(s): {cause}"
        )
        super().__init__(message)


def _coerce_stage_payload(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}
    return dict(payload)


def _run_stage_node_thread_candidate(stage_payload: dict) -> dict:
    return _coerce_stage_payload(run_stage_node_thread_candidate(stage_payload))


def _run_stage_node_round_loop(stage_payload: dict) -> dict:
    return _coerce_stage_payload(run_stage_node_round_loop(stage_payload))


def _run_stage_node_moderation(stage_payload: dict) -> dict:
    return _coerce_stage_payload(run_stage_node_moderation(stage_payload))


def _run_stage_node_end_condition(stage_payload: dict) -> dict:
    return _coerce_stage_payload(run_stage_node_end_condition(stage_payload))


def _resolve_stage_node_handler(node_id: str) -> Callable[[dict], dict]:
    handlers: dict[str, Callable[[dict], dict]] = {
        "thread_candidate": _run_stage_node_thread_candidate,
        "round_loop": _run_stage_node_round_loop,
        "moderation": _run_stage_node_moderation,
        "end_condition": _run_stage_node_end_condition,
    }
    if node_id not in handlers:
        allowed = ", ".join(sorted(handlers))
        raise RuntimeError(f"Unknown stage node id: {node_id} (allowed: {allowed})")
    return handlers[node_id]


def _run_stage_node_with_retry(
    *,
    node_id: str,
    stage_payload: dict,
    max_stage_retries: int,
    checkpoint_log: list[dict],
) -> tuple[dict, int]:
    stage_node_handler = _resolve_stage_node_handler(node_id)
    retry_budget = max(0, int(max_stage_retries))
    max_attempts = retry_budget + 1

    for attempt in range(1, max_attempts + 1):
        try:
            resolved_payload = _coerce_stage_payload(stage_node_handler(_coerce_stage_payload(stage_payload)))
        except Exception as exc:
            is_last_attempt = attempt >= max_attempts
            checkpoint_log.append(
                {
                    "node_id": node_id,
                    "attempt": attempt,
                    "outcome": "failed" if is_last_attempt else "retry",
                    "error": str(exc),
                }
            )
            if is_last_attempt:
                raise StageNodeExecutionError(
                    node_id=node_id,
                    attempts=attempt,
                    cause=exc,
                ) from exc
            continue

        checkpoint_log.append(
            {
                "node_id": node_id,
                "attempt": attempt,
                "outcome": "success",
            }
        )
        return resolved_payload, attempt

    raise RuntimeError(f"Stage node '{node_id}' failed before execution.")


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


def _run_manual_stage_pipeline(
    stage_payloads: dict[str, dict],
    *,
    max_stage_retries: int = 0,
) -> tuple[list[str], dict[str, dict], dict[str, int], list[dict]]:
    executed_nodes: list[str] = []
    resolved_payloads: dict[str, dict] = {}
    node_attempts: dict[str, int] = {}
    checkpoint_log: list[dict] = []
    for node_id in SIMULATION_STAGE_NODE_ORDER:
        stage_payload = _coerce_stage_payload(stage_payloads.get(node_id))
        resolved_payload, attempt_count = _run_stage_node_with_retry(
            node_id=node_id,
            stage_payload=stage_payload,
            max_stage_retries=max_stage_retries,
            checkpoint_log=checkpoint_log,
        )
        resolved_payloads[node_id] = resolved_payload
        node_attempts[node_id] = attempt_count
        executed_nodes.append(node_id)
    return executed_nodes, resolved_payloads, node_attempts, checkpoint_log


def _run_langgraph_stage_pipeline(
    stage_payloads: dict[str, dict],
    *,
    max_stage_retries: int = 0,
) -> tuple[list[str], dict[str, dict], dict[str, int], list[dict]]:
    StateGraph, START, END = _load_langgraph_primitives()

    graph = StateGraph(dict)
    node_attempts: dict[str, int] = {}
    checkpoint_log: list[dict] = []

    for node_id in SIMULATION_STAGE_NODE_ORDER:
        stage_payload = _coerce_stage_payload(stage_payloads.get(node_id))

        def _node(
            state: dict,
            *,
            _node_id: str = node_id,
            _stage_payload: dict = stage_payload,
        ) -> dict:
            executed = list(state.get("executed_nodes", []))
            executed.append(_node_id)
            resolved_payload, attempt_count = _run_stage_node_with_retry(
                node_id=_node_id,
                stage_payload=_stage_payload,
                max_stage_retries=max_stage_retries,
                checkpoint_log=checkpoint_log,
            )
            node_attempts[_node_id] = attempt_count
            return {
                "executed_nodes": executed,
                _node_id: resolved_payload,
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
        node_payload = final_state.get(node_id, stage_payloads.get(node_id, {}))
        resolved_payloads[node_id] = _coerce_stage_payload(node_payload)
    return executed_nodes, resolved_payloads, node_attempts, checkpoint_log


def _graph_node_trace_template(
    sim_result: dict,
    *,
    backend: str,
    execution_mode: str,
    executed_nodes: list[str] | None = None,
    node_attempts: dict[str, int] | None = None,
    stage_checkpoints: list[dict] | None = None,
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
        "node_attempts": dict(node_attempts or {}),
        "stage_checkpoints": [dict(entry) for entry in (stage_checkpoints or [])],
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
    max_stage_retries: int = 0,
    packs=None,
    backend: str = "manual",
) -> dict:
    selected = _normalize_backend(backend)
    stage_retry_budget = max(0, int(max_stage_retries))
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
        executed_nodes, resolved_payloads, node_attempts, stage_checkpoints = _run_langgraph_stage_pipeline(
            stage_payloads,
            max_stage_retries=stage_retry_budget,
        )
        execution_mode = "stategraph"
    else:
        executed_nodes, resolved_payloads, node_attempts, stage_checkpoints = _run_manual_stage_pipeline(
            stage_payloads,
            max_stage_retries=stage_retry_budget,
        )
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
        node_attempts=node_attempts,
        stage_checkpoints=stage_checkpoints,
    )
    return sim_result
