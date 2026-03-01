from pathlib import Path
from project_dream.pack_service import load_packs


def test_pack_service_validates_board_reference():
    packs = load_packs(Path("tests/fixtures/packs"))
    assert "B01" in packs.boards
    assert packs.communities["COM-PLZ-001"]["board_id"] == "B01"


def test_pack_service_includes_template_flow_runtime_fields():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    template = packs.thread_templates["T5"]
    flow = packs.comment_flows["P5"]

    assert isinstance(template.get("title_patterns"), list)
    assert template["title_patterns"]
    assert isinstance(template.get("trigger_tags"), list)
    assert template["trigger_tags"]
    assert isinstance(template.get("taboos"), list)

    assert isinstance(flow.get("body_sections"), list)
    assert flow["body_sections"]
    assert isinstance(flow.get("escalation_rules"), list)
    assert flow["escalation_rules"]
    first_rule = flow["escalation_rules"][0]
    assert {"condition", "action_type", "reason_rule_id"} <= set(first_rule.keys())


def test_pack_service_loads_event_cards_and_meme_seeds():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    assert packs.event_cards
    assert packs.meme_seeds

    first_event = next(iter(packs.event_cards.values()))
    first_meme = next(iter(packs.meme_seeds.values()))
    assert "id" in first_event
    assert "id" in first_meme


def test_pack_service_loads_gate_policy_from_rule_pack():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    assert isinstance(packs.gate_policy, dict)
    assert "safety" in packs.gate_policy
    assert "lore" in packs.gate_policy

    safety = packs.gate_policy["safety"]
    lore = packs.gate_policy["lore"]
    assert isinstance(safety.get("taboo_words"), list)
    assert isinstance(lore.get("evidence_keywords"), list)
    assert isinstance(lore.get("contradiction_term_groups"), list)


def test_pack_service_exposes_manifest_and_fingerprint():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    assert isinstance(packs.pack_manifest, dict)
    assert packs.pack_manifest["schema_version"] == "pack_manifest.v1"
    assert packs.pack_manifest["checksum_algorithm"] == "sha256"
    assert isinstance(packs.pack_fingerprint, str)
    assert len(packs.pack_fingerprint) == 64
