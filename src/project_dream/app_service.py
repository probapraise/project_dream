from pathlib import Path

from project_dream.data_ingest import load_corpus_texts
from project_dream.eval_suite import evaluate_run
from project_dream.infra.store import RunRepository
from project_dream.kb_index import build_index, retrieve_context
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.orchestrator_runtime import run_simulation_with_backend
from project_dream.regression_runner import run_regression_batch
from project_dream.report_generator import build_report_v1


def _merge_unique_corpus(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for rows in groups:
        for raw in rows:
            text = str(raw).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
    return merged


def simulate_and_persist(
    seed: SeedInput,
    *,
    rounds: int,
    packs_dir: Path,
    repository: RunRepository,
    corpus_dir: Path = Path("corpus"),
    orchestrator_backend: str = "manual",
    vector_backend: str = "memory",
    vector_db_path: Path | None = None,
) -> Path:
    packs = load_packs(packs_dir, enforce_phase1_minimums=True)
    index = build_index(
        packs,
        vector_backend=vector_backend,
        vector_db_path=vector_db_path,
    )
    context = retrieve_context(
        index,
        task=f"{seed.title} {seed.summary}",
        seed=seed.summary,
        board_id=seed.board_id,
        zone_id=seed.zone_id,
        persona_ids=[],
        top_k=3,
    )
    ingested_corpus = load_corpus_texts(corpus_dir)
    merged_corpus = _merge_unique_corpus(context["corpus"], ingested_corpus)
    sim_result = run_simulation_with_backend(
        seed=seed,
        rounds=rounds,
        corpus=merged_corpus,
        packs=packs,
        backend=orchestrator_backend,
    )
    sim_result["orchestrator_backend"] = orchestrator_backend
    sim_result["context_bundle"] = context["bundle"]
    sim_result["context_corpus"] = merged_corpus
    sim_result["seed"] = seed.model_dump()
    sim_result["pack_manifest"] = packs.pack_manifest
    sim_result["pack_fingerprint"] = packs.pack_fingerprint
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


def regress_and_persist(
    *,
    repository: RunRepository,
    packs_dir: Path,
    corpus_dir: Path = Path("corpus"),
    seeds_dir: Path = Path("examples/seeds/regression"),
    rounds: int = 4,
    max_seeds: int = 10,
    metric_set: str = "v1",
    min_community_coverage: int = 2,
    min_conflict_frame_runs: int = 2,
    min_moderation_hook_runs: int = 1,
    min_validation_warning_runs: int = 1,
    orchestrator_backend: str = "manual",
    vector_backend: str = "memory",
    vector_db_path: Path | None = None,
) -> dict:
    summary = run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=packs_dir,
        corpus_dir=corpus_dir,
        output_dir=repository.runs_dir,
        rounds=rounds,
        max_seeds=max_seeds,
        metric_set=metric_set,
        min_community_coverage=min_community_coverage,
        min_conflict_frame_runs=min_conflict_frame_runs,
        min_moderation_hook_runs=min_moderation_hook_runs,
        min_validation_warning_runs=min_validation_warning_runs,
        orchestrator_backend=orchestrator_backend,
        vector_backend=vector_backend,
        vector_db_path=vector_db_path,
    )
    repository.persist_regression_summary(summary)
    return summary
