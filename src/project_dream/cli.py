import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from project_dream.app_service import evaluate_and_persist, simulate_and_persist
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-dream")
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate")
    sim.add_argument("--seed", required=True)
    sim.add_argument("--packs-dir", required=False, default="packs")
    sim.add_argument("--output-dir", required=False, default="runs")
    sim.add_argument("--rounds", type=int, default=3)

    eva = sub.add_parser("evaluate")
    eva.add_argument("--runs-dir", required=False, default="runs")
    eva.add_argument("--run-id", required=False, default=None)
    eva.add_argument("--metric-set", required=False, default="v1")

    reg = sub.add_parser("regress")
    reg.add_argument("--seeds-dir", required=False, default="examples/seeds/regression")
    reg.add_argument("--packs-dir", required=False, default="packs")
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
            repository=repository,
        )
    elif args.command == "evaluate":
        repository = FileRunRepository(Path(args.runs_dir))
        evaluate_and_persist(
            repository=repository,
            run_id=args.run_id,
            metric_set=args.metric_set,
        )
    elif args.command == "regress":
        summary = run_regression_batch(
            seeds_dir=Path(args.seeds_dir),
            packs_dir=Path(args.packs_dir),
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
