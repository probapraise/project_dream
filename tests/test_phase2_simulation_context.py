from pathlib import Path

from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.sim_orchestrator import run_simulation


def test_simulation_uses_pack_context_and_action_logs():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-001",
        title="중계망 먹통 사건",
        summary="장터기둥 게시판 접속 장애",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)

    assert result["rounds"]
    first = result["rounds"][0]
    assert first["board_id"] == "B07"
    assert first["community_id"] == "COM-PLZ-004"
    assert first["thread_template_id"].startswith("T")
    assert first["comment_flow_id"].startswith("P")
    assert first["persona_id"].startswith("P")

    assert result["action_logs"]
    assert any(row["action_type"] == "REPORT" for row in result["action_logs"])


def test_simulation_emits_thread_candidates_and_selection():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-THREAD-001",
        title="학칙 위반 제보",
        summary="증거 캡처가 올라오며 논쟁이 시작된다",
        board_id="B11",
        zone_id="A",
    )

    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)

    candidates = result["thread_candidates"]
    assert len(candidates) == 3
    assert all(item["candidate_id"].startswith("TC-") for item in candidates)

    selected = result["selected_thread"]
    assert selected["candidate_id"] in {item["candidate_id"] for item in candidates}
    assert selected["thread_template_id"].startswith("T")
    assert selected["comment_flow_id"].startswith("P")

    round_rows = result["rounds"]
    assert round_rows
    assert all(row["thread_candidate_id"] == selected["candidate_id"] for row in round_rows)


def test_simulation_marks_round_limit_end_condition():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-END-ROUND-001",
        title="마감 라운드 테스트",
        summary="정상 라운드 종료",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)

    state = result["thread_state"]
    assert state["termination_reason"] == "round_limit"
    assert state["ended_round"] == 3
    assert state["ended_early"] is False


def test_simulation_ends_early_on_locked_status():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-END-MOD-001",
        title="누적 신고 락 테스트",
        summary="신고 누적으로 잠금 종료",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=10, corpus=["샘플"], max_retries=0, packs=packs)

    state = result["thread_state"]
    assert state["status"] in {"locked", "ghost", "sanctioned"}
    assert state["termination_reason"] == "moderation_lock"
    assert state["ended_early"] is True
    assert state["ended_round"] < 10


def test_simulation_emits_round_summaries():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-SUMMARY-001",
        title="라운드 요약 테스트",
        summary="라운드별 참여와 신고를 요약한다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=4, corpus=["샘플"], packs=packs)

    summaries = result["round_summaries"]
    assert summaries
    assert len(summaries) == result["thread_state"]["ended_round"]

    first = summaries[0]
    assert first["round"] == 1
    assert first["participant_count"] >= 1
    assert "status" in first
    assert "report_events" in first
    assert "policy_events" in first


def test_simulation_emits_moderation_decisions():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-MOD-001",
        title="운영 판단 기록 테스트",
        summary="라운드마다 운영 판단 이벤트를 남긴다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=4, corpus=["샘플"], packs=packs)

    decisions = result["moderation_decisions"]
    assert decisions
    assert len(decisions) == result["thread_state"]["ended_round"]
    assert all("round" in item for item in decisions)
    assert all("action_type" in item for item in decisions)
    assert all("status_after" in item for item in decisions)
    assert all(item["action_type"] in {"NO_OP", "HIDE_PREVIEW", "LOCK_THREAD", "GHOST_THREAD", "SANCTION_USER"} for item in decisions)


def test_simulation_emits_policy_transition_event_fields():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-ENV-001",
        title="누적 신고 과열",
        summary="동일 사건 반복으로 신고가 누적된다",
        board_id="B07",
        zone_id="D",
    )

    # max_retries=0 + 5라운드로 누적 신고를 hidden 임계치(10) 이상으로 올린다.
    result = run_simulation(seed=seed, rounds=5, corpus=["샘플"], max_retries=0, packs=packs)
    transitions = [
        row
        for row in result["action_logs"]
        if row["action_type"] in {"HIDE_PREVIEW", "LOCK_THREAD", "GHOST_THREAD", "SANCTION_USER"}
    ]
    assert transitions
    first = transitions[0]
    assert first["prev_status"] in {"visible", "hidden", "locked", "ghost"}
    assert first["next_status"] in {"hidden", "locked", "ghost", "sanctioned"}
    assert first["reason_rule_id"].startswith("RULE-PLZ-")


def test_simulation_emits_generation_stage_trace_fields():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-GEN-STAGE-001",
        title="생성 단계 추적",
        summary="2단계 생성 엔진의 산출물을 로그에 남긴다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=packs)

    assert result["rounds"]
    first = result["rounds"][0]
    assert "generation_stage1" in first
    assert "generation_stage2" in first

    stage1 = first["generation_stage1"]
    stage2 = first["generation_stage2"]
    assert isinstance(stage1, dict)
    assert isinstance(stage2, dict)
    assert {"claim", "evidence", "intent"} <= set(stage1.keys())
    assert "dial" in stage1
    assert "voice_hint" in stage2


def test_simulation_reflects_template_flow_runtime_fields():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-TPL-001",
        title="거래 사기 검증",
        summary="의심 후기 묶음을 검증한다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=packs)

    selected = result["selected_thread"]
    assert selected.get("title_pattern")
    assert isinstance(selected.get("trigger_tags"), list)
    assert selected["trigger_tags"]

    first = result["rounds"][0]
    stage1 = first["generation_stage1"]
    stage2 = first["generation_stage2"]
    assert isinstance(stage1.get("trigger_tags"), list)
    assert isinstance(stage1.get("body_sections"), list)
    assert isinstance(stage1.get("template_taboos"), list)
    assert "sections=" in stage2.get("prompt", "")


def test_simulation_emits_flow_escalation_actions():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-FLOW-ESC-001",
        title="검증 과열",
        summary="신고 누적과 함께 흐름 에스컬레이션이 발생한다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=5, corpus=["샘플"], max_retries=0, packs=packs)
    flow_actions = [row for row in result["action_logs"] if str(row.get("action_type", "")).startswith("FLOW_ESCALATE_")]

    assert flow_actions
    assert all("reason_rule_id" in row for row in flow_actions)
    assert all(str(row["reason_rule_id"]).startswith("RULE-PLZ-") for row in flow_actions)


def test_simulation_selects_event_card_and_meme_seed():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-EVENT-MEME-001",
        title="이벤트/밈 선택 테스트",
        summary="템플릿 기반으로 이벤트 카드와 밈 시드를 고른다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=packs)
    selected = result["selected_thread"]

    assert selected.get("event_card_id")
    assert selected.get("meme_seed_id")
    assert all(row.get("event_card_id") == selected["event_card_id"] for row in result["rounds"])
    assert all(row.get("meme_seed_id") == selected["meme_seed_id"] for row in result["rounds"])


def test_simulation_tracks_evidence_grade_and_countdown():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-EVID-001",
        title="증거 카운트다운 테스트",
        summary="증거 만료 시간이 라운드에 반영되어야 한다",
        board_id="B07",
        zone_id="D",
        evidence_grade="B",
        evidence_type="log",
        evidence_expiry_hours=24,
    )

    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)
    rounds = result["rounds"]

    assert rounds
    assert all(row.get("evidence_grade") == "B" for row in rounds)
    assert all(row.get("evidence_type") == "log" for row in rounds)
    assert all("evidence_hours_left" in row for row in rounds)

    first_hour = rounds[0]["evidence_hours_left"]
    last_hour = rounds[-1]["evidence_hours_left"]
    assert first_hour >= last_hour


def test_simulation_reflects_dial_weighted_flow_and_sort_tab_selection():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    evidence_seed = SeedInput(
        seed_id="SEED-DIAL-E-001",
        title="팩트체크 우선 사건",
        summary="증거 검증이 핵심인 사건",
        board_id="B01",
        zone_id="A",
        dial={"U": 10, "E": 60, "M": 10, "S": 10, "H": 10},
    )
    hype_seed = SeedInput(
        seed_id="SEED-DIAL-H-001",
        title="밈 과열 사건",
        summary="패러디 확산이 핵심인 사건",
        board_id="B01",
        zone_id="A",
        dial={"U": 10, "E": 10, "M": 10, "S": 10, "H": 60},
    )

    evidence_result = run_simulation(seed=evidence_seed, rounds=2, corpus=["샘플"], packs=packs)
    hype_result = run_simulation(seed=hype_seed, rounds=2, corpus=["샘플"], packs=packs)

    assert evidence_result["selected_thread"]["comment_flow_id"] == "P2"
    assert {row["sort_tab"] for row in evidence_result["rounds"]} == {"evidence_first"}
    assert all(row["dial_dominant_axis"] == "E" for row in evidence_result["rounds"])
    assert all(row["dial_target_flow_id"] == "P2" for row in evidence_result["rounds"])
    assert all(row["dial_target_sort_tab"] == "evidence_first" for row in evidence_result["rounds"])

    assert hype_result["selected_thread"]["comment_flow_id"] == "P6"
    assert {row["sort_tab"] for row in hype_result["rounds"]} == {"weekly_hot"}
    assert all(row["dial_dominant_axis"] == "H" for row in hype_result["rounds"])
    assert all(row["dial_target_flow_id"] == "P6" for row in hype_result["rounds"])
    assert all(row["dial_target_sort_tab"] == "weekly_hot" for row in hype_result["rounds"])


def test_simulation_passes_pack_gate_policy_into_gate_pipeline(monkeypatch):
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-GATE-POLICY-001",
        title="게이트 정책 주입 테스트",
        summary="pack gate_policy가 run_gates로 전달되는지 확인",
        board_id="B07",
        zone_id="D",
    )
    captured_gate_policies: list[dict] = []

    def fake_run_gates(text: str, corpus: list[str], **kwargs) -> dict:
        policy = kwargs.get("gate_policy")
        if isinstance(policy, dict):
            captured_gate_policies.append(policy)
        return {
            "final_text": text,
            "gates": [
                {"gate_name": "safety", "passed": True, "reason": "ok", "violations": []},
                {"gate_name": "similarity", "passed": True, "reason": "ok", "violations": []},
                {"gate_name": "lore", "passed": True, "reason": "ok", "violations": []},
            ],
            "violations": [],
        }

    monkeypatch.setattr("project_dream.sim_orchestrator.run_gates", fake_run_gates)

    run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=packs)

    assert captured_gate_policies
    assert captured_gate_policies[0] == packs.gate_policy


def test_simulation_emits_dispute_hooks_when_moderation_and_evidence_risk_overlap():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-DISPUTE-001",
        title="운영 개입 분쟁 훅 테스트",
        summary="운영 개입 뒤 반발/항소 루프가 발생해야 한다",
        board_id="B07",
        zone_id="D",
        evidence_grade="C",
        evidence_type="rumor_capture",
        evidence_expiry_hours=12,
    )

    result = run_simulation(seed=seed, rounds=5, corpus=["샘플"], max_retries=0, packs=packs)
    action_types = [str(row.get("action_type", "")) for row in result.get("action_logs", [])]

    assert any(
        action in {"HIDE_PREVIEW", "LOCK_THREAD", "GHOST_THREAD", "SANCTION_USER"}
        for action in action_types
    )
    assert "APPEAL_TIMER_TICK" in action_types
    assert "APPEAL_DELAY" in action_types
    assert "CONSPIRACY_BACKLASH" in action_types


def test_simulation_emits_cross_inflow_stage_logs():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-CROSS-001",
        title="교차 유입 스테이지 테스트",
        summary="운영 개입 이후 타 보드 요약 전달 로그가 남아야 한다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=5, corpus=["샘플"], max_retries=0, packs=packs)

    assert "cross_inflow_logs" in result
    cross_logs = result["cross_inflow_logs"]
    assert cross_logs

    first = cross_logs[0]
    assert first["from_board_id"] == "B07"
    assert first["to_board_id"] != "B07"
    assert first["mode"] in {"repost", "summary_relay"}
    assert first["reason"] in {"moderation", "report_pressure"}


def test_simulation_emits_meme_flow_logs_with_hub_factory_backflow():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-MEME-FLOW-001",
        title="밈 확산 라우팅 테스트",
        summary="허브에서 밈공장으로 확산 후 역류 로그가 기록되어야 한다",
        board_id="B07",
        zone_id="D",
    )

    result = run_simulation(seed=seed, rounds=5, corpus=["샘플"], max_retries=0, packs=packs)

    assert "meme_flow_logs" in result
    logs = result["meme_flow_logs"]
    assert logs
    assert logs[0]["phase"] == "hub_to_factory"
    assert any(row["phase"] == "backflow" for row in logs)

    rounds = {int(row["round"]) for row in logs}
    assert rounds == set(range(1, result["thread_state"]["ended_round"] + 1))
    assert all(row["meme_decay_profile"] in {"explosive", "weekly", "institutional"} for row in logs)
    assert all(float(row["meme_heat"]) >= 0.0 for row in logs)


def test_simulation_selects_meme_decay_profile_by_dominant_axis():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    cases = [
        (
            "explosive",
            {"U": 10, "E": 10, "M": 10, "S": 10, "H": 60},
        ),
        (
            "weekly",
            {"U": 10, "E": 60, "M": 10, "S": 10, "H": 10},
        ),
        (
            "institutional",
            {"U": 10, "E": 10, "M": 60, "S": 10, "H": 10},
        ),
    ]

    for index, (expected_profile, dial) in enumerate(cases, start=1):
        seed = SeedInput(
            seed_id=f"SEED-MEME-PROFILE-{index:03d}",
            title="밈 반감기 프로필 테스트",
            summary="다이얼 축에 따라 반감기 프로필이 고정되어야 한다",
            board_id="B07",
            zone_id="D",
            dial=dial,
        )
        result = run_simulation(seed=seed, rounds=4, corpus=["샘플"], max_retries=0, packs=packs)
        profiles = {str(row.get("meme_decay_profile", "")) for row in result.get("meme_flow_logs", [])}
        assert profiles == {expected_profile}


def test_simulation_applies_board_culture_weight_by_dial_axis():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    hype_seed = SeedInput(
        seed_id="SEED-CULTURE-H-001",
        title="문화 가중치 H 테스트",
        summary="냉소 보드에서 H 다이얼은 높은 문화 가중치가 적용되어야 한다",
        board_id="B16",
        zone_id="A",
        dial={"U": 10, "E": 10, "M": 10, "S": 10, "H": 60},
    )
    evidence_seed = SeedInput(
        seed_id="SEED-CULTURE-E-001",
        title="문화 가중치 E 테스트",
        summary="동일 보드에서 E 다이얼은 상대적으로 낮은 문화 가중치가 적용되어야 한다",
        board_id="B16",
        zone_id="A",
        dial={"U": 10, "E": 60, "M": 10, "S": 10, "H": 10},
    )

    hype_result = run_simulation(seed=hype_seed, rounds=2, corpus=["샘플"], max_retries=0, packs=packs)
    evidence_result = run_simulation(seed=evidence_seed, rounds=2, corpus=["샘플"], max_retries=0, packs=packs)

    hype_first = hype_result["rounds"][0]
    evidence_first = evidence_result["rounds"][0]

    assert hype_first["board_emotion"] == "냉소"
    assert evidence_first["board_emotion"] == "냉소"
    assert float(hype_first["culture_weight_multiplier"]) > float(evidence_first["culture_weight_multiplier"])
