import json
from datetime import UTC, datetime
from pathlib import Path

from project_dream.data_ingest import load_corpus_texts
from project_dream.eval_suite import REQUIRED_REPORT_KEYS, evaluate_run
from project_dream.kb_index import build_index, retrieve_context
from project_dream.models import SeedInput
from project_dream.orchestrator_runtime import run_simulation_with_backend
from project_dream.pack_service import load_packs
from project_dream.report_generator import build_report_v1
from project_dream.storage import persist_eval, persist_run


MODERATION_ACTIONS = {
    "HIDE_PREVIEW",
    "LOCK_THREAD",
    "GHOST_THREAD",
    "SANCTION_USER",
}


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


def _seed_files(seeds_dir: Path, max_seeds: int) -> list[Path]:
    files = sorted(seeds_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No seed files found under {seeds_dir}")
    return files[:max_seeds]


def _missing_required_sections(report: dict) -> list[str]:
    return sorted(list(REQUIRED_REPORT_KEYS - set(report.keys())))


def _has_conflict_frames(report: dict) -> bool:
    conflict = report.get("conflict_map", {})
    return bool(conflict.get("claim_a")) and bool(conflict.get("claim_b"))


def _has_moderation_hook(sim_result: dict, report: dict) -> bool:
    has_moderation = any(
        row.get("action_type") in MODERATION_ACTIONS for row in sim_result.get("action_logs", [])
    )
    return has_moderation and len(report.get("foreshadowing", [])) > 0


def _has_context_trace(eval_result: dict) -> bool:
    checks = eval_result.get("checks", [])
    for check in checks:
        if check.get("name") == "runlog.context_trace_present":
            return bool(check.get("passed"))
    return False


def _has_stage_trace(eval_result: dict) -> bool:
    checks = eval_result.get("checks", [])
    for check in checks:
        if check.get("name") == "runlog.stage_trace_present":
            return bool(check.get("passed"))
    return False


def _has_stage_trace_consistency(eval_result: dict) -> bool:
    checks = eval_result.get("checks", [])
    for check in checks:
        if check.get("name") == "runlog.stage_trace_consistency":
            return bool(check.get("passed"))
    return False


def _has_stage_trace_ordering(eval_result: dict) -> bool:
    checks = eval_result.get("checks", [])
    for check in checks:
        if check.get("name") == "runlog.stage_trace_ordering":
            return bool(check.get("passed"))
    return False


def _write_summary(output_dir: Path, summary: dict) -> Path:
    summary_dir = output_dir / "regressions"
    summary_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now(UTC).strftime("regression-%Y%m%d-%H%M%S-%f.json")
    path = summary_dir / filename
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_regression_batch(
    seeds_dir: Path,
    packs_dir: Path,
    output_dir: Path,
    corpus_dir: Path = Path("corpus"),
    rounds: int = 4,
    max_seeds: int = 10,
    metric_set: str = "v1",
    min_community_coverage: int = 2,
    min_conflict_frame_runs: int = 2,
    min_moderation_hook_runs: int = 1,
    min_validation_warning_runs: int = 1,
    orchestrator_backend: str = "manual",
) -> dict:
    packs = load_packs(packs_dir, enforce_phase1_minimums=True)
    index = build_index(packs)
    ingested_corpus = load_corpus_texts(corpus_dir)
    seed_files = _seed_files(seeds_dir, max_seeds=max_seeds)

    run_summaries: list[dict] = []
    unique_communities: set[str] = set()
    missing_required_sections_total = 0
    conflict_frame_runs = 0
    moderation_hook_runs = 0
    validation_warning_runs = 0
    context_trace_runs = 0
    stage_trace_runs = 0
    stage_trace_consistent_runs = 0
    stage_trace_ordered_runs = 0
    stage_trace_coverage_sum = 0.0
    eval_pass_runs = 0
    report_gate_pass_runs = 0

    for seed_file in seed_files:
        seed = SeedInput.model_validate_json(seed_file.read_text(encoding="utf-8"))
        context = retrieve_context(
            index,
            task=f"{seed.title} {seed.summary}",
            seed=seed.summary,
            board_id=seed.board_id,
            zone_id=seed.zone_id,
            persona_ids=[],
            top_k=3,
        )
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
        report = build_report_v1(seed, sim_result, packs)
        run_dir = persist_run(output_dir, sim_result, report)
        eval_result = evaluate_run(run_dir, metric_set=metric_set)
        persist_eval(run_dir, eval_result)

        communities = sorted(
            {row.get("community_id") for row in sim_result.get("rounds", []) if row.get("community_id")}
        )
        unique_communities.update(communities)

        missing_sections = _missing_required_sections(report)
        has_conflict = _has_conflict_frames(report)
        has_moderation_hook = _has_moderation_hook(sim_result, report)
        has_validation_warning = len(report.get("risk_checks", [])) > 0
        has_context_trace = _has_context_trace(eval_result)
        has_stage_trace = _has_stage_trace(eval_result)
        has_stage_trace_consistency = _has_stage_trace_consistency(eval_result)
        has_stage_trace_ordering = _has_stage_trace_ordering(eval_result)
        stage_trace_coverage_rate = float(eval_result.get("metrics", {}).get("stage_trace_coverage_rate", 0.0))
        report_gate = report.get("report_gate", {}) if isinstance(report, dict) else {}
        has_report_gate_pass = bool(report_gate.get("pass_fail"))

        missing_required_sections_total += len(missing_sections)
        conflict_frame_runs += int(has_conflict)
        moderation_hook_runs += int(has_moderation_hook)
        validation_warning_runs += int(has_validation_warning)
        context_trace_runs += int(has_context_trace)
        stage_trace_runs += int(has_stage_trace)
        stage_trace_consistent_runs += int(has_stage_trace_consistency)
        stage_trace_ordered_runs += int(has_stage_trace_ordering)
        stage_trace_coverage_sum += stage_trace_coverage_rate
        eval_pass_runs += int(bool(eval_result.get("pass_fail")))
        report_gate_pass_runs += int(has_report_gate_pass)

        run_summaries.append(
            {
                "seed_file": seed_file.name,
                "seed_id": seed.seed_id,
                "run_id": run_dir.name,
                "eval_pass_fail": bool(eval_result.get("pass_fail")),
                "missing_required_sections": missing_sections,
                "communities": communities,
                "has_conflict_frames": has_conflict,
                "has_moderation_hook": has_moderation_hook,
                "has_validation_warning": has_validation_warning,
                "has_context_trace": has_context_trace,
                "has_stage_trace": has_stage_trace,
                "has_stage_trace_consistency": has_stage_trace_consistency,
                "has_stage_trace_ordering": has_stage_trace_ordering,
                "stage_trace_coverage_rate": stage_trace_coverage_rate,
                "has_report_gate_pass": has_report_gate_pass,
            }
        )

    seed_runs = len(run_summaries)
    avg_stage_trace_coverage_rate = (
        float(round(stage_trace_coverage_sum / seed_runs, 4)) if seed_runs > 0 else 0.0
    )

    gates = {
        "format_missing_zero": missing_required_sections_total == 0,
        "community_coverage": len(unique_communities) >= min_community_coverage,
        "conflict_frame_runs": conflict_frame_runs >= min_conflict_frame_runs,
        "moderation_hook_runs": moderation_hook_runs >= min_moderation_hook_runs,
        "validation_warning_runs": validation_warning_runs >= min_validation_warning_runs,
        "context_trace_runs": context_trace_runs == len(run_summaries),
        "stage_trace_runs": stage_trace_runs == len(run_summaries),
        "stage_trace_consistent_runs": stage_trace_consistent_runs == len(run_summaries),
        "stage_trace_ordered_runs": stage_trace_ordered_runs == len(run_summaries),
        "stage_trace_coverage_rate": avg_stage_trace_coverage_rate >= 1.0,
        "report_gate_pass_runs": report_gate_pass_runs == len(run_summaries),
    }
    pass_fail = all(gates.values())

    summary = {
        "schema_version": "regression.v1",
        "metric_set": metric_set,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "pass_fail": pass_fail,
        "config": {
            "seeds_dir": str(seeds_dir),
            "packs_dir": str(packs_dir),
            "corpus_dir": str(corpus_dir),
            "output_dir": str(output_dir),
            "rounds": rounds,
            "max_seeds": max_seeds,
            "min_community_coverage": min_community_coverage,
            "min_conflict_frame_runs": min_conflict_frame_runs,
            "min_moderation_hook_runs": min_moderation_hook_runs,
            "min_validation_warning_runs": min_validation_warning_runs,
            "orchestrator_backend": orchestrator_backend,
        },
        "totals": {
            "seed_runs": len(run_summaries),
            "eval_pass_runs": eval_pass_runs,
            "missing_required_sections_total": missing_required_sections_total,
            "unique_communities": len(unique_communities),
            "conflict_frame_runs": conflict_frame_runs,
            "moderation_hook_runs": moderation_hook_runs,
            "validation_warning_runs": validation_warning_runs,
            "context_trace_runs": context_trace_runs,
            "stage_trace_runs": stage_trace_runs,
            "stage_trace_consistent_runs": stage_trace_consistent_runs,
            "stage_trace_ordered_runs": stage_trace_ordered_runs,
            "avg_stage_trace_coverage_rate": avg_stage_trace_coverage_rate,
            "report_gate_pass_runs": report_gate_pass_runs,
        },
        "gates": gates,
        "runs": run_summaries,
    }
    summary_path = _write_summary(output_dir, summary)
    summary["summary_path"] = str(summary_path)
    return summary
