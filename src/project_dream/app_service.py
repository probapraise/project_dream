from pathlib import Path

from project_dream.eval_suite import evaluate_run
from project_dream.infra.store import RunRepository
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.report_generator import build_report_v1
from project_dream.sim_orchestrator import run_simulation


def simulate_and_persist(
    seed: SeedInput,
    *,
    rounds: int,
    packs_dir: Path,
    repository: RunRepository,
) -> Path:
    packs = load_packs(packs_dir, enforce_phase1_minimums=True)
    sim_result = run_simulation(seed=seed, rounds=rounds, corpus=[], packs=packs)
    report = build_report_v1(seed, sim_result, packs)
    return repository.persist_run(sim_result, report)


def evaluate_and_persist(
    *,
    repository: RunRepository,
    metric_set: str = "v1",
    run_id: str | None = None,
) -> dict:
    run_dir = repository.get_run(run_id) if run_id else repository.find_latest_run()
    eval_result = evaluate_run(run_dir, metric_set=metric_set)
    repository.persist_eval(run_dir, eval_result)
    return eval_result
