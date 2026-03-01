import json
import hashlib
from dataclasses import dataclass
from pathlib import Path

from project_dream.pack_schemas import (
    BoardPackPayload,
    CommunityPackPayload,
    EntityPackPayload,
    PackManifestPayload,
    PersonaPackPayload,
    RulePackPayload,
    TemplatePackPayload,
    WorldPackPayload,
    validate_pack_payload,
)


@dataclass
class LoadedPacks:
    boards: dict[str, dict]
    communities: dict[str, dict]
    rules: dict[str, dict]
    orgs: dict[str, dict]
    chars: dict[str, dict]
    archetypes: dict[str, dict]
    personas: dict[str, dict]
    register_profiles: dict[str, dict]
    register_switch_rules: list[dict]
    thread_templates: dict[str, dict]
    comment_flows: dict[str, dict]
    event_cards: dict[str, dict]
    meme_seeds: dict[str, dict]
    world_schema: dict
    gate_policy: dict
    pack_manifest: dict
    pack_fingerprint: str


_FLOW_TABOO_HINTS = {
    "P1": ["realname_dox", "signature_dox"],
    "P3": ["patient_dox", "panic_false_alarm"],
    "P4": ["appeal_dox", "bypass_guide"],
    "P5": ["illegal_trade", "fake_review"],
    "P6": ["realname_mock", "death_mocking"],
}
_PACK_FILE_NAMES = (
    "board_pack.json",
    "community_pack.json",
    "rule_pack.json",
    "entity_pack.json",
    "persona_pack.json",
    "template_pack.json",
    "world_pack.json",
)
_ALLOWED_DIAL_AXES = {"U", "E", "M", "S", "H"}
_ALLOWED_STATUS_VALUES = {"visible", "hidden", "locked", "ghost", "sanctioned"}


def _read_pack(path: Path, default_key: str) -> dict:
    if not path.exists():
        return {default_key: []}
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"Pack manifest referenced missing file: {path.name}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_manifest_fingerprint(manifest: dict) -> str:
    files = manifest.get("files", {})
    normalized_files = {}
    if isinstance(files, dict):
        for key in sorted(files.keys()):
            normalized_files[str(key)] = str(files.get(key, ""))
    normalized = {
        "schema_version": str(manifest.get("schema_version", "pack_manifest.v1")),
        "pack_version": str(manifest.get("pack_version", "1.0.0")),
        "checksum_algorithm": str(manifest.get("checksum_algorithm", "sha256")),
        "files": normalized_files,
    }
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_manifest_from_disk(base_dir: Path) -> dict:
    files: dict[str, str] = {}
    for filename in _PACK_FILE_NAMES:
        path = base_dir / filename
        if path.exists():
            files[filename] = _sha256_file(path)
    return {
        "schema_version": "pack_manifest.v1",
        "pack_version": "1.0.0",
        "checksum_algorithm": "sha256",
        "files": files,
    }


def write_pack_manifest(base_dir: Path, *, pack_version: str | None = None) -> dict:
    manifest = _build_manifest_from_disk(base_dir)
    if pack_version:
        manifest["pack_version"] = str(pack_version)
    else:
        existing_path = base_dir / "pack_manifest.json"
        if existing_path.exists():
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            existing_version = str(existing.get("pack_version", "")).strip()
            if existing_version:
                manifest["pack_version"] = existing_version
    manifest = validate_pack_payload(manifest, PackManifestPayload, "pack_manifest.json")
    (base_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def _load_and_verify_manifest(base_dir: Path) -> tuple[dict, str]:
    manifest_path = base_dir / "pack_manifest.json"
    if not manifest_path.exists():
        fallback_manifest = _build_manifest_from_disk(base_dir)
        return fallback_manifest, _build_manifest_fingerprint(fallback_manifest)

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = validate_pack_payload(raw_manifest, PackManifestPayload, "pack_manifest.json")
    algorithm = str(manifest.get("checksum_algorithm", "")).strip().lower()
    if algorithm != "sha256":
        raise ValueError(f"Unsupported pack manifest checksum algorithm: {algorithm}")

    manifest_files = manifest.get("files", {})
    if not isinstance(manifest_files, dict):
        raise ValueError("Invalid pack manifest files payload")

    for filename in _PACK_FILE_NAMES:
        expected = str(manifest_files.get(filename, "")).strip().lower()
        if not expected:
            raise ValueError(f"Pack manifest missing checksum: {filename}")
        actual = _sha256_file(base_dir / filename)
        if actual != expected:
            raise ValueError(f"Pack manifest checksum mismatch: {filename}")

    return manifest, _build_manifest_fingerprint(manifest)


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


def _normalize_gate_policy(raw_policy: dict) -> dict:
    safety_raw = raw_policy.get("safety", {}) if isinstance(raw_policy, dict) else {}
    lore_raw = raw_policy.get("lore", {}) if isinstance(raw_policy, dict) else {}
    similarity_raw = raw_policy.get("similarity", {}) if isinstance(raw_policy, dict) else {}
    contradiction_groups_raw = (
        lore_raw.get("contradiction_term_groups", [])
        if isinstance(lore_raw, dict)
        else []
    )
    contradiction_term_groups: list[dict] = []
    if isinstance(contradiction_groups_raw, list):
        for group in contradiction_groups_raw:
            if not isinstance(group, dict):
                continue
            positives = _as_str_list(group.get("positives"))
            negatives = _as_str_list(group.get("negatives"))
            if not positives or not negatives:
                continue
            contradiction_term_groups.append({"positives": positives, "negatives": negatives})

    taboo_words = _as_str_list(safety_raw.get("taboo_words"))
    if not taboo_words:
        taboo_words = ["실명", "서명 단서", "사망 조롱"]
    evidence_keywords = _as_str_list(lore_raw.get("evidence_keywords"))
    if not evidence_keywords:
        evidence_keywords = ["정본", "증거", "로그", "출처", "근거"]
    context_keywords = _as_str_list(lore_raw.get("context_keywords"))
    if not context_keywords:
        context_keywords = ["주장", "판단", "사실", "정황", "의혹"]
    claim_markers = _as_str_list(lore_raw.get("claim_markers"))
    if not claim_markers:
        claim_markers = ["확정", "추정", "의혹", "단정"]
    moderation_keywords = _as_str_list(lore_raw.get("moderation_keywords"))
    if not moderation_keywords:
        moderation_keywords = ["운영", "관리자", "모더레이터"]
    if not contradiction_term_groups:
        contradiction_term_groups = [
            {"positives": ["확정", "단정"], "negatives": ["추정", "의혹", "가능성"]},
            {"positives": ["사실"], "negatives": ["루머", "소문"]},
        ]

    return {
        "safety": {
            "phone_pattern": str(safety_raw.get("phone_pattern", r"01[0-9]-\d{3,4}-\d{4}")).strip()
            or r"01[0-9]-\d{3,4}-\d{4}",
            "taboo_words": taboo_words,
            "rule_ids": dict(safety_raw.get("rule_ids", {}))
            if isinstance(safety_raw.get("rule_ids"), dict)
            else {},
        },
        "lore": {
            "evidence_keywords": evidence_keywords,
            "context_keywords": context_keywords,
            "claim_markers": claim_markers,
            "moderation_keywords": moderation_keywords,
            "contradiction_term_groups": contradiction_term_groups,
            "rule_ids": dict(lore_raw.get("rule_ids", {}))
            if isinstance(lore_raw.get("rule_ids"), dict)
            else {},
        },
        "similarity": {
            "rule_ids": dict(similarity_raw.get("rule_ids", {}))
            if isinstance(similarity_raw.get("rule_ids"), dict)
            else {},
        },
    }


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
    pack_manifest, pack_fingerprint = _load_and_verify_manifest(base_dir)

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
    world_pack = validate_pack_payload(
        _read_pack(base_dir / "world_pack.json", "entities"),
        WorldPackPayload,
        "world_pack.json",
    )

    boards = _index_by_id(board_pack["boards"], "board")
    communities = _index_by_id(community_pack["communities"], "community")
    rules = _index_by_id(rule_pack.get("rules", []), "rule")
    gate_policy = _normalize_gate_policy(rule_pack.get("gate_policy", {}))
    orgs = _index_by_id(entity_pack.get("orgs", []), "org")
    chars = _index_by_id(entity_pack.get("chars", []), "char")
    archetypes = _index_by_id(persona_pack.get("archetypes", []), "archetype")
    personas = _index_by_id(persona_pack.get("personas", []), "persona")
    register_profiles = _index_by_id(persona_pack.get("register_profiles", []), "register_profile")
    register_switch_rules = sorted(
        [
            dict(rule)
            for rule in persona_pack.get("register_switch_rules", [])
            if isinstance(rule, dict)
        ],
        key=lambda row: (-int(row.get("priority", 0)), str(row.get("id", ""))),
    )
    raw_thread_templates = _index_by_id(template_pack.get("thread_templates", []), "thread_template")
    raw_comment_flows = _index_by_id(template_pack.get("comment_flows", []), "comment_flow")
    event_cards = _index_by_id(template_pack.get("event_cards", []), "event_card")
    meme_seeds = _index_by_id(template_pack.get("meme_seeds", []), "meme_seed")
    world_entities = _index_by_id(world_pack.get("entities", []), "world_entity")
    world_relations = [
        dict(row) for row in world_pack.get("relations", []) if isinstance(row, dict)
    ]
    world_timeline_events = [
        dict(row) for row in world_pack.get("timeline_events", []) if isinstance(row, dict)
    ]
    world_rules = [
        dict(row) for row in world_pack.get("world_rules", []) if isinstance(row, dict)
    ]
    world_glossary = [
        dict(row) for row in world_pack.get("glossary", []) if isinstance(row, dict)
    ]
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
        archetype_id = str(persona.get("archetype_id", "")).strip()
        if archetype_id and archetype_id not in archetypes:
            raise ValueError(f"Unknown archetype_id for persona {persona['id']}: {archetype_id}")

    for archetype in archetypes.values():
        default_profile_id = str(archetype.get("default_register_profile_id", "")).strip()
        if default_profile_id and default_profile_id not in register_profiles:
            raise ValueError(
                f"Unknown default_register_profile_id for archetype {archetype['id']}: {default_profile_id}"
            )

    for rule in register_switch_rules:
        profile_id = str(rule.get("apply_profile_id", "")).strip()
        if profile_id not in register_profiles:
            raise ValueError(f"Unknown register_profile_id in register_switch_rule {rule.get('id', '')}: {profile_id}")
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            conditions = {}
        for archetype_id in _as_str_list(conditions.get("archetype_ids")):
            if archetype_id not in archetypes:
                raise ValueError(
                    f"Unknown archetype_id in register_switch_rule {rule.get('id', '')}: {archetype_id}"
                )
        for axis in _as_str_list(conditions.get("dial_axis_in")):
            if axis not in _ALLOWED_DIAL_AXES:
                raise ValueError(f"Unknown dial axis in register_switch_rule {rule.get('id', '')}: {axis}")
        for status in _as_str_list(conditions.get("status_in")):
            if status not in _ALLOWED_STATUS_VALUES:
                raise ValueError(f"Unknown status in register_switch_rule {rule.get('id', '')}: {status}")

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

    for entity in world_entities.values():
        linked_org_id = str(entity.get("linked_org_id", "")).strip()
        if linked_org_id and linked_org_id not in orgs:
            raise ValueError(f"Unknown linked_org_id in world entity {entity['id']}: {linked_org_id}")
        linked_char_id = str(entity.get("linked_char_id", "")).strip()
        if linked_char_id and linked_char_id not in chars:
            raise ValueError(f"Unknown linked_char_id in world entity {entity['id']}: {linked_char_id}")
        linked_board_id = str(entity.get("linked_board_id", "")).strip()
        if linked_board_id and linked_board_id not in boards:
            raise ValueError(f"Unknown linked_board_id in world entity {entity['id']}: {linked_board_id}")

    for relation in world_relations:
        relation_id = str(relation.get("id", "")).strip() or "(unknown)"
        from_entity_id = str(relation.get("from_entity_id", "")).strip()
        to_entity_id = str(relation.get("to_entity_id", "")).strip()
        if from_entity_id not in world_entities:
            raise ValueError(f"Unknown from_entity_id in world relation {relation_id}: {from_entity_id}")
        if to_entity_id not in world_entities:
            raise ValueError(f"Unknown to_entity_id in world relation {relation_id}: {to_entity_id}")

    for event in world_timeline_events:
        event_id = str(event.get("id", "")).strip() or "(unknown)"
        for entity_id in _as_str_list(event.get("entity_ids")):
            if entity_id not in world_entities:
                raise ValueError(f"Unknown entity_id in world timeline event {event_id}: {entity_id}")
        location_entity_id = str(event.get("location_entity_id", "")).strip()
        if location_entity_id and location_entity_id not in world_entities:
            raise ValueError(
                f"Unknown location_entity_id in world timeline event {event_id}: {location_entity_id}"
            )

    for world_rule in world_rules:
        rule_id = str(world_rule.get("id", "")).strip() or "(unknown)"
        for entity_id in _as_str_list(world_rule.get("scope_entity_ids")):
            if entity_id not in world_entities:
                raise ValueError(f"Unknown scope_entity_id in world rule {rule_id}: {entity_id}")

    world_schema = {
        "schema_version": str(world_pack.get("schema_version", "world_schema.v1")),
        "version": str(world_pack.get("version", "1.0.0")),
        "forbidden_terms": _as_str_list(world_pack.get("forbidden_terms")),
        "relation_conflict_rules": [
            dict(row) for row in world_pack.get("relation_conflict_rules", []) if isinstance(row, dict)
        ],
        "entities": list(world_entities.values()),
        "relations": world_relations,
        "timeline_events": world_timeline_events,
        "world_rules": world_rules,
        "glossary": world_glossary,
    }

    packs = LoadedPacks(
        boards=boards,
        communities=communities,
        rules=rules,
        orgs=orgs,
        chars=chars,
        archetypes=archetypes,
        personas=personas,
        register_profiles=register_profiles,
        register_switch_rules=register_switch_rules,
        thread_templates=thread_templates,
        comment_flows=comment_flows,
        event_cards=event_cards,
        meme_seeds=meme_seeds,
        world_schema=world_schema,
        gate_policy=gate_policy,
        pack_manifest=pack_manifest,
        pack_fingerprint=pack_fingerprint,
    )

    if enforce_phase1_minimums:
        _validate_minimum_requirements(packs)
    return packs
