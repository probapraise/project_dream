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

    assert result["action_logs"]
    assert any(row["action_type"] == "REPORT" for row in result["action_logs"])
