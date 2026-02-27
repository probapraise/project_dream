import json
from pathlib import Path

from project_dream.models import EvalCheck, EvalResult


REQUIRED_REPORT_KEYS = {
    "schema_version",
    "seed_id",
    "title",
    "summary",
    "lens_summaries",
    "highlights_top10",
    "conflict_map",
    "dialogue_candidates",
    "foreshadowing",
    "risk_checks",
}


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def evaluate_run(run_dir: Path) -> dict:
    report = _safe_read_json(run_dir / "report.json")
    runlog_rows = _safe_read_jsonl(run_dir / "runlog.jsonl")

    checks: list[EvalCheck] = []

    event_types = {row.get("type") for row in runlog_rows}
    has_required_event_types = {"round", "gate", "action"}.issubset(event_types)
    checks.append(
        EvalCheck(
            name="runlog.required_event_types",
            passed=has_required_event_types,
            details=f"event_types={sorted([t for t in event_types if t])}",
        )
    )

    checks.append(
        EvalCheck(
            name="report.schema_version",
            passed=report.get("schema_version") == "report.v1",
            details=f"schema_version={report.get('schema_version')}",
        )
    )

    missing_keys = sorted(list(REQUIRED_REPORT_KEYS - set(report.keys())))
    checks.append(
        EvalCheck(
            name="report.required_sections",
            passed=len(missing_keys) == 0,
            details=f"missing={missing_keys}",
        )
    )

    lens_count = len(report.get("lens_summaries", []))
    checks.append(
        EvalCheck(
            name="report.lens_count",
            passed=lens_count == 4,
            details=f"lens_count={lens_count}",
        )
    )

    dialogue_count = len(report.get("dialogue_candidates", []))
    checks.append(
        EvalCheck(
            name="report.dialogue_count",
            passed=3 <= dialogue_count <= 5,
            details=f"dialogue_count={dialogue_count}",
        )
    )

    highlight_count = len(report.get("highlights_top10", []))
    checks.append(
        EvalCheck(
            name="report.highlights_count",
            passed=1 <= highlight_count <= 10,
            details=f"highlight_count={highlight_count}",
        )
    )

    pass_fail = all(check.passed for check in checks)
    result = EvalResult(
        run_id=run_dir.name,
        seed_id=str(report.get("seed_id", "unknown")),
        pass_fail=pass_fail,
        checks=checks,
        metrics={
            "runlog_rows": len(runlog_rows),
            "round_rows": sum(1 for row in runlog_rows if row.get("type") == "round"),
            "gate_rows": sum(1 for row in runlog_rows if row.get("type") == "gate"),
            "action_rows": sum(1 for row in runlog_rows if row.get("type") == "action"),
            "highlight_count": highlight_count,
            "dialogue_count": dialogue_count,
            "lens_count": lens_count,
        },
    )
    return result.model_dump()


def find_latest_run(runs_dir: Path) -> Path:
    candidates = sorted([p for p in runs_dir.glob("run-*") if p.is_dir()], key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No run directories found under {runs_dir}")
    return candidates[-1]
