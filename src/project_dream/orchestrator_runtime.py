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

    return run_simulation(
        seed=seed,
        rounds=rounds,
        corpus=corpus,
        max_retries=max_retries,
        packs=packs,
    )
