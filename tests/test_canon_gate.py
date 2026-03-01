from pathlib import Path

import pytest

from project_dream.canon_gate import enforce_canon_gate, run_canon_gate
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs


def _seed(*, summary: str = "거래 기록과 증거 로그를 기반으로 검증 진행") -> SeedInput:
    return SeedInput(
        seed_id="SEED-CANON-001",
        title="장터 거래 분쟁",
        summary=summary,
        board_id="B07",
        zone_id="D",
    )


def test_run_canon_gate_passes_for_valid_world_and_seed():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    result = run_canon_gate(seed=_seed(), packs=packs)

    assert result["pass_fail"] is True
    assert result["checks"]
    assert all(bool(row.get("passed")) for row in result["checks"])


def test_run_canon_gate_fails_when_seed_contains_forbidden_term():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = _seed(summary="금서 원문을 복제해서 배포하자는 제안이 올라왔다")

    result = run_canon_gate(seed=seed, packs=packs)

    assert result["pass_fail"] is False
    forbidden_check = next(row for row in result["checks"] if row.get("name") == "canon.seed_forbidden_terms")
    assert forbidden_check["passed"] is False
    assert "금서 원문" in forbidden_check["details"]


def test_run_canon_gate_fails_on_timeline_inversion():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    packs.world_schema["entities"][0]["valid_from"] = "Y30"
    packs.world_schema["entities"][0]["valid_to"] = "Y10"

    result = run_canon_gate(seed=_seed(), packs=packs)

    assert result["pass_fail"] is False
    timeline_check = next(row for row in result["checks"] if row.get("name") == "canon.timeline_consistency")
    assert timeline_check["passed"] is False
    assert "valid_from>valid_to" in timeline_check["details"]


def test_run_canon_gate_fails_on_relation_conflict():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    packs.world_schema["relations"].append(
        {
            "id": "WR-CONFLICT-001",
            "relation_type": "hostile_to",
            "from_entity_id": "WE-FACTION-ACADEMY",
            "to_entity_id": "WE-FACTION-MERCHANT",
            "notes": "규제권력과 시장권력의 공개적 적대",
            "source": "canon.rumor.board",
            "valid_from": "Y172-Q2",
            "valid_to": "",
            "evidence_grade": "B",
        }
    )

    result = run_canon_gate(seed=_seed(), packs=packs)

    assert result["pass_fail"] is False
    conflict_check = next(row for row in result["checks"] if row.get("name") == "canon.relation_conflicts")
    assert conflict_check["passed"] is False
    assert "WE-FACTION-ACADEMY->WE-FACTION-MERCHANT" in conflict_check["details"]


def test_enforce_canon_gate_raises_on_failure():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = _seed(summary="금서 원문을 유출해서 돌리자는 제안")

    with pytest.raises(ValueError, match="Canon gate failed"):
        enforce_canon_gate(seed=seed, packs=packs)
