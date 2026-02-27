import argparse
from pathlib import Path

from project_dream.eval_suite import evaluate_run, find_latest_run
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.regression_runner import run_regression_batch
from project_dream.report_generator import build_report_v1
from project_dream.sim_orchestrator import run_simulation
from project_dream.storage import persist_eval, persist_run


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "simulate":
        seed_path = Path(args.seed)
        seed = SeedInput.model_validate_json(seed_path.read_text(encoding="utf-8"))
        packs = load_packs(Path(args.packs_dir), enforce_phase1_minimums=True)
        sim_result = run_simulation(seed=seed, rounds=args.rounds, corpus=[], packs=packs)
        report = build_report_v1(seed, sim_result, packs)
        persist_run(Path(args.output_dir), sim_result, report)
    elif args.command == "evaluate":
        runs_dir = Path(args.runs_dir)
        run_dir = runs_dir / args.run_id if args.run_id else find_latest_run(runs_dir)
        eval_result = evaluate_run(run_dir, metric_set=args.metric_set)
        persist_eval(run_dir, eval_result)
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
