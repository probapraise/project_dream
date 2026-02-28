import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from project_dream.app_service import evaluate_and_persist, simulate_and_persist
from project_dream.data_ingest import build_corpus_from_packs
from project_dream.eval_export import export_external_eval_bundle
from project_dream.infra.http_server import serve
from project_dream.infra.store import FileRunRepository
from project_dream.infra.web_api import ProjectDreamAPI
from project_dream.models import SeedInput
from project_dream.regression_runner import run_regression_batch


def _emit_http_access_log(entry: dict) -> None:
    print(json.dumps(entry, ensure_ascii=False), file=sys.stderr, flush=True)


@contextmanager
def _temporary_env(overrides: dict[str, str]) -> None:
    previous: dict[str, str | None] = {}
    for key, value in overrides.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _build_regress_live_metrics(summary: dict) -> dict[str, float | int]:
    totals = summary.get("totals", {})
    seed_runs = int(totals.get("seed_runs", 0))
    eval_pass_runs = int(totals.get("eval_pass_runs", 0))
    conflict_frame_runs = int(totals.get("conflict_frame_runs", 0))
    moderation_hook_runs = int(totals.get("moderation_hook_runs", 0))
    validation_warning_runs = int(totals.get("validation_warning_runs", 0))
    unique_communities = int(totals.get("unique_communities", 0))
    avg_stage_trace_coverage_rate = float(totals.get("avg_stage_trace_coverage_rate", 0.0))

    return {
        "seed_runs": seed_runs,
        "eval_pass_rate": _ratio(eval_pass_runs, seed_runs),
        "conflict_frame_rate": _ratio(conflict_frame_runs, seed_runs),
        "moderation_hook_rate": _ratio(moderation_hook_runs, seed_runs),
        "validation_warning_rate": _ratio(validation_warning_runs, seed_runs),
        "unique_communities": unique_communities,
        "avg_stage_trace_coverage_rate": avg_stage_trace_coverage_rate,
    }


def _load_json_or_none(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_regress_live_baseline(
    path: Path,
    *,
    summary: dict,
    llm_model: str,
    metrics: dict[str, float | int],
) -> None:
    payload = {
        "schema_version": "regress_live_baseline.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "llm_model": llm_model,
        "metric_set": summary.get("metric_set"),
        "metrics": metrics,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _compare_regress_live_baseline(
    *,
    current_metrics: dict[str, float | int],
    baseline_metrics: dict[str, float | int],
    allowed_rate_drop: float,
    allowed_community_drop: int,
) -> list[str]:
    failures: list[str] = []
    rate_keys = [
        "eval_pass_rate",
        "conflict_frame_rate",
        "moderation_hook_rate",
        "validation_warning_rate",
        "avg_stage_trace_coverage_rate",
    ]

    for key in rate_keys:
        current = float(current_metrics.get(key, 0.0))
        baseline = float(baseline_metrics.get(key, 0.0))
        if current < (baseline - allowed_rate_drop):
            failures.append(
                f"{key}: current={current:.4f} baseline={baseline:.4f} allowed_drop={allowed_rate_drop:.4f}"
            )

    current_unique = int(current_metrics.get("unique_communities", 0))
    baseline_unique = int(baseline_metrics.get("unique_communities", 0))
    if current_unique < (baseline_unique - allowed_community_drop):
        failures.append(
            f"unique_communities: current={current_unique} baseline={baseline_unique} "
            f"allowed_drop={allowed_community_drop}"
        )
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-dream")
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate")
    sim.add_argument("--seed", required=True)
    sim.add_argument("--packs-dir", required=False, default="packs")
    sim.add_argument("--corpus-dir", required=False, default="corpus")
    sim.add_argument("--output-dir", required=False, default="runs")
    sim.add_argument("--rounds", type=int, default=3)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("--packs-dir", required=False, default="packs")
    ingest.add_argument("--corpus-dir", required=False, default="corpus")

    eva = sub.add_parser("evaluate")
    eva.add_argument("--runs-dir", required=False, default="runs")
    eva.add_argument("--run-id", required=False, default=None)
    eva.add_argument("--metric-set", required=False, default="v1")

    eva_export = sub.add_parser("eval-export")
    eva_export.add_argument("--runs-dir", required=False, default="runs")
    eva_export.add_argument("--run-id", required=False, default=None)
    eva_export.add_argument("--output-dir", required=False, default=None)
    eva_export.add_argument("--max-contexts", type=int, default=5)

    reg = sub.add_parser("regress")
    reg.add_argument("--seeds-dir", required=False, default="examples/seeds/regression")
    reg.add_argument("--packs-dir", required=False, default="packs")
    reg.add_argument("--corpus-dir", required=False, default="corpus")
    reg.add_argument("--output-dir", required=False, default="runs")
    reg.add_argument("--rounds", type=int, default=4)
    reg.add_argument("--max-seeds", type=int, default=10)
    reg.add_argument("--metric-set", required=False, default="v1")
    reg.add_argument("--min-community-coverage", type=int, default=2)
    reg.add_argument("--min-conflict-frame-runs", type=int, default=2)
    reg.add_argument("--min-moderation-hook-runs", type=int, default=1)
    reg.add_argument("--min-validation-warning-runs", type=int, default=1)

    reg_live = sub.add_parser("regress-live")
    reg_live.add_argument("--seeds-dir", required=False, default="examples/seeds/regression")
    reg_live.add_argument("--packs-dir", required=False, default="packs")
    reg_live.add_argument("--corpus-dir", required=False, default="corpus")
    reg_live.add_argument("--output-dir", required=False, default="runs")
    reg_live.add_argument("--rounds", type=int, default=3)
    reg_live.add_argument("--max-seeds", type=int, default=2)
    reg_live.add_argument("--metric-set", required=False, default="v2")
    reg_live.add_argument("--min-community-coverage", type=int, default=1)
    reg_live.add_argument("--min-conflict-frame-runs", type=int, default=0)
    reg_live.add_argument("--min-moderation-hook-runs", type=int, default=0)
    reg_live.add_argument("--min-validation-warning-runs", type=int, default=0)
    reg_live.add_argument("--llm-model", required=False, default="gemini-3.1-flash")
    reg_live.add_argument("--llm-timeout-sec", type=int, default=60)
    reg_live.add_argument(
        "--baseline-file",
        required=False,
        default="runs/regressions/regress-live-baseline.json",
    )
    reg_live.add_argument("--update-baseline", action="store_true")
    reg_live.add_argument("--allowed-rate-drop", type=float, default=0.05)
    reg_live.add_argument("--allowed-community-drop", type=int, default=1)

    srv = sub.add_parser("serve")
    srv.add_argument("--host", required=False, default="127.0.0.1")
    srv.add_argument("--port", required=False, type=int, default=8000)
    srv.add_argument("--runs-dir", required=False, default="runs")
    srv.add_argument("--packs-dir", required=False, default="packs")
    srv.add_argument("--api-token", required=False, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "simulate":
        seed_path = Path(args.seed)
        seed = SeedInput.model_validate_json(seed_path.read_text(encoding="utf-8"))
        repository = FileRunRepository(Path(args.output_dir))
        simulate_and_persist(
            seed,
            rounds=args.rounds,
            packs_dir=Path(args.packs_dir),
            corpus_dir=Path(args.corpus_dir),
            repository=repository,
        )
    elif args.command == "ingest":
        summary = build_corpus_from_packs(
            packs_dir=Path(args.packs_dir),
            corpus_dir=Path(args.corpus_dir),
        )
        print(json.dumps(summary, ensure_ascii=False))
    elif args.command == "evaluate":
        repository = FileRunRepository(Path(args.runs_dir))
        evaluate_and_persist(
            repository=repository,
            run_id=args.run_id,
            metric_set=args.metric_set,
        )
    elif args.command == "eval-export":
        repository = FileRunRepository(Path(args.runs_dir))
        run_dir = repository.get_run(args.run_id) if args.run_id else repository.find_latest_run()
        output_dir = Path(args.output_dir) if args.output_dir else None
        manifest = export_external_eval_bundle(
            run_dir,
            output_dir=output_dir,
            max_contexts=args.max_contexts,
        )
        print(json.dumps(manifest, ensure_ascii=False))
    elif args.command == "regress":
        summary = run_regression_batch(
            seeds_dir=Path(args.seeds_dir),
            packs_dir=Path(args.packs_dir),
            corpus_dir=Path(args.corpus_dir),
            output_dir=Path(args.output_dir),
            rounds=args.rounds,
            max_seeds=args.max_seeds,
            metric_set=args.metric_set,
            min_community_coverage=args.min_community_coverage,
            min_conflict_frame_runs=args.min_conflict_frame_runs,
            min_moderation_hook_runs=args.min_moderation_hook_runs,
            min_validation_warning_runs=args.min_validation_warning_runs,
        )
        return 0 if summary["pass_fail"] else 2
    elif args.command == "regress-live":
        baseline_path = Path(args.baseline_file)
        with _temporary_env(
            {
                "PROJECT_DREAM_LLM_PROVIDER": "google",
                "PROJECT_DREAM_LLM_MODEL": args.llm_model,
                "PROJECT_DREAM_LLM_RESPONSE_MODE": "model_output",
                "PROJECT_DREAM_LLM_TIMEOUT_SEC": str(args.llm_timeout_sec),
            }
        ):
            summary = run_regression_batch(
                seeds_dir=Path(args.seeds_dir),
                packs_dir=Path(args.packs_dir),
                corpus_dir=Path(args.corpus_dir),
                output_dir=Path(args.output_dir),
                rounds=args.rounds,
                max_seeds=args.max_seeds,
                metric_set=args.metric_set,
                min_community_coverage=args.min_community_coverage,
                min_conflict_frame_runs=args.min_conflict_frame_runs,
                min_moderation_hook_runs=args.min_moderation_hook_runs,
                min_validation_warning_runs=args.min_validation_warning_runs,
            )
        if not summary["pass_fail"]:
            return 2

        current_metrics = _build_regress_live_metrics(summary)
        if args.update_baseline:
            _write_regress_live_baseline(
                baseline_path,
                summary=summary,
                llm_model=args.llm_model,
                metrics=current_metrics,
            )
            print(
                f"[regress-live] baseline updated: {baseline_path}",
                file=sys.stderr,
            )
            return 0

        baseline_payload = _load_json_or_none(baseline_path)
        if baseline_payload is None:
            print(
                f"[regress-live] baseline not found, skip compare: {baseline_path}",
                file=sys.stderr,
            )
            return 0

        baseline_metrics = baseline_payload.get("metrics", {})
        failures = _compare_regress_live_baseline(
            current_metrics=current_metrics,
            baseline_metrics=baseline_metrics,
            allowed_rate_drop=args.allowed_rate_drop,
            allowed_community_drop=args.allowed_community_drop,
        )
        if failures:
            print("[regress-live] quality regression detected:", file=sys.stderr)
            for row in failures:
                print(f"  - {row}", file=sys.stderr)
            return 3
        return 0
    elif args.command == "serve":
        api_token = args.api_token or os.environ.get("PROJECT_DREAM_API_TOKEN")
        if not api_token:
            parser.error("serve requires --api-token or PROJECT_DREAM_API_TOKEN")

        api = ProjectDreamAPI.for_local_filesystem(
            runs_dir=Path(args.runs_dir),
            packs_dir=Path(args.packs_dir),
        )
        try:
            serve(
                api=api,
                host=args.host,
                port=args.port,
                api_token=api_token,
                request_logger=_emit_http_access_log,
            )
        except KeyboardInterrupt:
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
