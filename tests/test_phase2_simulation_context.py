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
