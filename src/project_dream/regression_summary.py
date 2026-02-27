import argparse
import json
from pathlib import Path


def find_latest_regression_summary(regressions_dir: Path) -> Path | None:
    candidates = sorted(regressions_dir.glob("regression-*.json"))
    if not candidates:
        return None
    return candidates[-1]


def render_summary_markdown(summary: dict) -> str:
    gates = summary.get("gates", {})
    totals = summary.get("totals", {})
    pass_fail = bool(summary.get("pass_fail"))
    status = "PASS" if pass_fail else "FAIL"
    metric_set = summary.get("metric_set", "unknown")
    summary_path = summary.get("summary_path", "")

    lines = [
        "## Regression Gate Summary",
        "",
        f"- status: **{status}**",
        f"- metric_set: `{metric_set}`",
        "",
        "### Totals",
        f"- seed_runs: `{totals.get('seed_runs', 0)}`",
        f"- eval_pass_runs: `{totals.get('eval_pass_runs', 0)}`",
        f"- unique_communities: `{totals.get('unique_communities', 0)}`",
        "",
        "### Gates",
    ]

    for key in sorted(gates.keys()):
        icon = "PASS" if gates.get(key) else "FAIL"
        lines.append(f"- `{key}`: **{icon}**")

    if summary_path:
        lines.extend(["", f"- summary_path: `{summary_path}`"])
    lines.append("")
    return "\n".join(lines)


def render_missing_summary_markdown() -> str:
    return "\n".join(
        [
            "## Regression Gate Summary",
            "",
            "- status: **UNKNOWN**",
            "- No regression summary found under `runs/regressions`.",
            "",
        ]
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_job_summary(regressions_dir: Path, output_file: Path) -> None:
    latest = find_latest_regression_summary(regressions_dir)
    if latest is None:
        content = render_missing_summary_markdown()
    else:
        summary = _load_json(latest)
        summary.setdefault("summary_path", str(latest))
        content = render_summary_markdown(summary)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-dream-regression-summary")
    parser.add_argument("--regressions-dir", required=False, default="runs/regressions")
    parser.add_argument("--output-file", required=False, default="runs/regressions/job-summary.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    write_job_summary(Path(args.regressions_dir), Path(args.output_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
