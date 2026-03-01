from project_dream.env_engine import apply_policy_transition, compute_score
from project_dream.gen_engine import generate_comment, pop_last_generation_trace, reset_last_generation_trace
from project_dream.gate_pipeline import run_gates
from project_dream.persona_service import render_voice, select_participants
from project_dream.prompt_templates import render_prompt
from typing import TypedDict

SIMULATION_STAGE_NODE_ORDER = (
    "thread_candidate",
    "round_loop",
    "moderation",
    "end_condition",
)
ROUND_LOOP_NODE_ORDER = (
    "generate_comment",
    "gate_retry",
    "policy_transition",
    "emit_logs",
)


class ThreadCandidateStagePayload(TypedDict):
    thread_candidates: list[dict]
    selected_thread: dict | None


class RoundLoopStagePayload(TypedDict):
    rounds: list[dict]
    gate_logs: list[dict]
    action_logs: list[dict]
    persona_memory: dict[str, list[str]]


class ModerationStagePayload(TypedDict):
    round_summaries: list[dict]
    moderation_decisions: list[dict]


class EndConditionStagePayload(TypedDict):
    end_condition: dict | None
    thread_state: dict | None


class SimulationStagePayloads(TypedDict):
    thread_candidate: ThreadCandidateStagePayload
    round_loop: RoundLoopStagePayload
    moderation: ModerationStagePayload
    end_condition: EndConditionStagePayload


def _as_dict_list(values: object) -> list[dict]:
    if not isinstance(values, list):
        return []
    out: list[dict] = []
    for value in values:
        if isinstance(value, dict):
            out.append(dict(value))
    return out


def _coerce_round_number(value: object) -> int:
    try:
        round_number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, round_number)


def _normalize_persona_memory(memory_payload: object) -> dict[str, list[str]]:
    if not isinstance(memory_payload, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for raw_persona_id, raw_entries in memory_payload.items():
        if not isinstance(raw_entries, list):
            continue
        entries: list[str] = []
        for raw_entry in raw_entries:
            text = str(raw_entry).strip()
            if text:
                entries.append(text)
        normalized[str(raw_persona_id)] = entries
    return normalized


def run_stage_node_thread_candidate(stage_payload: ThreadCandidateStagePayload | dict) -> ThreadCandidateStagePayload:
    payload = dict(stage_payload) if isinstance(stage_payload, dict) else {}
    thread_candidates = _as_dict_list(payload.get("thread_candidates"))

    selected_thread_raw = payload.get("selected_thread")
    selected_thread = dict(selected_thread_raw) if isinstance(selected_thread_raw, dict) else None
    candidate_ids = {
        str(candidate.get("candidate_id", "")).strip()
        for candidate in thread_candidates
        if str(candidate.get("candidate_id", "")).strip()
    }

    if candidate_ids:
        selected_id = str((selected_thread or {}).get("candidate_id", "")).strip()
        if not selected_id or selected_id not in candidate_ids:
            selected_thread = _select_thread_candidate(thread_candidates)

    return {
        "thread_candidates": thread_candidates,
        "selected_thread": selected_thread,
    }


def run_stage_node_round_loop(stage_payload: RoundLoopStagePayload | dict) -> RoundLoopStagePayload:
    payload = dict(stage_payload) if isinstance(stage_payload, dict) else {}
    return {
        "rounds": _as_dict_list(payload.get("rounds")),
        "gate_logs": _as_dict_list(payload.get("gate_logs")),
        "action_logs": _as_dict_list(payload.get("action_logs")),
        "persona_memory": _normalize_persona_memory(payload.get("persona_memory")),
    }


def run_stage_node_moderation(stage_payload: ModerationStagePayload | dict) -> ModerationStagePayload:
    payload = dict(stage_payload) if isinstance(stage_payload, dict) else {}
    round_summaries = sorted(_as_dict_list(payload.get("round_summaries")), key=lambda row: _coerce_round_number(row.get("round")))
    moderation_rows = sorted(
        _as_dict_list(payload.get("moderation_decisions")),
        key=lambda row: _coerce_round_number(row.get("round")),
    )

    moderation_decisions: list[dict] = []
    for index, row in enumerate(moderation_rows, start=1):
        normalized = dict(row)
        if _coerce_round_number(normalized.get("round")) <= 0:
            normalized["round"] = index
        normalized.setdefault("action_type", "NO_OP")
        normalized.setdefault("reason_rule_id", "RULE-PLZ-UI-01")
        moderation_decisions.append(normalized)

    return {
        "round_summaries": round_summaries,
        "moderation_decisions": moderation_decisions,
    }


def run_stage_node_end_condition(stage_payload: EndConditionStagePayload | dict) -> EndConditionStagePayload:
    payload = dict(stage_payload) if isinstance(stage_payload, dict) else {}
    end_condition_raw = payload.get("end_condition")
    thread_state_raw = payload.get("thread_state")

    end_condition = dict(end_condition_raw) if isinstance(end_condition_raw, dict) else {}
    thread_state = dict(thread_state_raw) if isinstance(thread_state_raw, dict) else None
    thread_state_view = thread_state or {}

    status = str(thread_state_view.get("status") or end_condition.get("status") or "visible")
    lock_statuses = {"locked", "ghost", "sanctioned"}
    termination_reason = str(
        thread_state_view.get("termination_reason")
        or end_condition.get("termination_reason")
        or ("moderation_lock" if status in lock_statuses else "round_limit")
    )
    ended_round = _coerce_round_number(end_condition.get("ended_round", thread_state_view.get("ended_round", 0)))

    if "ended_early" in end_condition:
        ended_early = bool(end_condition.get("ended_early"))
    elif "ended_early" in thread_state_view:
        ended_early = bool(thread_state_view.get("ended_early"))
    else:
        ended_early = termination_reason == "moderation_lock"

    normalized_end_condition = {
        "termination_reason": termination_reason,
        "ended_round": ended_round,
        "ended_early": ended_early,
        "status": status,
    }
    normalized_thread_state = None
    if thread_state is not None:
        normalized_thread_state = dict(thread_state)
        normalized_thread_state.update(normalized_end_condition)

    return {
        "end_condition": normalized_end_condition,
        "thread_state": normalized_thread_state,
    }


def _select_community_id(seed, packs) -> str:
    if not packs:
        return f"ZONE-{seed.zone_id}"

    candidates = [c for c in packs.communities.values() if c.get("board_id") == seed.board_id]
    if not candidates:
        return "UNKNOWN-COMMUNITY"

    for community in candidates:
        if community.get("zone_id") == seed.zone_id:
            return community["id"]
    return candidates[0]["id"]


def _select_template(seed, packs) -> tuple[str, str]:
    if not packs or not packs.thread_templates:
        return "T1", "P1"

    sorted_templates = sorted(packs.thread_templates.values(), key=lambda x: x["id"])
    for template in sorted_templates:
        if seed.board_id in template.get("intended_boards", []):
            return template["id"], template.get("default_comment_flow", "P1")
    return "T1", "P1"


def _select_event_card_id(seed, packs) -> str:
    if not packs or not getattr(packs, "event_cards", None):
        return "EV-DEFAULT"
    events = sorted(packs.event_cards.values(), key=lambda x: x["id"])
    for event in events:
        if seed.board_id in _as_str_list(event.get("intended_boards")):
            return event["id"]
    return events[0]["id"]


def _select_meme_seed_id(seed, packs) -> str:
    if not packs or not getattr(packs, "meme_seeds", None):
        return "MM-DEFAULT"
    memes = sorted(packs.meme_seeds.values(), key=lambda x: x["id"])
    for meme in memes:
        if seed.board_id in _as_str_list(meme.get("intended_boards")):
            return meme["id"]
    return memes[0]["id"]


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _resolve_template_context(packs, template_id: str, selected_title_pattern: str = "") -> dict:
    if packs and template_id in packs.thread_templates:
        template = dict(packs.thread_templates[template_id])
    else:
        template = {"id": template_id}
    title_patterns = _as_str_list(template.get("title_patterns")) or ["{title}"]
    return {
        "template_id": template_id,
        "title_patterns": title_patterns,
        "title_pattern": selected_title_pattern or title_patterns[0],
        "trigger_tags": _as_str_list(template.get("trigger_tags")) or [f"template:{template_id.lower()}"],
        "taboos": _as_str_list(template.get("taboos")),
    }


def _resolve_flow_context(packs, flow_id: str) -> dict:
    if packs and flow_id in packs.comment_flows:
        flow = dict(packs.comment_flows[flow_id])
    else:
        flow = {"id": flow_id}
    return {
        "flow_id": flow_id,
        "body_sections": _as_str_list(flow.get("body_sections")) or ["상황정리", "근거정리", "요청/정리"],
        "escalation_rules": list(flow.get("escalation_rules", []))
        if isinstance(flow.get("escalation_rules"), list)
        else [],
    }


def _render_title_pattern(pattern: str, seed) -> str:
    try:
        return pattern.format(
            title=seed.title,
            summary=seed.summary,
            board_id=seed.board_id,
            zone_id=seed.zone_id,
        )
    except (KeyError, ValueError):
        return seed.title


def _memory_summary(entries: list[str], *, max_items: int = 2, max_chars: int = 140) -> str:
    if not entries:
        return ""
    text = " / ".join(entries[-max_items:])
    return text[:max_chars]


def _sanitize_for_memory(text: str) -> str:
    # Keep only user-facing utterance, excluding system-added hints/rewrites.
    base = text.split(" | memory=", 1)[0]
    base = base.replace(" / 근거(정본/증거/로그) 기준 추가 필요", "")
    return base.strip()


def _build_thread_candidates(
    seed,
    *,
    community_id: str,
    template_id: str,
    flow_id: str,
    template_context: dict | None = None,
    flow_context: dict | None = None,
    event_card_id: str = "",
    meme_seed_id: str = "",
    count: int = 3,
) -> list[dict]:
    frames = ("fact", "conflict", "rumor")
    template_ctx = template_context or _resolve_template_context(None, template_id)
    flow_ctx = flow_context or _resolve_flow_context(None, flow_id)
    title_patterns = _as_str_list(template_ctx.get("title_patterns")) or ["{title}"]
    trigger_tags = _as_str_list(template_ctx.get("trigger_tags"))
    body_sections = _as_str_list(flow_ctx.get("body_sections"))
    candidates: list[dict] = []
    for idx in range(count):
        frame = frames[idx % len(frames)]
        title_pattern = title_patterns[idx % len(title_patterns)]
        rendered_title = _render_title_pattern(title_pattern, seed)
        prompt = render_prompt(
            "thread_generation",
            {
                "board_id": seed.board_id,
                "zone_id": seed.zone_id,
                "title": rendered_title,
                "summary": seed.summary,
            },
        )
        candidates.append(
            {
                "candidate_id": f"TC-{idx + 1}",
                "community_id": community_id,
                "thread_template_id": template_id,
                "comment_flow_id": flow_id,
                "event_card_id": event_card_id,
                "meme_seed_id": meme_seed_id,
                "frame": frame,
                "title_pattern": title_pattern,
                "rendered_title": rendered_title,
                "trigger_tags": trigger_tags,
                "body_sections": body_sections,
                "score": round(1.0 - (idx * 0.1), 2),
                "text": (
                    f"{prompt} | frame={frame}"
                    f" | tags={','.join(trigger_tags)}"
                    f" | sections={','.join(body_sections)}"
                ),
            }
        )
    return candidates


def _select_thread_candidate(candidates: list[dict]) -> dict:
    if not candidates:
        return {
            "candidate_id": "TC-0",
            "thread_template_id": "T1",
            "comment_flow_id": "P1",
            "score": 0.0,
            "text": "no-thread-candidate",
        }
    return max(candidates, key=lambda item: float(item.get("score", 0.0)))


def _build_round_summaries(round_logs: list[dict], action_logs: list[dict]) -> list[dict]:
    policy_actions = {"HIDE_PREVIEW", "LOCK_THREAD", "GHOST_THREAD", "SANCTION_USER"}
    rounds = sorted({int(row.get("round", 0)) for row in round_logs if int(row.get("round", 0)) > 0})
    summaries: list[dict] = []

    for round_idx in rounds:
        rows = [row for row in round_logs if int(row.get("round", 0)) == round_idx]
        reports = [
            row
            for row in action_logs
            if int(row.get("round", 0)) == round_idx and row.get("action_type") == "REPORT"
        ]
        policies = [
            row
            for row in action_logs
            if int(row.get("round", 0)) == round_idx and row.get("action_type") in policy_actions
        ]

        last_status = rows[-1].get("status", "visible") if rows else "visible"
        max_score = max(float(row.get("score", 0.0)) for row in rows) if rows else 0.0
        summaries.append(
            {
                "round": round_idx,
                "participant_count": len(rows),
                "report_events": len(reports),
                "policy_events": len(policies),
                "status": last_status,
                "max_score": round(max_score, 4),
            }
        )

    return summaries


def _is_escalation_rule_matched(rule: dict, *, round_idx: int, total_reports: int, status: str) -> bool:
    condition = rule.get("condition", {})
    if not isinstance(condition, dict):
        condition = {}
    reports_gte = int(condition.get("reports_gte", 0))
    round_gte = int(condition.get("round_gte", 0))
    status_in = condition.get("status_in", [])
    if total_reports < reports_gte:
        return False
    if round_idx < round_gte:
        return False
    if isinstance(status_in, list) and status_in:
        allowed = {str(value) for value in status_in}
        if status not in allowed:
            return False
    return True


def _collect_flow_escalation_events(
    *,
    rules: list[dict],
    round_idx: int,
    total_reports: int,
    status: str,
    seed_id: str,
    fired_actions: set[str],
) -> list[dict]:
    events: list[dict] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        action_type = str(rule.get("action_type", "")).strip()
        if not action_type or action_type in fired_actions:
            continue
        if not _is_escalation_rule_matched(
            rule,
            round_idx=round_idx,
            total_reports=total_reports,
            status=status,
        ):
            continue
        fired_actions.add(action_type)
        events.append(
            {
                "round": round_idx,
                "action_type": action_type,
                "actor_id": "system",
                "target_id": seed_id,
                "reason_rule_id": str(rule.get("reason_rule_id", "RULE-PLZ-UI-01")),
                "status": status,
                "total_reports": total_reports,
            }
        )
    return events


def _round_node_generate_comment(
    *,
    seed,
    persona_id: str,
    round_idx: int,
    memory_before: str,
    voice_constraints: dict,
    selected_title_pattern: str,
    selected_trigger_tags: list[str],
    template_taboos: list[str],
    selected_body_sections: list[str],
) -> dict:
    reset_last_generation_trace()
    text = generate_comment(
        seed,
        persona_id,
        round_idx=round_idx,
        memory_hint=memory_before,
        voice_constraints=voice_constraints,
        template_context={
            "title_pattern": selected_title_pattern,
            "trigger_tags": selected_trigger_tags,
            "taboos": template_taboos,
        },
        flow_context={
            "body_sections": selected_body_sections,
        },
    )
    generation_trace = pop_last_generation_trace() or {}
    stage1_trace = generation_trace.get(
        "stage1",
        {
            "claim": "",
            "evidence": "",
            "intent": "",
            "dial": "",
            "title_pattern": "",
            "trigger_tags": [],
            "body_sections": [],
            "template_taboos": [],
        },
    )
    stage2_trace = generation_trace.get(
        "stage2",
        {
            "voice_hint": "",
            "prompt": "",
            "sections": [],
            "trigger_tags": [],
        },
    )
    return {
        "text": text,
        "stage1_trace": stage1_trace,
        "stage2_trace": stage2_trace,
    }


def _round_node_gate_retry(
    *,
    text: str,
    corpus: list[str],
    max_retries: int,
    forbidden_terms: list[str] | None = None,
    sensitivity_tags: list[str] | None = None,
    gate_policy: dict | None = None,
) -> dict:
    last = None
    total_failed_in_attempts = 0
    current_text = text

    for _ in range(max_retries + 1):
        gate_kwargs: dict[str, object] = {}
        if forbidden_terms:
            gate_kwargs["forbidden_terms"] = list(forbidden_terms)
        if sensitivity_tags:
            gate_kwargs["sensitivity_tags"] = list(sensitivity_tags)
        if gate_policy:
            gate_kwargs["gate_policy"] = dict(gate_policy)
        last = run_gates(current_text, corpus=corpus, **gate_kwargs)
        failed_in_attempt = [gate for gate in last["gates"] if not gate["passed"]]
        total_failed_in_attempts += len(failed_in_attempt)
        if not failed_in_attempt:
            break
        current_text = last["final_text"]

    assert last is not None
    return {
        "final_text": last["final_text"],
        "gates": list(last["gates"]),
        "report_delta": total_failed_in_attempts,
    }


def _round_node_policy_transition(
    *,
    round_idx: int,
    idx: int,
    status: str,
    sanction_level: int,
    total_reports: int,
    total_views: int,
    report_delta: int,
    account_type: str,
    verified: bool,
    sort_tab: str,
    evidence_grade: str,
    evidence_hours_left: int,
) -> dict:
    next_total_reports = total_reports + report_delta
    next_total_views = total_views + 3

    score = compute_score(
        up=1 + (idx % 3),
        comments=round_idx,
        views=next_total_views,
        preserve=1 if idx == 0 else 0,
        reports=next_total_reports,
        trust=1,
        account_type=account_type,
        sanction_level=sanction_level,
        sort_tab=sort_tab,
        evidence_grade=evidence_grade,
        evidence_hours_left=evidence_hours_left,
    )

    severity = 0
    if report_delta >= 3:
        severity = 2
    if report_delta >= 5:
        severity = 3

    next_status, transition_event = apply_policy_transition(
        status=status,
        reports=next_total_reports,
        severity=severity,
        appeal=False,
        account_type=account_type,
        verified=verified,
        sanction_level=sanction_level,
    )
    next_sanction_level = int(transition_event.get("sanction_level", sanction_level))

    return {
        "status": next_status,
        "sanction_level": next_sanction_level,
        "total_reports": next_total_reports,
        "total_views": next_total_views,
        "score": score,
        "transition_event": transition_event,
    }


def _round_node_emit_logs(
    *,
    seed,
    round_idx: int,
    persona_id: str,
    board_id: str,
    community_id: str,
    template_id: str,
    flow_id: str,
    event_card_id: str,
    meme_seed_id: str,
    selected_thread_candidate_id: str,
    selected_title_pattern: str,
    selected_trigger_tags: list[str],
    selected_body_sections: list[str],
    template_taboos: list[str],
    evidence_grade: str,
    evidence_type: str,
    evidence_hours_left: int,
    account_type: str,
    sort_tab: str,
    sanction_level: int,
    status: str,
    score: float,
    stage1_trace: dict,
    stage2_trace: dict,
    final_text: str,
    memory_before: str,
    memory_entries: list[str],
    voice_constraints: dict,
    gates: list[dict],
    transition_event: dict,
    report_delta: int,
    total_reports: int,
) -> dict:
    memory_source = _sanitize_for_memory(final_text)
    memory_entries.append(f"R{round_idx}:{memory_source[:80]}")
    memory_after = _memory_summary(memory_entries)

    round_row = {
        "round": round_idx,
        "persona_id": persona_id,
        "board_id": board_id,
        "community_id": community_id,
        "thread_template_id": template_id,
        "comment_flow_id": flow_id,
        "event_card_id": event_card_id,
        "meme_seed_id": meme_seed_id,
        "thread_candidate_id": selected_thread_candidate_id,
        "status": status,
        "score": score,
        "title_pattern": selected_title_pattern,
        "template_trigger_tags": selected_trigger_tags,
        "flow_body_sections": selected_body_sections,
        "template_taboos": template_taboos,
        "evidence_grade": evidence_grade,
        "evidence_type": evidence_type,
        "evidence_hours_left": evidence_hours_left,
        "account_type": account_type,
        "sort_tab": sort_tab,
        "sanction_level": sanction_level,
        "generation_stage1": stage1_trace,
        "generation_stage2": stage2_trace,
        "text": final_text,
        "memory_before": memory_before,
        "memory_after": memory_after,
        "voice_style": voice_constraints.get("sentence_length", "medium"),
        "round_loop_nodes": list(ROUND_LOOP_NODE_ORDER),
    }
    gate_row = {"round": round_idx, "persona_id": persona_id, "gates": gates}

    action_rows = [
        {
            "round": round_idx,
            "action_type": "POST_COMMENT",
            "actor_id": persona_id,
            "target_id": seed.seed_id,
            "status": status,
            "account_type": account_type,
        }
    ]
    if report_delta > 0:
        action_rows.append(
            {
                "round": round_idx,
                "action_type": "REPORT",
                "actor_id": persona_id,
                "target_id": seed.seed_id,
                "delta": report_delta,
                "total_reports": total_reports,
            }
        )
    if transition_event["action_type"] != "NO_OP":
        action_rows.append(
            {
                "round": round_idx,
                "action_type": transition_event["action_type"],
                "actor_id": "system",
                "target_id": seed.seed_id,
                "prev_status": transition_event["prev_status"],
                "next_status": transition_event["next_status"],
                "reason_rule_id": transition_event["reason_rule_id"],
                "sanction_level": sanction_level,
                "status": status,
            }
        )

    return {
        "round_row": round_row,
        "gate_row": gate_row,
        "action_rows": action_rows,
        "memory_after": memory_after,
    }


def extract_stage_payloads(sim_result: dict) -> SimulationStagePayloads:
    persona_memory = sim_result.get("persona_memory", {})
    if isinstance(persona_memory, dict):
        persona_memory_copy = {str(k): list(v) for k, v in persona_memory.items() if isinstance(v, list)}
    else:
        persona_memory_copy = {}

    return {
        "thread_candidate": {
            "thread_candidates": list(sim_result.get("thread_candidates", [])),
            "selected_thread": sim_result.get("selected_thread"),
        },
        "round_loop": {
            "rounds": list(sim_result.get("rounds", [])),
            "gate_logs": list(sim_result.get("gate_logs", [])),
            "action_logs": list(sim_result.get("action_logs", [])),
            "persona_memory": persona_memory_copy,
        },
        "moderation": {
            "round_summaries": list(sim_result.get("round_summaries", [])),
            "moderation_decisions": list(sim_result.get("moderation_decisions", [])),
        },
        "end_condition": {
            "end_condition": sim_result.get("end_condition"),
            "thread_state": sim_result.get("thread_state"),
        },
    }


def assemble_sim_result_from_stage_payloads(stage_payloads: SimulationStagePayloads | dict[str, dict]) -> dict:
    thread_payload = dict(stage_payloads.get("thread_candidate", {}))
    round_payload = dict(stage_payloads.get("round_loop", {}))
    moderation_payload = dict(stage_payloads.get("moderation", {}))
    end_payload = dict(stage_payloads.get("end_condition", {}))

    return {
        "thread_candidates": list(thread_payload.get("thread_candidates", [])),
        "selected_thread": thread_payload.get("selected_thread"),
        "round_summaries": list(moderation_payload.get("round_summaries", [])),
        "moderation_decisions": list(moderation_payload.get("moderation_decisions", [])),
        "end_condition": end_payload.get("end_condition"),
        "rounds": list(round_payload.get("rounds", [])),
        "gate_logs": list(round_payload.get("gate_logs", [])),
        "action_logs": list(round_payload.get("action_logs", [])),
        "persona_memory": dict(round_payload.get("persona_memory", {})),
        "thread_state": end_payload.get("thread_state"),
    }


def run_simulation(
    seed,
    rounds: int,
    corpus: list[str],
    max_retries: int = 2,
    packs=None,
) -> dict:
    round_logs: list[dict] = []
    gate_logs: list[dict] = []
    action_logs: list[dict] = []
    moderation_decisions: list[dict] = []
    persona_memory: dict[str, list[str]] = {}
    community_id = _select_community_id(seed, packs)
    template_id, flow_id = _select_template(seed, packs)
    event_card_id = _select_event_card_id(seed, packs)
    meme_seed_id = _select_meme_seed_id(seed, packs)
    template_context = _resolve_template_context(packs, template_id)
    flow_context = _resolve_flow_context(packs, flow_id)
    thread_candidates = _build_thread_candidates(
        seed,
        community_id=community_id,
        template_id=template_id,
        flow_id=flow_id,
        template_context=template_context,
        flow_context=flow_context,
        event_card_id=event_card_id,
        meme_seed_id=meme_seed_id,
        count=3,
    )
    selected_thread = _select_thread_candidate(thread_candidates)
    selected_title_pattern = str(selected_thread.get("title_pattern", "")).strip()
    selected_trigger_tags = _as_str_list(selected_thread.get("trigger_tags")) or _as_str_list(
        template_context.get("trigger_tags")
    )
    selected_body_sections = _as_str_list(selected_thread.get("body_sections")) or _as_str_list(
        flow_context.get("body_sections")
    )
    template_taboos = _as_str_list(template_context.get("taboos"))
    seed_forbidden_terms = _as_str_list(getattr(seed, "forbidden_terms", []))
    seed_sensitivity_tags = _as_str_list(getattr(seed, "sensitivity_tags", []))
    pack_gate_policy = None
    if packs is not None:
        raw_policy = getattr(packs, "gate_policy", None)
        if isinstance(raw_policy, dict):
            pack_gate_policy = dict(raw_policy)
    raw_evidence_grade = str(getattr(seed, "evidence_grade", "B")).strip().upper()
    evidence_grade = raw_evidence_grade if raw_evidence_grade in {"A", "B", "C"} else "B"
    evidence_type = str(getattr(seed, "evidence_type", "log")).strip() or "log"
    try:
        evidence_hours_left = max(0, int(getattr(seed, "evidence_expiry_hours", 72)))
    except (TypeError, ValueError):
        evidence_hours_left = 72
    fired_flow_actions: set[str] = set()
    account_type_cycle = ("public", "alias", "mask")
    sort_tab_cycle = ("latest", "weekly_hot", "evidence_first", "preserve_first")

    status = "visible"
    sanction_level = 0
    total_reports = 0
    total_views = 0
    last_processed_round = 0
    ended_early = False
    termination_reason = "round_limit"

    for round_idx in range(1, rounds + 1):
        last_processed_round = round_idx
        round_status_before = status
        round_action = "NO_OP"
        round_reason_rule_id = "RULE-PLZ-UI-01"
        participants = select_participants(seed, round_idx=round_idx, packs=packs)[:3]

        for idx, persona_id in enumerate(participants):
            account_type = account_type_cycle[idx % len(account_type_cycle)]
            verified = account_type == "public"
            sort_tab = sort_tab_cycle[(round_idx - 1) % len(sort_tab_cycle)]
            before_entries = persona_memory.get(persona_id, [])
            memory_before = _memory_summary(before_entries)
            voice_constraints = dict(render_voice(persona_id, seed.zone_id, packs=packs))
            base_taboos = _as_str_list(voice_constraints.get("taboo_words"))
            voice_constraints["taboo_words"] = _unique(base_taboos + template_taboos)

            generated = _round_node_generate_comment(
                seed=seed,
                persona_id=persona_id,
                round_idx=round_idx,
                memory_before=memory_before,
                voice_constraints=voice_constraints,
                selected_title_pattern=selected_title_pattern,
                selected_trigger_tags=selected_trigger_tags,
                template_taboos=template_taboos,
                selected_body_sections=selected_body_sections,
            )
            gated = _round_node_gate_retry(
                text=str(generated["text"]),
                corpus=corpus,
                max_retries=max_retries,
                forbidden_terms=seed_forbidden_terms,
                sensitivity_tags=seed_sensitivity_tags,
                gate_policy=pack_gate_policy,
            )
            transitioned = _round_node_policy_transition(
                round_idx=round_idx,
                idx=idx,
                status=status,
                sanction_level=sanction_level,
                total_reports=total_reports,
                total_views=total_views,
                report_delta=int(gated["report_delta"]),
                account_type=account_type,
                verified=verified,
                sort_tab=sort_tab,
                evidence_grade=evidence_grade,
                evidence_hours_left=evidence_hours_left,
            )
            status = str(transitioned["status"])
            sanction_level = int(transitioned["sanction_level"])
            total_reports = int(transitioned["total_reports"])
            total_views = int(transitioned["total_views"])
            score = float(transitioned["score"])
            transition_event = dict(transitioned["transition_event"])
            report_delta = int(gated["report_delta"])

            memory_entries = persona_memory.setdefault(persona_id, [])
            emitted = _round_node_emit_logs(
                seed=seed,
                round_idx=round_idx,
                persona_id=persona_id,
                board_id=seed.board_id,
                community_id=community_id,
                template_id=template_id,
                flow_id=flow_id,
                event_card_id=event_card_id,
                meme_seed_id=meme_seed_id,
                selected_thread_candidate_id=str(selected_thread.get("candidate_id", "TC-0")),
                selected_title_pattern=selected_title_pattern,
                selected_trigger_tags=selected_trigger_tags,
                selected_body_sections=selected_body_sections,
                template_taboos=template_taboos,
                evidence_grade=evidence_grade,
                evidence_type=evidence_type,
                evidence_hours_left=evidence_hours_left,
                account_type=account_type,
                sort_tab=sort_tab,
                sanction_level=sanction_level,
                status=status,
                score=score,
                stage1_trace=dict(generated["stage1_trace"]),
                stage2_trace=dict(generated["stage2_trace"]),
                final_text=str(gated["final_text"]),
                memory_before=memory_before,
                memory_entries=memory_entries,
                voice_constraints=voice_constraints,
                gates=list(gated["gates"]),
                transition_event=transition_event,
                report_delta=report_delta,
                total_reports=total_reports,
            )
            round_logs.append(dict(emitted["round_row"]))
            gate_logs.append(dict(emitted["gate_row"]))
            action_logs.extend(list(emitted["action_rows"]))

            if transition_event["action_type"] != "NO_OP":
                round_action = transition_event["action_type"]
                round_reason_rule_id = transition_event["reason_rule_id"]

            if status in {"locked", "ghost", "sanctioned"}:
                ended_early = True
                termination_reason = "moderation_lock"
                break

        flow_events = _collect_flow_escalation_events(
            rules=list(flow_context.get("escalation_rules", [])),
            round_idx=round_idx,
            total_reports=total_reports,
            status=status,
            seed_id=seed.seed_id,
            fired_actions=fired_flow_actions,
        )
        action_logs.extend(flow_events)

        moderation_decisions.append(
            {
                "round": round_idx,
                "action_type": round_action,
                "reason_rule_id": round_reason_rule_id,
                "status_before": round_status_before,
                "status_after": status,
                "report_total": total_reports,
                "sanction_level": sanction_level,
            }
        )

        if ended_early:
            break
        evidence_hours_left = max(0, evidence_hours_left - 6)

    end_condition = {
        "termination_reason": termination_reason,
        "ended_round": last_processed_round,
        "ended_early": ended_early,
        "status": status,
    }
    round_summaries = _build_round_summaries(round_logs, action_logs)

    thread_state = {
        "board_id": seed.board_id,
        "community_id": community_id,
        "thread_template_id": template_id,
        "comment_flow_id": flow_id,
        "event_card_id": event_card_id,
        "meme_seed_id": meme_seed_id,
        "evidence_grade": evidence_grade,
        "evidence_type": evidence_type,
        "evidence_hours_left": evidence_hours_left,
        "title_pattern": selected_title_pattern,
        "trigger_tags": selected_trigger_tags,
        "body_sections": selected_body_sections,
        "status": status,
        "sanction_level": sanction_level,
        "total_reports": total_reports,
        "termination_reason": termination_reason,
        "ended_round": last_processed_round,
        "ended_early": ended_early,
    }
    stage_payloads = {
        "thread_candidate": {
            "thread_candidates": thread_candidates,
            "selected_thread": selected_thread,
        },
        "round_loop": {
            "rounds": round_logs,
            "gate_logs": gate_logs,
            "action_logs": action_logs,
            "persona_memory": persona_memory,
        },
        "moderation": {
            "round_summaries": round_summaries,
            "moderation_decisions": moderation_decisions,
        },
        "end_condition": {
            "end_condition": end_condition,
            "thread_state": thread_state,
        },
    }
    return assemble_sim_result_from_stage_payloads(stage_payloads)
