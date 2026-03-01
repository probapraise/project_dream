from __future__ import annotations

import re
from typing import Any

from project_dream.models import SeedInput


_TIME_TAG_RE = re.compile(r"^Y(?P<year>\d+)(?:-Q(?P<quarter>[1-4]))?(?:-M(?P<month>\d{1,2}))?$")


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def _append_check(checks: list[dict], *, name: str, passed: bool, details: str) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "details": str(details).strip(),
        }
    )


def _parse_time_tag(raw: object) -> tuple[bool, int, str]:
    text = str(raw or "").strip()
    if not text:
        return True, 0, ""
    match = _TIME_TAG_RE.fullmatch(text)
    if match is None:
        return False, 0, f"invalid_time_tag:{text}"

    year = int(match.group("year"))
    quarter_raw = match.group("quarter")
    month_raw = match.group("month")
    if quarter_raw and month_raw:
        return False, 0, f"mixed_granularity_time_tag:{text}"

    if month_raw:
        month = int(month_raw)
        if month < 1 or month > 12:
            return False, 0, f"invalid_month_time_tag:{text}"
        return True, (year * 100) + month, ""

    if quarter_raw:
        quarter = int(quarter_raw)
        month = (quarter - 1) * 3 + 1
        return True, (year * 100) + month, ""

    return True, year * 100 + 1, ""


def _collect_time_window_issues(rows: list[dict], *, row_type: str) -> list[str]:
    issues: list[str] = []
    for row in rows:
        row_id = str(row.get("id", "")).strip() or "(unknown)"
        valid_from_ok, valid_from_value, valid_from_error = _parse_time_tag(row.get("valid_from"))
        valid_to_ok, valid_to_value, valid_to_error = _parse_time_tag(row.get("valid_to"))
        if not valid_from_ok:
            issues.append(f"{row_type}:{row_id}:valid_from:{valid_from_error}")
            continue
        if not valid_to_ok:
            issues.append(f"{row_type}:{row_id}:valid_to:{valid_to_error}")
            continue
        if valid_to_value > 0 and valid_from_value > valid_to_value:
            issues.append(f"{row_type}:{row_id}:valid_from>valid_to")
    return issues


def _collect_timeline_era_issues(world_schema: dict) -> list[str]:
    issues: list[str] = []
    for row in _as_dict_list(world_schema.get("timeline_events")):
        row_id = str(row.get("id", "")).strip() or "(unknown)"
        era_ok, era_value, era_error = _parse_time_tag(row.get("era"))
        if not era_ok:
            issues.append(f"timeline_event:{row_id}:era:{era_error}")
            continue

        valid_from_ok, valid_from_value, valid_from_error = _parse_time_tag(row.get("valid_from"))
        valid_to_ok, valid_to_value, valid_to_error = _parse_time_tag(row.get("valid_to"))
        if not valid_from_ok:
            issues.append(f"timeline_event:{row_id}:valid_from:{valid_from_error}")
            continue
        if not valid_to_ok:
            issues.append(f"timeline_event:{row_id}:valid_to:{valid_to_error}")
            continue
        if era_value > 0 and era_value < valid_from_value:
            issues.append(f"timeline_event:{row_id}:era_before_valid_from")
        if era_value > 0 and valid_to_value > 0 and era_value > valid_to_value:
            issues.append(f"timeline_event:{row_id}:era_after_valid_to")
    return issues


def _as_dict_list(values: object) -> list[dict]:
    if not isinstance(values, list):
        return []
    return [row for row in values if isinstance(row, dict)]


def _collect_reference_integrity_issues(world_schema: dict) -> list[str]:
    issues: list[str] = []
    entities = _as_dict_list(world_schema.get("entities"))
    entity_ids = {str(row.get("id", "")).strip() for row in entities if str(row.get("id", "")).strip()}

    for relation in _as_dict_list(world_schema.get("relations")):
        relation_id = str(relation.get("id", "")).strip() or "(unknown)"
        from_entity_id = str(relation.get("from_entity_id", "")).strip()
        to_entity_id = str(relation.get("to_entity_id", "")).strip()
        if from_entity_id not in entity_ids:
            issues.append(f"relation:{relation_id}:from_entity_id:{from_entity_id}")
        if to_entity_id not in entity_ids:
            issues.append(f"relation:{relation_id}:to_entity_id:{to_entity_id}")

    for event in _as_dict_list(world_schema.get("timeline_events")):
        event_id = str(event.get("id", "")).strip() or "(unknown)"
        for entity_id in _as_str_list(event.get("entity_ids")):
            if entity_id not in entity_ids:
                issues.append(f"timeline_event:{event_id}:entity_id:{entity_id}")
        location_entity_id = str(event.get("location_entity_id", "")).strip()
        if location_entity_id and location_entity_id not in entity_ids:
            issues.append(f"timeline_event:{event_id}:location_entity_id:{location_entity_id}")

    for world_rule in _as_dict_list(world_schema.get("world_rules")):
        rule_id = str(world_rule.get("id", "")).strip() or "(unknown)"
        for entity_id in _as_str_list(world_rule.get("scope_entity_ids")):
            if entity_id not in entity_ids:
                issues.append(f"world_rule:{rule_id}:scope_entity_id:{entity_id}")

    return issues


def _collect_relation_conflict_issues(world_schema: dict) -> list[str]:
    issues: list[str] = []
    relations = _as_dict_list(world_schema.get("relations"))
    relation_types_by_edge: dict[tuple[str, str], set[str]] = {}
    for row in relations:
        from_entity_id = str(row.get("from_entity_id", "")).strip()
        to_entity_id = str(row.get("to_entity_id", "")).strip()
        relation_type = str(row.get("relation_type", "")).strip()
        if not from_entity_id or not to_entity_id or not relation_type:
            continue
        edge = (from_entity_id, to_entity_id)
        relation_types_by_edge.setdefault(edge, set()).add(relation_type)

    raw_rules = _as_dict_list(world_schema.get("relation_conflict_rules"))
    if not raw_rules:
        raw_rules = [
            {"id": "DEFAULT-REL-CONFLICT-01", "relation_type_a": "allied_with", "relation_type_b": "hostile_to"},
            {"id": "DEFAULT-REL-CONFLICT-02", "relation_type_a": "regulates", "relation_type_b": "exempts"},
        ]

    for row in raw_rules:
        rule_id = str(row.get("id", "")).strip() or "(unknown)"
        left = str(row.get("relation_type_a", "")).strip()
        right = str(row.get("relation_type_b", "")).strip()
        if not left or not right:
            continue
        for edge, relation_types in relation_types_by_edge.items():
            if left in relation_types and right in relation_types:
                issues.append(f"{rule_id}:{edge[0]}->{edge[1]}:{left}&{right}")
    return issues


def _collect_glossary_conflict_issues(world_schema: dict) -> list[str]:
    issues: list[str] = []
    glossary_rows = _as_dict_list(world_schema.get("glossary"))
    definitions_by_term: dict[str, str] = {}
    first_row_by_term: dict[str, str] = {}

    for row in glossary_rows:
        row_id = str(row.get("id", "")).strip() or "(unknown)"
        definition = str(row.get("definition", "")).strip()
        terms = [str(row.get("term", "")).strip()]
        terms.extend(_as_str_list(row.get("aliases")))
        normalized_terms = [term.lower() for term in terms if term]
        for term in normalized_terms:
            if term not in definitions_by_term:
                definitions_by_term[term] = definition
                first_row_by_term[term] = row_id
                continue
            if definitions_by_term[term] != definition:
                issues.append(f"{term}:{first_row_by_term[term]}!={row_id}")
    return issues


def _build_seed_forbidden_terms(seed: SeedInput | None, world_schema: dict) -> list[str]:
    values: list[str] = []
    values.extend(_as_str_list(world_schema.get("forbidden_terms")))
    if seed is not None:
        values.extend(_as_str_list(seed.forbidden_terms))
    seen: set[str] = set()
    out: list[str] = []
    for term in values:
        lowered = term.lower()
        if not lowered or lowered in seen:
            continue
        seen.add(lowered)
        out.append(term)
    return out


def _collect_seed_forbidden_issues(seed: SeedInput | None, world_schema: dict) -> list[str]:
    if seed is None:
        return []
    forbidden_terms = _build_seed_forbidden_terms(seed, world_schema)
    if not forbidden_terms:
        return []
    search_space_parts = [seed.title, seed.summary]
    search_space_parts.extend(seed.public_facts)
    search_space_parts.extend(seed.hidden_facts)
    search_space = "\n".join(str(row) for row in search_space_parts).lower()

    hits: list[str] = []
    for term in forbidden_terms:
        if term.lower() in search_space:
            hits.append(term)
    return hits


def _short_details(issues: list[str], *, max_items: int = 3) -> str:
    if not issues:
        return "ok"
    head = issues[:max_items]
    details = ", ".join(head)
    remaining = len(issues) - len(head)
    if remaining > 0:
        details += f" (+{remaining} more)"
    return details


def run_canon_gate(*, seed: SeedInput | None, packs: Any) -> dict:
    world_schema = getattr(packs, "world_schema", {})
    if not isinstance(world_schema, dict):
        world_schema = {}

    checks: list[dict] = []

    reference_issues = _collect_reference_integrity_issues(world_schema)
    _append_check(
        checks,
        name="canon.reference_integrity",
        passed=len(reference_issues) == 0,
        details=_short_details(reference_issues),
    )

    timeline_issues: list[str] = []
    timeline_issues.extend(_collect_time_window_issues(_as_dict_list(world_schema.get("entities")), row_type="entity"))
    timeline_issues.extend(
        _collect_time_window_issues(_as_dict_list(world_schema.get("relations")), row_type="relation")
    )
    timeline_issues.extend(
        _collect_time_window_issues(_as_dict_list(world_schema.get("timeline_events")), row_type="timeline_event")
    )
    timeline_issues.extend(
        _collect_time_window_issues(_as_dict_list(world_schema.get("world_rules")), row_type="world_rule")
    )
    timeline_issues.extend(_collect_time_window_issues(_as_dict_list(world_schema.get("glossary")), row_type="glossary"))
    timeline_issues.extend(_collect_timeline_era_issues(world_schema))
    _append_check(
        checks,
        name="canon.timeline_consistency",
        passed=len(timeline_issues) == 0,
        details=_short_details(timeline_issues),
    )

    relation_conflicts = _collect_relation_conflict_issues(world_schema)
    _append_check(
        checks,
        name="canon.relation_conflicts",
        passed=len(relation_conflicts) == 0,
        details=_short_details(relation_conflicts),
    )

    glossary_conflicts = _collect_glossary_conflict_issues(world_schema)
    _append_check(
        checks,
        name="canon.glossary_conflicts",
        passed=len(glossary_conflicts) == 0,
        details=_short_details(glossary_conflicts),
    )

    seed_forbidden_hits = _collect_seed_forbidden_issues(seed, world_schema)
    _append_check(
        checks,
        name="canon.seed_forbidden_terms",
        passed=len(seed_forbidden_hits) == 0,
        details=_short_details(seed_forbidden_hits),
    )

    pass_fail = all(bool(row.get("passed")) for row in checks)
    return {
        "schema_version": "canon_gate.v1",
        "pass_fail": pass_fail,
        "checks": checks,
    }


def enforce_canon_gate(*, seed: SeedInput | None, packs: Any) -> dict:
    result = run_canon_gate(seed=seed, packs=packs)
    if result.get("pass_fail"):
        return result

    failures = [
        row for row in result.get("checks", []) if isinstance(row, dict) and not bool(row.get("passed"))
    ]
    failure_summaries = [
        f"{row.get('name', 'unknown')}: {row.get('details', '')}".strip()
        for row in failures[:3]
    ]
    details = "; ".join(failure_summaries) if failure_summaries else "unknown"
    raise ValueError(f"Canon gate failed: {details}")
