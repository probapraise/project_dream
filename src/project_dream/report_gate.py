from __future__ import annotations

from project_dream.eval_suite import REQUIRED_REPORT_KEYS, VALID_RISK_SEVERITIES


def _check(name: str, passed: bool, details: str) -> dict:
    return {"name": name, "passed": bool(passed), "details": details}


def _dialogue_fields_valid(dialogue_candidates: object) -> tuple[bool, list[int]]:
    invalid_indices: list[int] = []
    if not isinstance(dialogue_candidates, list):
        return False, [-1]
    for idx, item in enumerate(dialogue_candidates):
        if not isinstance(item, dict):
            invalid_indices.append(idx)
            continue
        speaker = str(item.get("speaker", "")).strip()
        line = str(item.get("line", "")).strip()
        if not speaker or not line:
            invalid_indices.append(idx)
    return len(invalid_indices) == 0, invalid_indices


def _risk_severity_valid(risk_checks: object) -> tuple[bool, list[int]]:
    invalid_indices: list[int] = []
    if not isinstance(risk_checks, list):
        return False, [-1]
    for idx, item in enumerate(risk_checks):
        if not isinstance(item, dict):
            invalid_indices.append(idx)
            continue
        severity = str(item.get("severity", "")).strip().lower()
        if severity not in VALID_RISK_SEVERITIES:
            invalid_indices.append(idx)
    return len(invalid_indices) == 0, invalid_indices


def run_report_gate(report: dict) -> dict:
    checks: list[dict] = []

    missing_sections = sorted(list(REQUIRED_REPORT_KEYS - set(report.keys())))
    checks.append(
        _check(
            "report.required_sections",
            len(missing_sections) == 0,
            f"missing={missing_sections}",
        )
    )

    lens_count = len(report.get("lens_summaries", [])) if isinstance(report.get("lens_summaries"), list) else 0
    checks.append(_check("report.lens_count", lens_count == 4, f"lens_count={lens_count}"))

    dialogue_candidates = report.get("dialogue_candidates", [])
    dialogue_count = len(dialogue_candidates) if isinstance(dialogue_candidates, list) else 0
    checks.append(_check("report.dialogue_count", 3 <= dialogue_count <= 5, f"dialogue_count={dialogue_count}"))

    highlight_count = len(report.get("highlights_top10", [])) if isinstance(report.get("highlights_top10"), list) else 0
    checks.append(
        _check(
            "report.highlights_count",
            1 <= highlight_count <= 10,
            f"highlight_count={highlight_count}",
        )
    )

    conflict = report.get("conflict_map", {})
    mediation_points = conflict.get("mediation_points", []) if isinstance(conflict, dict) else []
    mediation_count = len(mediation_points) if isinstance(mediation_points, list) else 0
    checks.append(
        _check(
            "report.conflict_map.mediation_points_count",
            mediation_count >= 1,
            f"mediation_points={mediation_count}",
        )
    )

    foreshadowing = report.get("foreshadowing", [])
    foreshadowing_count = len(foreshadowing) if isinstance(foreshadowing, list) else 0
    checks.append(
        _check(
            "report.foreshadowing_count",
            foreshadowing_count >= 1,
            f"foreshadowing_count={foreshadowing_count}",
        )
    )

    dialogue_valid, invalid_dialogue_indices = _dialogue_fields_valid(dialogue_candidates)
    checks.append(
        _check(
            "report.dialogue_candidate_fields",
            dialogue_valid,
            f"invalid_indices={invalid_dialogue_indices}",
        )
    )

    risk_valid, invalid_risk_indices = _risk_severity_valid(report.get("risk_checks", []))
    checks.append(
        _check(
            "report.risk_checks.severity_values",
            risk_valid,
            f"invalid_indices={invalid_risk_indices}",
        )
    )

    failed_checks = [check for check in checks if not check["passed"]]
    return {
        "schema_version": "report_gate.v1",
        "pass_fail": len(failed_checks) == 0,
        "checks": checks,
        "failed_checks": failed_checks,
    }
