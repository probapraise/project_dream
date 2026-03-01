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
    "story_checklist",
}
VALID_RISK_SEVERITIES = {"low", "medium", "high"}
REQUIRED_STORY_CHECKLIST_KEYS = {
    "countdown_risk",
    "evidence_grade",
    "board_migration_clue",
    "meme",
    "event_card",
}
VALID_STORY_CHECKLIST_STATUSES = {"ok", "risk", "missing"}
REQUIRED_STAGE_EVENT_TYPES = {
    "thread_candidate",
    "thread_selected",
    "round_summary",
    "moderation_decision",
    "end_condition",
}


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

    round_rows = [row for row in runlog_rows if row.get("type") == "round"]
    dial_flow_total = 0
    dial_flow_aligned = 0
    dial_sort_tab_total = 0
    dial_sort_tab_aligned = 0
    for row in round_rows:
        expected_flow_id = str(row.get("dial_target_flow_id", "")).strip()
        flow_id = str(row.get("comment_flow_id", "")).strip()
        if expected_flow_id and flow_id:
            dial_flow_total += 1
            dial_flow_aligned += int(expected_flow_id == flow_id)

        expected_tab = str(row.get("dial_target_sort_tab", "")).strip()
        sort_tab = str(row.get("sort_tab", "")).strip()
        if expected_tab and sort_tab:
            dial_sort_tab_total += 1
            dial_sort_tab_aligned += int(expected_tab == sort_tab)

    dial_flow_alignment_rate = dial_flow_aligned / max(1, dial_flow_total)
    dial_sort_tab_alignment_rate = dial_sort_tab_aligned / max(1, dial_sort_tab_total)

    metrics.update(
        {
            "lore_pass_rate": float(round(lore_pass_rate, 4)),
            "moderation_escalation_depth": float(round(moderation_escalation_depth, 4)),
            "dialogue_speaker_diversity": float(round(dialogue_speaker_diversity, 4)),
            "dial_flow_alignment_rate": float(round(dial_flow_alignment_rate, 4)),
            "dial_sort_tab_alignment_rate": float(round(dial_sort_tab_alignment_rate, 4)),
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

    story_checklist = report.get("story_checklist", {})
    missing_story_items: list[str] = []
    invalid_story_items: list[str] = []
    if not isinstance(story_checklist, dict):
        missing_story_items = sorted(REQUIRED_STORY_CHECKLIST_KEYS)
        invalid_story_items.append("story_checklist_not_dict")
    else:
        for key in sorted(REQUIRED_STORY_CHECKLIST_KEYS):
            if key not in story_checklist:
                missing_story_items.append(key)
                continue
            item = story_checklist.get(key)
            if not isinstance(item, dict):
                invalid_story_items.append(f"{key}:not_dict")
                continue
            label = str(item.get("label", "")).strip()
            status = str(item.get("status", "")).strip().lower()
            details = str(item.get("details", "")).strip()
            if not label:
                invalid_story_items.append(f"{key}:label")
            if status not in VALID_STORY_CHECKLIST_STATUSES:
                invalid_story_items.append(f"{key}:status")
            if not details:
                invalid_story_items.append(f"{key}:details")
    checks.append(
        EvalCheck(
            name="report.story_checklist.required_items",
            passed=len(missing_story_items) == 0 and len(invalid_story_items) == 0,
            details=(
                f"missing={sorted(missing_story_items)};"
                f"invalid={sorted(invalid_story_items)}"
            ),
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

    context_rows = [row for row in runlog_rows if row.get("type") == "context"]
    checks.append(
        EvalCheck(
            name="runlog.context_trace_present",
            passed=len(context_rows) >= 1,
            details=f"context_rows={len(context_rows)}",
        )
    )

    stage_type_counts: dict[str, int] = {
        event_type: sum(1 for row in runlog_rows if row.get("type") == event_type)
        for event_type in sorted(REQUIRED_STAGE_EVENT_TYPES)
    }
    missing_stage_types = [
        event_type for event_type in sorted(REQUIRED_STAGE_EVENT_TYPES) if stage_type_counts[event_type] < 1
    ]
    checks.append(
        EvalCheck(
            name="runlog.stage_trace_present",
            passed=len(missing_stage_types) == 0,
            details=f"missing={missing_stage_types};counts={stage_type_counts}",
        )
    )

    round_ids = sorted({int(row.get("round", 0)) for row in runlog_rows if row.get("type") == "round"})
    round_summary_ids = sorted(
        {int(row.get("round", 0)) for row in runlog_rows if row.get("type") == "round_summary"}
    )
    moderation_ids = sorted(
        {int(row.get("round", 0)) for row in runlog_rows if row.get("type") == "moderation_decision"}
    )
    end_conditions = [row for row in runlog_rows if row.get("type") == "end_condition"]
    ended_round = None
    if end_conditions:
        ended_round = int(end_conditions[0].get("ended_round", 0))

    expected_rounds = ended_round if ended_round and ended_round > 0 else len(round_ids)
    if expected_rounds > 0:
        round_summary_coverage = min(stage_type_counts.get("round_summary", 0), expected_rounds) / expected_rounds
        moderation_coverage = min(stage_type_counts.get("moderation_decision", 0), expected_rounds) / expected_rounds
    else:
        round_summary_coverage = 0.0
        moderation_coverage = 0.0
    stage_trace_coverage_rate = (
        (1.0 if stage_type_counts.get("thread_candidate", 0) >= 1 else 0.0)
        + (1.0 if stage_type_counts.get("thread_selected", 0) >= 1 else 0.0)
        + (1.0 if stage_type_counts.get("end_condition", 0) >= 1 else 0.0)
        + round_summary_coverage
        + moderation_coverage
    ) / 5.0
    stage_trace_coverage_rate = float(round(stage_trace_coverage_rate, 4))

    stage_trace_consistent = (
        len(end_conditions) == 1
        and ended_round is not None
        and ended_round > 0
        and ended_round == len(round_ids)
        and round_ids == round_summary_ids
        and round_ids == moderation_ids
    )
    checks.append(
        EvalCheck(
            name="runlog.stage_trace_consistency",
            passed=stage_trace_consistent,
            details=(
                f"end_condition_rows={len(end_conditions)};"
                f"ended_round={ended_round};"
                f"round_ids={round_ids};"
                f"round_summary_ids={round_summary_ids};"
                f"moderation_ids={moderation_ids}"
            ),
        )
    )

    indices_by_type: dict[str, list[int]] = {}
    for idx, row in enumerate(runlog_rows):
        row_type = row.get("type")
        if not row_type:
            continue
        indices_by_type.setdefault(str(row_type), []).append(idx)

    core_indices = [
        idx
        for row_type in ("round", "gate", "action")
        for idx in indices_by_type.get(row_type, [])
    ]
    first_round_idx = (
        min(indices_by_type.get("round", [])) if indices_by_type.get("round") else None
    )
    core_last_idx = max(core_indices) if core_indices else None

    context_first_idx = (
        min(indices_by_type.get("context", [])) if indices_by_type.get("context") else None
    )
    thread_candidate_last_idx = (
        max(indices_by_type.get("thread_candidate", []))
        if indices_by_type.get("thread_candidate")
        else None
    )
    thread_selected_first_idx = (
        min(indices_by_type.get("thread_selected", []))
        if indices_by_type.get("thread_selected")
        else None
    )
    round_summary_first_idx = (
        min(indices_by_type.get("round_summary", []))
        if indices_by_type.get("round_summary")
        else None
    )
    round_summary_last_idx = (
        max(indices_by_type.get("round_summary", []))
        if indices_by_type.get("round_summary")
        else None
    )
    moderation_first_idx = (
        min(indices_by_type.get("moderation_decision", []))
        if indices_by_type.get("moderation_decision")
        else None
    )
    moderation_last_idx = (
        max(indices_by_type.get("moderation_decision", []))
        if indices_by_type.get("moderation_decision")
        else None
    )
    end_condition_idx = (
        min(indices_by_type.get("end_condition", []))
        if indices_by_type.get("end_condition")
        else None
    )

    stage_trace_ordered = (
        context_first_idx is not None
        and first_round_idx is not None
        and core_last_idx is not None
        and thread_candidate_last_idx is not None
        and thread_selected_first_idx is not None
        and round_summary_first_idx is not None
        and round_summary_last_idx is not None
        and moderation_first_idx is not None
        and moderation_last_idx is not None
        and end_condition_idx is not None
        and context_first_idx < first_round_idx
        and thread_candidate_last_idx < first_round_idx
        and thread_selected_first_idx < first_round_idx
        and round_summary_first_idx > core_last_idx
        and moderation_first_idx > round_summary_last_idx
        and end_condition_idx > moderation_last_idx
    )
    checks.append(
        EvalCheck(
            name="runlog.stage_trace_ordering",
            passed=stage_trace_ordered,
            details=(
                f"context_first={context_first_idx};"
                f"first_round={first_round_idx};"
                f"core_last={core_last_idx};"
                f"thread_candidate_last={thread_candidate_last_idx};"
                f"thread_selected_first={thread_selected_first_idx};"
                f"round_summary_first={round_summary_first_idx};"
                f"round_summary_last={round_summary_last_idx};"
                f"moderation_first={moderation_first_idx};"
                f"moderation_last={moderation_last_idx};"
                f"end_condition={end_condition_idx}"
            ),
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

    story_checklist = report.get("story_checklist", {})
    if isinstance(story_checklist, dict):
        story_checklist_present_items = sum(1 for key in REQUIRED_STORY_CHECKLIST_KEYS if key in story_checklist)
    else:
        story_checklist_present_items = 0

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
            "context_rows": len(context_rows),
            "stage_trace_rows": sum(stage_type_counts.values()),
            "stage_trace_coverage_rate": stage_trace_coverage_rate,
            "stage_trace_consistent": int(stage_trace_consistent),
            "stage_trace_ordered": int(stage_trace_ordered),
            "round_rows": sum(1 for row in runlog_rows if row.get("type") == "round"),
            "gate_rows": sum(1 for row in runlog_rows if row.get("type") == "gate"),
            "action_rows": sum(1 for row in runlog_rows if row.get("type") == "action"),
            "highlight_count": highlight_count,
            "dialogue_count": dialogue_count,
            "lens_count": lens_count,
            "story_checklist_present_items": story_checklist_present_items,
            **quality_metrics,
        },
    )
    return result.model_dump()


def find_latest_run(runs_dir: Path) -> Path:
    candidates = sorted([p for p in runs_dir.glob("run-*") if p.is_dir()], key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No run directories found under {runs_dir}")
    return candidates[-1]
