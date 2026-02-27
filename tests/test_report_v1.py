from pathlib import Path

from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.report_generator import build_report_v1
from project_dream.sim_orchestrator import run_simulation


def test_report_v1_has_required_sections_and_sizes():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-RPT-001",
        title="보고서 템플릿 검증",
        summary="리포트 필수 항목 검증",
        board_id="B07",
        zone_id="D",
    )
    sim_result = run_simulation(seed=seed, rounds=4, corpus=["샘플"], packs=packs)

    report = build_report_v1(seed, sim_result, packs)

    assert report["schema_version"] == "report.v1"
    assert len(report["lens_summaries"]) == 4
    assert 1 <= len(report["highlights_top10"]) <= 10
    assert report["conflict_map"]["claim_a"]
    assert report["conflict_map"]["claim_b"]
    assert report["conflict_map"]["third_interest"]
    assert len(report["dialogue_candidates"]) >= 3
    assert len(report["dialogue_candidates"]) <= 5
    assert report["foreshadowing"]
    assert report["risk_checks"]
