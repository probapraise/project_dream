from pathlib import Path

from project_dream.models import SeedInput
from project_dream.pack_service import load_packs
from project_dream.persona_service import apply_register_switch, render_voice, select_participants


def test_select_participants_prefers_board_zone_personas():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    seed = SeedInput(
        seed_id="SEED-PER-001",
        title="장터 분쟁",
        summary="거래 글에서 증거 충돌이 난다",
        board_id="B07",
        zone_id="D",
    )

    participants = select_participants(seed, round_idx=1, packs=packs)

    assert participants
    assert participants[0] in {"P07", "P08"}
    assert participants[1] in {"P07", "P08"}
    assert len(set(participants)) == len(participants)


def test_select_participants_fallback_without_packs():
    seed = SeedInput(seed_id="SEED-PER-002", title="사건", summary="요약", board_id="B01", zone_id="A")

    participants = select_participants(seed, round_idx=2)

    assert participants
    assert participants[0].startswith("AG-")


def test_render_voice_returns_constraints():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    voice = render_voice("P07", "D", packs=packs)

    assert voice["sentence_length"] in {"short", "medium", "long"}
    assert voice["endings"]
    assert voice["frequent_words"]
    assert isinstance(voice["taboo_words"], list)


def test_apply_register_switch_uses_pack_rules_and_profiles():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    base_voice = render_voice("P07", "D", packs=packs)

    switched = apply_register_switch(
        base_voice,
        persona_id="P07",
        packs=packs,
        runtime_context={
            "round_idx": 2,
            "dial_dominant_axis": "H",
            "meme_phase": "factory_amplify",
            "status": "visible",
            "total_reports": 0,
            "evidence_hours_left": 72,
        },
    )

    assert switched["register_switch_applied"] is True
    assert switched["register_profile_id"] == "REG-AMPLIFY"
    assert switched["register_rule_id"] == "RR-HYPE-AMPLIFY"
    assert "짤로간다" in switched["endings"]


def test_apply_register_switch_keeps_base_voice_when_no_rule_matches():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    base_voice = render_voice("P07", "D", packs=packs)

    switched = apply_register_switch(
        base_voice,
        persona_id="P07",
        packs=packs,
        runtime_context={
            "round_idx": 1,
            "dial_dominant_axis": "E",
            "meme_phase": "hub_to_factory",
            "status": "visible",
            "total_reports": 0,
            "evidence_hours_left": 72,
        },
    )

    assert switched["register_switch_applied"] is False
    assert switched["register_rule_id"] == ""
