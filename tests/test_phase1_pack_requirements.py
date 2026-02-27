from pathlib import Path

from project_dream.pack_service import load_packs


def test_phase1_pack_minimum_requirements():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    assert len(packs.boards) == 18
    assert len(packs.communities) == 4
    assert len(packs.rules) >= 15
    assert len(packs.orgs) >= 5
    assert len(packs.chars) >= 10
    assert len(packs.thread_templates) == 12
    assert len(packs.comment_flows) == 6


def test_phase1_pack_cross_references():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    for community in packs.communities.values():
        assert community["board_id"] in packs.boards

    for persona in packs.personas.values():
        main_com = persona.get("main_com")
        if main_com:
            assert main_com in packs.communities
