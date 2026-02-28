from collections import Counter

from project_dream.llm_client import LLMClient, build_default_llm_client
from project_dream.models import ReportConflictMap, ReportRiskCheck, ReportV1
from project_dream.prompt_templates import render_prompt
from project_dream.report_gate import run_report_gate


def _build_lens_summaries(sim_result: dict, packs) -> list[dict]:
    rounds = sim_result.get("rounds", [])
    by_community = Counter(row.get("community_id", "UNKNOWN") for row in rounds)
    summaries: list[dict] = []

    for community in sorted(packs.communities.values(), key=lambda c: c["id"]):
        cid = community["id"]
        count = by_community.get(cid, 0)
        mood = "관측 없음" if count == 0 else f"발화 {count}회 관측"
        summaries.append(
            {
                "community_id": cid,
                "community_name": community.get("name", cid),
                "summary": mood,
            }
        )
    return summaries


def _build_highlights_top10(sim_result: dict) -> list[dict]:
    rounds = sim_result.get("rounds", [])
    ranked = sorted(rounds, key=lambda row: row.get("score", 0), reverse=True)
    return [
        {
            "round": row["round"],
            "persona_id": row["persona_id"],
            "community_id": row["community_id"],
            "score": row.get("score", 0),
            "text": row.get("text", ""),
        }
        for row in ranked[:10]
    ]


def _build_conflict_map(sim_result: dict) -> ReportConflictMap:
    action_logs = sim_result.get("action_logs", [])
    report_count = sum(1 for row in action_logs if row.get("action_type") == "REPORT")
    moderation_count = sum(
        1
        for row in action_logs
        if row.get("action_type") in {"HIDE_PREVIEW", "LOCK_THREAD", "GHOST_THREAD", "SANCTION_USER"}
    )
    return ReportConflictMap(
        claim_a=f"공론장 확산 파트: 신고 이벤트 {report_count}회",
        claim_b=f"운영 개입 파트: 정책 전이 {moderation_count}회",
        third_interest="노출 점수 경쟁과 보존권 우선순위",
        mediation_points=[
            "정본/증거 근거 우선 정렬",
            "항소 가능한 임시 조치 우선",
            "보존권/신고 비율 임계치 재평가",
        ],
    )


def _build_dialogue_candidates(
    sim_result: dict,
    llm_client: LLMClient,
    template_set: str = "v1",
) -> list[dict]:
    rounds = sim_result.get("rounds", [])
    candidates: list[dict] = []
    for row in rounds[:5]:
        prompt = render_prompt(
            "report_dialogue_candidate",
            {
                "text": row.get("text", ""),
                "speaker": row.get("persona_id", "unknown"),
                "round": row.get("round", 0),
            },
            template_set=template_set,
        )
        candidates.append(
            {
                "speaker": row.get("persona_id", "unknown"),
                "line": llm_client.generate(prompt, task="report_dialogue_candidate"),
                "tone": "forum",
            }
        )
    while len(candidates) < 3:
        prompt = render_prompt(
            "report_dialogue_candidate",
            {
                "text": "추가 발화 필요",
                "speaker": "system",
                "round": 0,
            },
            template_set=template_set,
        )
        candidates.append({"speaker": "system", "line": "추가 발화 필요", "tone": "neutral"})
        candidates[-1]["line"] = llm_client.generate(prompt, task="report_dialogue_candidate")
    return candidates[:5]


def _build_foreshadowing(sim_result: dict) -> list[str]:
    action_logs = sim_result.get("action_logs", [])
    hooks = []
    if any(row.get("action_type") == "HIDE_PREVIEW" for row in action_logs):
        hooks.append("가리기 이후 역유입(스트라이샌드) 가능성")
    if any(row.get("action_type") == "LOCK_THREAD" for row in action_logs):
        hooks.append("봉문 이후 타게시판 우회 확산 가능성")
    if any(row.get("action_type") == "GHOST_THREAD" for row in action_logs):
        hooks.append("유령처리 링크 공유에 의한 음지 확산")
    if not hooks:
        hooks.append("운영 개입 전 여론 선점 경쟁")
    return hooks


def _build_risk_checks(sim_result: dict) -> list[ReportRiskCheck]:
    gate_logs = sim_result.get("gate_logs", [])
    risk: list[ReportRiskCheck] = []

    safety_fail = 0
    similarity_fail = 0
    lore_fail = 0
    for row in gate_logs:
        for gate in row.get("gates", []):
            if gate["passed"]:
                continue
            if gate["gate_name"] == "safety":
                safety_fail += 1
            if gate["gate_name"] == "similarity":
                similarity_fail += 1
            if gate["gate_name"] == "lore":
                lore_fail += 1

    if safety_fail > 0:
        risk.append(
            ReportRiskCheck(
                category="safety",
                severity="medium",
                details=f"안전 게이트 재작성 {safety_fail}회",
            )
        )
    if similarity_fail > 0:
        risk.append(
            ReportRiskCheck(
                category="similarity",
                severity="medium",
                details=f"유사도 게이트 재작성 {similarity_fail}회",
            )
        )
    if lore_fail > 0:
        risk.append(
            ReportRiskCheck(
                category="rule",
                severity="high",
                details=f"정합성 게이트 재작성 {lore_fail}회",
            )
        )
    if not risk:
        risk.append(ReportRiskCheck(category="rule", severity="low", details="중요 리스크 미검출"))
    return risk


def _seed_constraints(seed) -> dict:
    public_facts = [str(item) for item in getattr(seed, "public_facts", []) if str(item).strip()]
    hidden_facts = [str(item) for item in getattr(seed, "hidden_facts", []) if str(item).strip()]
    stakeholders = [str(item) for item in getattr(seed, "stakeholders", []) if str(item).strip()]
    forbidden_terms = [str(item) for item in getattr(seed, "forbidden_terms", []) if str(item).strip()]
    sensitivity_tags = [str(item) for item in getattr(seed, "sensitivity_tags", []) if str(item).strip()]
    return {
        "public_facts": public_facts,
        "hidden_facts": hidden_facts,
        "stakeholders": stakeholders,
        "forbidden_terms": forbidden_terms,
        "sensitivity_tags": sensitivity_tags,
        "has_hidden_facts": len(hidden_facts) > 0,
    }


def _build_evidence_watch(seed) -> dict:
    raw_grade = str(getattr(seed, "evidence_grade", "B")).strip().upper()
    grade = raw_grade if raw_grade in {"A", "B", "C"} else "B"
    evidence_type = str(getattr(seed, "evidence_type", "log")).strip() or "log"
    try:
        expires_in_hours = max(0, int(getattr(seed, "evidence_expiry_hours", 72)))
    except (TypeError, ValueError):
        expires_in_hours = 72
    return {
        "grade": grade,
        "type": evidence_type,
        "expires_in_hours": expires_in_hours,
        "countdown_risk": expires_in_hours <= 24,
    }


def build_report_v1(
    seed,
    sim_result: dict,
    packs,
    llm_client: LLMClient | None = None,
    template_set: str = "v1",
) -> dict:
    client = llm_client if llm_client is not None else build_default_llm_client()
    round_count = len(sim_result.get("rounds", []))
    constraints = _seed_constraints(seed)
    evidence_watch = _build_evidence_watch(seed)
    risk_checks = _build_risk_checks(sim_result)
    if constraints["forbidden_terms"] or constraints["sensitivity_tags"]:
        risk_checks.append(
            ReportRiskCheck(
                category="seed_constraint",
                severity="low",
                details=(
                    f"forbidden_terms={len(constraints['forbidden_terms'])}, "
                    f"sensitivity_tags={','.join(constraints['sensitivity_tags']) or 'none'}"
                ),
            )
        )
    if evidence_watch["countdown_risk"] or evidence_watch["grade"] == "C":
        risk_checks.append(
            ReportRiskCheck(
                category="evidence",
                severity="medium" if evidence_watch["grade"] == "C" else "low",
                details=(
                    f"grade={evidence_watch['grade']}, "
                    f"expires_in_hours={evidence_watch['expires_in_hours']}"
                ),
            )
        )
    summary_prompt = render_prompt(
        "report_summary",
        {
            "title": seed.title,
            "round_count": round_count,
        },
        template_set=template_set,
    )
    report = ReportV1(
        seed_id=seed.seed_id,
        title=seed.title,
        summary=client.generate(summary_prompt, task="report_summary"),
        lens_summaries=_build_lens_summaries(sim_result, packs),
        highlights_top10=_build_highlights_top10(sim_result),
        conflict_map=_build_conflict_map(sim_result),
        dialogue_candidates=_build_dialogue_candidates(
            sim_result,
            llm_client=client,
            template_set=template_set,
        ),
        foreshadowing=_build_foreshadowing(sim_result),
        risk_checks=risk_checks,
        seed_constraints=constraints,
        evidence_watch=evidence_watch,
    )
    payload = report.model_dump()
    payload["report_gate"] = run_report_gate(payload)
    return payload
