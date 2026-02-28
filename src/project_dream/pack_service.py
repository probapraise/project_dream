import json
from dataclasses import dataclass
from pathlib import Path

from project_dream.pack_schemas import (
    BoardPackPayload,
    CommunityPackPayload,
    EntityPackPayload,
    PersonaPackPayload,
    RulePackPayload,
    TemplatePackPayload,
    validate_pack_payload,
)


@dataclass
class LoadedPacks:
    boards: dict[str, dict]
    communities: dict[str, dict]
    rules: dict[str, dict]
    orgs: dict[str, dict]
    chars: dict[str, dict]
    personas: dict[str, dict]
    thread_templates: dict[str, dict]
    comment_flows: dict[str, dict]
    event_cards: dict[str, dict]
    meme_seeds: dict[str, dict]


_FLOW_TABOO_HINTS = {
    "P1": ["realname_dox", "signature_dox"],
    "P3": ["patient_dox", "panic_false_alarm"],
    "P4": ["appeal_dox", "bypass_guide"],
    "P5": ["illegal_trade", "fake_review"],
    "P6": ["realname_mock", "death_mocking"],
}


def _read_pack(path: Path, default_key: str) -> dict:
    if not path.exists():
        return {default_key: []}
    return json.loads(path.read_text(encoding="utf-8"))


def _index_by_id(items: list[dict], name: str) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        item_id = item["id"]
        if item_id in indexed:
            raise ValueError(f"Duplicated {name} id: {item_id}")
        indexed[item_id] = item
    return indexed


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _default_title_patterns(template: dict) -> list[str]:
    name = str(template.get("name", "템플릿")).strip()
    return [
        f"[{name}] {{title}}",
        "{title} | {summary}",
        "{title}",
    ]


def _default_trigger_tags(template: dict) -> list[str]:
    template_id = str(template.get("id", "")).strip().lower()
    flow_id = str(template.get("default_comment_flow", "")).strip().lower()
    board_tags = [f"board:{str(board_id).lower()}" for board_id in _as_str_list(template.get("intended_boards"))[:2]]
    base = board_tags + [f"template:{template_id}"] if template_id else board_tags
    if flow_id:
        base.append(f"flow:{flow_id}")
    return _unique([tag for tag in base if tag])


def _default_template_taboos(template: dict, boards: dict[str, dict]) -> list[str]:
    flow_id = str(template.get("default_comment_flow", "")).strip()
    board_taboos: list[str] = []
    for board_id in _as_str_list(template.get("intended_boards")):
        board = boards.get(board_id)
        if not board:
            continue
        board_taboos.extend(_as_str_list(board.get("taboos")))
    hinted = _FLOW_TABOO_HINTS.get(flow_id, [])
    return _unique(board_taboos[:2] + hinted[:2])


def _normalize_thread_template(template: dict, *, boards: dict[str, dict]) -> dict:
    out = dict(template)
    title_patterns = _as_str_list(out.get("title_patterns")) or _default_title_patterns(out)
    trigger_tags = _as_str_list(out.get("trigger_tags")) or _default_trigger_tags(out)
    taboos = _as_str_list(out.get("taboos")) or _default_template_taboos(out, boards)

    out["title_patterns"] = title_patterns
    out["trigger_tags"] = trigger_tags
    out["taboos"] = taboos
    return out


def _default_body_sections(flow: dict) -> list[str]:
    phases = _as_str_list(flow.get("phases"))
    sections: list[str] = []
    for phase in phases:
        if ":" in phase:
            sections.append(phase.split(":", 1)[1].strip())
        else:
            sections.append(phase)
    sections = [section for section in sections if section]
    if sections:
        return sections
    return ["상황정리", "근거정리", "요청/정리"]


def _default_escalation_rules(flow: dict) -> list[dict]:
    flow_id = str(flow.get("id", "")).strip()
    rules = [
        {
            "condition": {"reports_gte": 8},
            "action_type": "FLOW_ESCALATE_REVIEW",
            "reason_rule_id": "RULE-PLZ-MOD-01",
        },
        {
            "condition": {"reports_gte": 16},
            "action_type": "FLOW_ESCALATE_LOCK_HINT",
            "reason_rule_id": "RULE-PLZ-MOD-02",
        },
    ]
    if flow_id == "P4":
        rules.append(
            {
                "condition": {"reports_gte": 10, "round_gte": 2},
                "action_type": "FLOW_ESCALATE_APPEAL_TRACK",
                "reason_rule_id": "RULE-PLZ-SAN-02",
            }
        )
    return rules


def _normalize_comment_flow(flow: dict) -> dict:
    out = dict(flow)
    out["body_sections"] = _as_str_list(out.get("body_sections")) or _default_body_sections(out)
    escalation_rules = out.get("escalation_rules")
    if not isinstance(escalation_rules, list) or not escalation_rules:
        out["escalation_rules"] = _default_escalation_rules(out)
    else:
        normalized_rules: list[dict] = []
        for rule in escalation_rules:
            if not isinstance(rule, dict):
                continue
            condition = rule.get("condition")
            if not isinstance(condition, dict):
                condition = {}
            action_type = str(rule.get("action_type", "")).strip()
            reason_rule_id = str(rule.get("reason_rule_id", "")).strip() or "RULE-PLZ-UI-01"
            if not action_type:
                continue
            normalized_rules.append(
                {
                    "condition": condition,
                    "action_type": action_type,
                    "reason_rule_id": reason_rule_id,
                }
            )
        out["escalation_rules"] = normalized_rules or _default_escalation_rules(out)
    return out


def _validate_minimum_requirements(packs: LoadedPacks) -> None:
    if len(packs.boards) != 18:
        raise ValueError(f"Expected 18 boards, got {len(packs.boards)}")
    if len(packs.communities) != 4:
        raise ValueError(f"Expected 4 communities, got {len(packs.communities)}")
    if len(packs.rules) < 15:
        raise ValueError(f"Expected at least 15 rules, got {len(packs.rules)}")
    if len(packs.orgs) < 5:
        raise ValueError(f"Expected at least 5 orgs, got {len(packs.orgs)}")
    if len(packs.chars) < 10:
        raise ValueError(f"Expected at least 10 chars, got {len(packs.chars)}")


def load_packs(base_dir: Path, enforce_phase1_minimums: bool = False) -> LoadedPacks:
    board_pack = validate_pack_payload(
        _read_pack(base_dir / "board_pack.json", "boards"),
        BoardPackPayload,
        "board_pack.json",
    )
    community_pack = validate_pack_payload(
        _read_pack(base_dir / "community_pack.json", "communities"),
        CommunityPackPayload,
        "community_pack.json",
    )
    rule_pack = validate_pack_payload(
        _read_pack(base_dir / "rule_pack.json", "rules"),
        RulePackPayload,
        "rule_pack.json",
    )
    entity_pack = validate_pack_payload(
        _read_pack(base_dir / "entity_pack.json", "orgs"),
        EntityPackPayload,
        "entity_pack.json",
    )
    persona_pack = validate_pack_payload(
        _read_pack(base_dir / "persona_pack.json", "personas"),
        PersonaPackPayload,
        "persona_pack.json",
    )
    template_pack = validate_pack_payload(
        _read_pack(base_dir / "template_pack.json", "thread_templates"),
        TemplatePackPayload,
        "template_pack.json",
    )

    boards = _index_by_id(board_pack["boards"], "board")
    communities = _index_by_id(community_pack["communities"], "community")
    rules = _index_by_id(rule_pack.get("rules", []), "rule")
    orgs = _index_by_id(entity_pack.get("orgs", []), "org")
    chars = _index_by_id(entity_pack.get("chars", []), "char")
    personas = _index_by_id(persona_pack.get("personas", []), "persona")
    raw_thread_templates = _index_by_id(template_pack.get("thread_templates", []), "thread_template")
    raw_comment_flows = _index_by_id(template_pack.get("comment_flows", []), "comment_flow")
    event_cards = _index_by_id(template_pack.get("event_cards", []), "event_card")
    meme_seeds = _index_by_id(template_pack.get("meme_seeds", []), "meme_seed")
    thread_templates = {
        template_id: _normalize_thread_template(template, boards=boards)
        for template_id, template in raw_thread_templates.items()
    }
    comment_flows = {
        flow_id: _normalize_comment_flow(flow)
        for flow_id, flow in raw_comment_flows.items()
    }

    for com in communities.values():
        board_id = com["board_id"]
        if board_id not in boards:
            raise ValueError(f"Unknown board_id: {board_id}")

    for char in chars.values():
        main_com = char.get("main_com")
        if main_com and main_com not in communities:
            raise ValueError(f"Unknown main_com for char {char['id']}: {main_com}")

    for persona in personas.values():
        main_com = persona.get("main_com")
        if main_com and main_com not in communities:
            raise ValueError(f"Unknown main_com for persona {persona['id']}: {main_com}")
        char_id = persona.get("char_id")
        if char_id and char_id not in chars:
            raise ValueError(f"Unknown char_id for persona {persona['id']}: {char_id}")

    for template in thread_templates.values():
        for board_id in template.get("intended_boards", []):
            if board_id not in boards:
                raise ValueError(f"Unknown intended board_id in template {template['id']}: {board_id}")
        flow_id = template.get("default_comment_flow")
        if flow_id and flow_id not in comment_flows:
            raise ValueError(f"Unknown default_comment_flow in template {template['id']}: {flow_id}")
        for board_id in template.get("crosspost_routes", []):
            if board_id not in boards:
                raise ValueError(f"Unknown crosspost board_id in template {template['id']}: {board_id}")

    for event in event_cards.values():
        for board_id in _as_str_list(event.get("intended_boards")):
            if board_id not in boards:
                raise ValueError(f"Unknown intended board_id in event_card {event['id']}: {board_id}")

    for meme in meme_seeds.values():
        for board_id in _as_str_list(meme.get("intended_boards")):
            if board_id not in boards:
                raise ValueError(f"Unknown intended board_id in meme_seed {meme['id']}: {board_id}")

    packs = LoadedPacks(
        boards=boards,
        communities=communities,
        rules=rules,
        orgs=orgs,
        chars=chars,
        personas=personas,
        thread_templates=thread_templates,
        comment_flows=comment_flows,
        event_cards=event_cards,
        meme_seeds=meme_seeds,
    )

    if enforce_phase1_minimums:
        _validate_minimum_requirements(packs)
    return packs
