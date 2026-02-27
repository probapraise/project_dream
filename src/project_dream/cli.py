import argparse
from pathlib import Path

from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.report_generator import build_report
from project_dream.sim_orchestrator import run_simulation
from project_dream.storage import persist_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-dream")
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate")
    sim.add_argument("--seed", required=True)
    sim.add_argument("--packs-dir", required=False, default="packs")
    sim.add_argument("--output-dir", required=False, default="runs")
    sim.add_argument("--rounds", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "simulate":
        seed_path = Path(args.seed)
        seed = SeedInput.model_validate_json(seed_path.read_text(encoding="utf-8"))
        packs = load_packs(Path(args.packs_dir), enforce_phase1_minimums=True)
        sim_result = run_simulation(seed=seed, rounds=args.rounds, corpus=[], packs=packs)
        report = build_report(seed, sim_result)
        persist_run(Path(args.output_dir), sim_result, report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
