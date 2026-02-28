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
