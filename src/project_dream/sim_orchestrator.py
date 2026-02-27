from project_dream.env_engine import apply_policy_transition, compute_score
from project_dream.gen_engine import generate_comment
from project_dream.gate_pipeline import run_gates
from project_dream.persona_service import select_participants


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
    community_id = _select_community_id(seed, packs)
    template_id, flow_id = _select_template(seed, packs)

    status = "visible"
    total_reports = 0
    total_views = 0

    for round_idx in range(1, rounds + 1):
        participants = select_participants(seed, round_idx=round_idx)[:3]

        for idx, persona_id in enumerate(participants):
            text = generate_comment(seed, persona_id, round_idx=round_idx)
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

            round_logs.append(
                {
                    "round": round_idx,
                    "persona_id": persona_id,
                    "board_id": seed.board_id,
                    "community_id": community_id,
                    "thread_template_id": template_id,
                    "comment_flow_id": flow_id,
                    "status": status,
                    "score": score,
                    "text": last["final_text"],
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

    return {
        "rounds": round_logs,
        "gate_logs": gate_logs,
        "action_logs": action_logs,
        "thread_state": {
            "board_id": seed.board_id,
            "community_id": community_id,
            "thread_template_id": template_id,
            "comment_flow_id": flow_id,
            "status": status,
            "total_reports": total_reports,
        },
    }
