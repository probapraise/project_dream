from project_dream.models import SeedInput
from project_dream.sim_orchestrator import run_simulation


def test_orchestrator_runs_three_rounds_minimum():
    seed = SeedInput(seed_id="SEED-001", title="사건", summary="요약", board_id="B01", zone_id="A")
    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"])
    assert len(result["rounds"]) >= 3
    assert len(result["gate_logs"]) >= 3
