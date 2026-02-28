from project_dream.models import SeedInput
from project_dream.sim_orchestrator import (
    SIMULATION_STAGE_NODE_ORDER,
    assemble_sim_result_from_stage_payloads,
    extract_stage_payloads,
    run_simulation,
)


def _seed() -> SeedInput:
    return SeedInput(
        seed_id="SEED-STAGE-001",
        title="스테이지 라운드트립",
        summary="node payload roundtrip test",
        board_id="B07",
        zone_id="D",
    )


def test_stage_payload_roundtrip_preserves_core_outputs():
    sim_result = run_simulation(seed=_seed(), rounds=3, corpus=["ctx-1"])

    payloads = extract_stage_payloads(sim_result)
    rebuilt = assemble_sim_result_from_stage_payloads(payloads)

    assert rebuilt["thread_state"] == sim_result["thread_state"]
    assert rebuilt["selected_thread"] == sim_result["selected_thread"]
    assert rebuilt["end_condition"] == sim_result["end_condition"]
    assert len(rebuilt["thread_candidates"]) == len(sim_result["thread_candidates"])
    assert len(rebuilt["rounds"]) == len(sim_result["rounds"])
    assert len(rebuilt["gate_logs"]) == len(sim_result["gate_logs"])
    assert len(rebuilt["action_logs"]) == len(sim_result["action_logs"])
    assert len(rebuilt["round_summaries"]) == len(sim_result["round_summaries"])
    assert len(rebuilt["moderation_decisions"]) == len(sim_result["moderation_decisions"])


def test_stage_payload_order_is_stable():
    assert SIMULATION_STAGE_NODE_ORDER == (
        "thread_candidate",
        "round_loop",
        "moderation",
        "end_condition",
    )


def test_extract_stage_payloads_returns_copies():
    sim_result = run_simulation(seed=_seed(), rounds=3, corpus=["ctx-1"])

    payloads = extract_stage_payloads(sim_result)
    payloads["round_loop"]["rounds"].append({"round": 999})
    payloads["moderation"]["round_summaries"].append({"round": 999})

    assert all(row.get("round") != 999 for row in sim_result["rounds"])
    assert all(row.get("round") != 999 for row in sim_result["round_summaries"])
