import pytest
from pydantic import ValidationError

from project_dream.models import SeedInput, Dial


def test_seed_input_defaults_and_validation():
    seed = SeedInput(
        seed_id="SEED-001",
        title="중계망 먹통 사건",
        summary="장터기둥이 갑자기 다운됨",
        board_id="B07",
        zone_id="D",
    )
    assert seed.dial == Dial(U=30, E=25, M=15, S=15, H=15)


def test_seed_input_v2_fields_are_supported():
    seed = SeedInput(
        seed_id="SEED-002",
        title="사건 2",
        summary="요약 2",
        board_id="B08",
        zone_id="C",
        public_facts=["공개 사실 A"],
        hidden_facts=["숨김 사실 B"],
        stakeholders=["조직 A", "조직 B"],
        forbidden_terms=["금지어X"],
        sensitivity_tags=["legal", "privacy"],
        evidence_grade="A",
        evidence_type="signed_log",
        evidence_expiry_hours=18,
    )
    assert seed.public_facts == ["공개 사실 A"]
    assert seed.hidden_facts == ["숨김 사실 B"]
    assert seed.stakeholders == ["조직 A", "조직 B"]
    assert seed.forbidden_terms == ["금지어X"]
    assert seed.sensitivity_tags == ["legal", "privacy"]
    assert seed.evidence_grade == "A"
    assert seed.evidence_type == "signed_log"
    assert seed.evidence_expiry_hours == 18


def test_dial_requires_total_sum_100():
    with pytest.raises(ValidationError):
        Dial(U=40, E=30, M=20, S=10, H=10)
