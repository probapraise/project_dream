from project_dream.env_engine import apply_policy_transition, compute_score
from project_dream.gen_engine import generate_comment
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
    count: int = 3,
) -> list[dict]:
    frames = ("fact", "conflict", "rumor")
    candidates: list[dict] = []
    for idx in range(count):
        frame = frames[idx % len(frames)]
        prompt = render_prompt(
            "thread_generation",
            {
                "board_id": seed.board_id,
                "zone_id": seed.zone_id,
                "title": seed.title,
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
                "score": round(1.0 - (idx * 0.1), 2),
                "text": f"{prompt} | frame={frame}",
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
    persona_memory: dict[str, list[str]] = {}
    community_id = _select_community_id(seed, packs)
    template_id, flow_id = _select_template(seed, packs)
    thread_candidates = _build_thread_candidates(
        seed,
        community_id=community_id,
        template_id=template_id,
        flow_id=flow_id,
        count=3,
    )
    selected_thread = _select_thread_candidate(thread_candidates)

    status = "visible"
    total_reports = 0
    total_views = 0
    last_processed_round = 0
    ended_early = False
    termination_reason = "round_limit"

    for round_idx in range(1, rounds + 1):
        last_processed_round = round_idx
        participants = select_participants(seed, round_idx=round_idx, packs=packs)[:3]

        for idx, persona_id in enumerate(participants):
            before_entries = persona_memory.get(persona_id, [])
            memory_before = _memory_summary(before_entries)
            voice_constraints = render_voice(persona_id, seed.zone_id, packs=packs)
            text = generate_comment(
                seed,
                persona_id,
                round_idx=round_idx,
                memory_hint=memory_before,
                voice_constraints=voice_constraints,
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
            )

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
                        "status": status,
                    }
                )

            if status in {"locked", "ghost", "sanctioned"}:
                ended_early = True
                termination_reason = "moderation_lock"
                break

        if ended_early:
            break

    end_condition = {
        "termination_reason": termination_reason,
        "ended_round": last_processed_round,
        "ended_early": ended_early,
        "status": status,
    }

    return {
        "thread_candidates": thread_candidates,
        "selected_thread": selected_thread,
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
            "status": status,
            "total_reports": total_reports,
            "termination_reason": termination_reason,
            "ended_round": last_processed_round,
            "ended_early": ended_early,
        },
    }
