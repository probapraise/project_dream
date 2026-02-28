from project_dream.env_engine import apply_policy_transition, compute_score
from project_dream.gen_engine import generate_comment, pop_last_generation_trace, reset_last_generation_trace
from project_dream.gate_pipeline import run_gates
from project_dream.persona_service import render_voice, select_participants
from project_dream.prompt_templates import render_prompt


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
    template_context = _resolve_template_context(packs, template_id)
    flow_context = _resolve_flow_context(packs, flow_id)
    thread_candidates = _build_thread_candidates(
        seed,
        community_id=community_id,
        template_id=template_id,
        flow_id=flow_id,
        template_context=template_context,
        flow_context=flow_context,
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
            last = None
            total_failed_in_attempts = 0

            for _ in range(max_retries + 1):
                last = run_gates(text, corpus=corpus)
                failed_in_attempt = [gate for gate in last["gates"] if not gate["passed"]]
                total_failed_in_attempts += len(failed_in_attempt)
                if not failed_in_attempt:
                    break
                text = last["final_text"]

            assert last is not None
            report_delta = total_failed_in_attempts
            total_reports += report_delta
            total_views += 3
            score = compute_score(
                up=1 + (idx % 3),
                comments=round_idx,
                views=total_views,
                preserve=1 if idx == 0 else 0,
                reports=total_reports,
                trust=1,
                account_type=account_type,
                sanction_level=sanction_level,
                sort_tab=sort_tab,
            )
            severity = 0
            if report_delta >= 3:
                severity = 2
            if report_delta >= 5:
                severity = 3
            status, transition_event = apply_policy_transition(
                status=status,
                reports=total_reports,
                severity=severity,
                appeal=False,
                account_type=account_type,
                verified=verified,
                sanction_level=sanction_level,
            )
            sanction_level = int(transition_event.get("sanction_level", sanction_level))

            memory_entries = persona_memory.setdefault(persona_id, [])
            memory_source = _sanitize_for_memory(last["final_text"])
            memory_entries.append(f"R{round_idx}:{memory_source[:80]}")
            memory_after = _memory_summary(memory_entries)

            round_logs.append(
                {
                    "round": round_idx,
                    "persona_id": persona_id,
                    "board_id": seed.board_id,
                    "community_id": community_id,
                    "thread_template_id": template_id,
                    "comment_flow_id": flow_id,
                    "thread_candidate_id": selected_thread.get("candidate_id", "TC-0"),
                    "status": status,
                    "score": score,
                    "title_pattern": selected_title_pattern,
                    "template_trigger_tags": selected_trigger_tags,
                    "flow_body_sections": selected_body_sections,
                    "template_taboos": template_taboos,
                    "account_type": account_type,
                    "sort_tab": sort_tab,
                    "sanction_level": sanction_level,
                    "generation_stage1": stage1_trace,
                    "generation_stage2": stage2_trace,
                    "text": last["final_text"],
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "voice_style": voice_constraints.get("sentence_length", "medium"),
                }
            )
            gate_logs.append({"round": round_idx, "persona_id": persona_id, "gates": last["gates"]})
            action_logs.append(
                {
                    "round": round_idx,
                    "action_type": "POST_COMMENT",
                    "actor_id": persona_id,
                    "target_id": seed.seed_id,
                    "status": status,
                    "account_type": account_type,
                }
            )
            if report_delta > 0:
                action_logs.append(
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
                action_logs.append(
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

    end_condition = {
        "termination_reason": termination_reason,
        "ended_round": last_processed_round,
        "ended_early": ended_early,
        "status": status,
    }
    round_summaries = _build_round_summaries(round_logs, action_logs)

    return {
        "thread_candidates": thread_candidates,
        "selected_thread": selected_thread,
        "round_summaries": round_summaries,
        "moderation_decisions": moderation_decisions,
        "end_condition": end_condition,
        "rounds": round_logs,
        "gate_logs": gate_logs,
        "action_logs": action_logs,
        "persona_memory": persona_memory,
        "thread_state": {
            "board_id": seed.board_id,
            "community_id": community_id,
            "thread_template_id": template_id,
            "comment_flow_id": flow_id,
            "title_pattern": selected_title_pattern,
            "trigger_tags": selected_trigger_tags,
            "body_sections": selected_body_sections,
            "status": status,
            "sanction_level": sanction_level,
            "total_reports": total_reports,
            "termination_reason": termination_reason,
            "ended_round": last_processed_round,
            "ended_early": ended_early,
        },
    }
