import json
from dataclasses import dataclass
from pathlib import Path


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
    board_pack = _read_pack(base_dir / "board_pack.json", "boards")
    community_pack = _read_pack(base_dir / "community_pack.json", "communities")
    rule_pack = _read_pack(base_dir / "rule_pack.json", "rules")
    entity_pack = _read_pack(base_dir / "entity_pack.json", "orgs")
    persona_pack = _read_pack(base_dir / "persona_pack.json", "personas")
    template_pack = _read_pack(base_dir / "template_pack.json", "thread_templates")

    boards = _index_by_id(board_pack["boards"], "board")
    communities = _index_by_id(community_pack["communities"], "community")
    rules = _index_by_id(rule_pack.get("rules", []), "rule")
    orgs = _index_by_id(entity_pack.get("orgs", []), "org")
    chars = _index_by_id(entity_pack.get("chars", []), "char")
    personas = _index_by_id(persona_pack.get("personas", []), "persona")
    thread_templates = _index_by_id(template_pack.get("thread_templates", []), "thread_template")
    comment_flows = _index_by_id(template_pack.get("comment_flows", []), "comment_flow")

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

    packs = LoadedPacks(
        boards=boards,
        communities=communities,
        rules=rules,
        orgs=orgs,
        chars=chars,
        personas=personas,
        thread_templates=thread_templates,
        comment_flows=comment_flows,
    )

    if enforce_phase1_minimums:
        _validate_minimum_requirements(packs)
    return packs
