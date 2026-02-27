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
VALID_RISK_SEVERITIES = {"low", "medium", "high"}


def _quality_metrics_v1(runlog_rows: list[dict], report: dict) -> dict[str, float]:
    round_rows = [row for row in runlog_rows if row.get("type") == "round"]
    gate_rows = [row for row in runlog_rows if row.get("type") == "gate"]
    action_rows = [row for row in runlog_rows if row.get("type") == "action"]

    moderation_actions = {
        "HIDE_PREVIEW",
        "LOCK_THREAD",
        "GHOST_THREAD",
        "SANCTION_USER",
    }
    moderation_count = sum(1 for row in action_rows if row.get("action_type") in moderation_actions)
    intervention_rate = moderation_count / max(1, len(round_rows))

    total_gate_checks = 0
    failed_gate_checks = 0
    for row in gate_rows:
        gates = row.get("gates", [])
        total_gate_checks += len(gates)
        failed_gate_checks += sum(1 for gate in gates if not gate.get("passed"))
    gate_rewrite_rate = failed_gate_checks / max(1, total_gate_checks)

    communities = [row.get("community_id") for row in round_rows if row.get("community_id")]
    unique_communities = len(set(communities))
    # Phase1 packs define 4 communities.
    community_dispersion = unique_communities / 4.0
    if community_dispersion > 1.0:
        community_dispersion = 1.0

    return {
        "moderation_intervention_rate": float(round(intervention_rate, 4)),
        "gate_rewrite_rate": float(round(gate_rewrite_rate, 4)),
        "community_dispersion": float(round(community_dispersion, 4)),
    }


def _quality_metrics_v2(runlog_rows: list[dict], report: dict) -> dict[str, float]:
    metrics = dict(_quality_metrics_v1(runlog_rows, report))

    gate_rows = [row for row in runlog_rows if row.get("type") == "gate"]
    lore_total = 0
    lore_passed = 0
    for row in gate_rows:
        for gate in row.get("gates", []):
            if gate.get("gate_name") != "lore":
                continue
            lore_total += 1
            lore_passed += int(bool(gate.get("passed")))
    lore_pass_rate = lore_passed / max(1, lore_total)

    action_rows = [row for row in runlog_rows if row.get("type") == "action"]
    depth_map = {
        "HIDE_PREVIEW": 0.25,
        "LOCK_THREAD": 0.5,
        "GHOST_THREAD": 0.75,
        "SANCTION_USER": 1.0,
    }
    moderation_escalation_depth = 0.0
    for row in action_rows:
        action_type = row.get("action_type")
        moderation_escalation_depth = max(moderation_escalation_depth, depth_map.get(action_type, 0.0))

    dialogue = report.get("dialogue_candidates", [])
    dialogue_count = len(dialogue)
    unique_speakers = len({item.get("speaker") for item in dialogue if item.get("speaker")})
    dialogue_speaker_diversity = unique_speakers / max(1, dialogue_count)

    metrics.update(
        {
            "lore_pass_rate": float(round(lore_pass_rate, 4)),
            "moderation_escalation_depth": float(round(moderation_escalation_depth, 4)),
            "dialogue_speaker_diversity": float(round(dialogue_speaker_diversity, 4)),
        }
    )
    return metrics


METRIC_SET_REGISTRY = {
    "v1": _quality_metrics_v1,
    "v2": _quality_metrics_v2,
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


def _report_quality_checks_v1(report: dict) -> list[EvalCheck]:
    checks: list[EvalCheck] = []

    conflict_map = report.get("conflict_map", {})
    mediation_points = conflict_map.get("mediation_points", []) if isinstance(conflict_map, dict) else []
    mediation_count = len(mediation_points) if isinstance(mediation_points, list) else 0
    checks.append(
        EvalCheck(
            name="report.conflict_map.mediation_points_count",
            passed=mediation_count >= 1,
            details=f"mediation_points={mediation_count}",
        )
    )

    foreshadowing = report.get("foreshadowing", [])
    foreshadowing_count = len(foreshadowing) if isinstance(foreshadowing, list) else 0
    checks.append(
        EvalCheck(
            name="report.foreshadowing_count",
            passed=foreshadowing_count >= 1,
            details=f"foreshadowing_count={foreshadowing_count}",
        )
    )

    dialogue_candidates = report.get("dialogue_candidates", [])
    invalid_dialogue_indices: list[int] = []
    if not isinstance(dialogue_candidates, list):
        invalid_dialogue_indices.append(-1)
    else:
        for idx, item in enumerate(dialogue_candidates):
            if not isinstance(item, dict):
                invalid_dialogue_indices.append(idx)
                continue
            speaker = str(item.get("speaker", "")).strip()
            line = str(item.get("line", "")).strip()
            if not speaker or not line:
                invalid_dialogue_indices.append(idx)
    checks.append(
        EvalCheck(
            name="report.dialogue_candidate_fields",
            passed=len(invalid_dialogue_indices) == 0 and isinstance(dialogue_candidates, list),
            details=f"invalid_indices={invalid_dialogue_indices}",
        )
    )

    risk_checks = report.get("risk_checks", [])
    invalid_severity_indices: list[int] = []
    if isinstance(risk_checks, list):
        for idx, item in enumerate(risk_checks):
            if not isinstance(item, dict):
                invalid_severity_indices.append(idx)
                continue
            severity = str(item.get("severity", "")).strip().lower()
            if severity not in VALID_RISK_SEVERITIES:
                invalid_severity_indices.append(idx)
    else:
        invalid_severity_indices.append(-1)
    checks.append(
        EvalCheck(
            name="report.risk_checks.severity_values",
            passed=len(invalid_severity_indices) == 0 and isinstance(risk_checks, list),
            details=f"invalid_indices={invalid_severity_indices}",
        )
    )

    return checks


def evaluate_run(run_dir: Path, metric_set: str = "v1") -> dict:
    if metric_set not in METRIC_SET_REGISTRY:
        raise ValueError(f"Unknown metric_set: {metric_set}")

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

    checks.extend(_report_quality_checks_v1(report))

    pass_fail = all(check.passed for check in checks)
    quality_metrics = METRIC_SET_REGISTRY[metric_set](runlog_rows, report)

    result = EvalResult(
        metric_set=metric_set,
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
            **quality_metrics,
        },
    )
    return result.model_dump()


def find_latest_run(runs_dir: Path) -> Path:
    candidates = sorted([p for p in runs_dir.glob("run-*") if p.is_dir()], key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No run directories found under {runs_dir}")
    return candidates[-1]
