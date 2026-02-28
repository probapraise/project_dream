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
    assert "report_gate" in report
    assert report["report_gate"]["schema_version"] == "report_gate.v1"
    assert report["report_gate"]["pass_fail"] is True


def test_report_v1_accepts_custom_llm_client_for_summary_and_dialogue():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate(self, prompt: str, *, task: str) -> str:
            self.calls.append({"prompt": prompt, "task": task})
            if task == "report_summary":
                return "FAKE REPORT SUMMARY"
            if task == "report_dialogue_candidate":
                return f"FAKE LINE::{prompt}"
            return prompt

    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-RPT-002",
        title="리포트 LLM 경계 검증",
        summary="요약 대체",
        board_id="B07",
        zone_id="D",
    )
    sim_result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)
    fake_client = FakeClient()

    report = build_report_v1(seed, sim_result, packs, llm_client=fake_client)

    assert report["summary"] == "FAKE REPORT SUMMARY"
    assert report["dialogue_candidates"]
    assert all(item["line"].startswith("FAKE LINE::") for item in report["dialogue_candidates"])
    assert any(call["task"] == "report_summary" for call in fake_client.calls)
    dialogue_calls = [call for call in fake_client.calls if call["task"] == "report_dialogue_candidate"]
    assert len(dialogue_calls) == len(report["dialogue_candidates"])
    assert report["report_gate"]["schema_version"] == "report_gate.v1"


def test_report_v1_includes_seed_constraints_summary():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-RPT-003",
        title="시드 제약 반영",
        summary="금지어와 민감도 태그 반영 확인",
        board_id="B07",
        zone_id="D",
        public_facts=["공개 A"],
        hidden_facts=["숨김 B"],
        stakeholders=["이해관계자 C"],
        forbidden_terms=["실명노출"],
        sensitivity_tags=["privacy"],
    )
    sim_result = run_simulation(seed=seed, rounds=3, corpus=["샘플"], packs=packs)

    report = build_report_v1(seed, sim_result, packs)

    assert "seed_constraints" in report
    constraints = report["seed_constraints"]
    assert constraints["forbidden_terms"] == ["실명노출"]
    assert constraints["sensitivity_tags"] == ["privacy"]
    assert constraints["has_hidden_facts"] is True


def test_report_v1_includes_evidence_watch_fields():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-RPT-004",
        title="증거 등급 리포트 반영",
        summary="카운트다운/증거 등급을 리포트에 표시한다",
        board_id="B07",
        zone_id="D",
        evidence_grade="C",
        evidence_type="rumor_capture",
        evidence_expiry_hours=12,
    )
    sim_result = run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=packs)

    report = build_report_v1(seed, sim_result, packs)

    assert "evidence_watch" in report
    watch = report["evidence_watch"]
    assert watch["grade"] == "C"
    assert watch["type"] == "rumor_capture"
    assert watch["expires_in_hours"] == 12
    assert any(item["category"] == "evidence" for item in report["risk_checks"])
