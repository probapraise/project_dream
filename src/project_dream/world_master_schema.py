from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictStr, ValidationError

WorldEvidenceGrade = Literal["A", "B", "C"]
WorldVisibilityLevel = Literal["PUBLIC", "CONFIDENTIAL", "META"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RelationConflictRuleRow(_StrictModel):
    id: StrictStr
    relation_type_a: StrictStr
    relation_type_b: StrictStr


class WorldMasterNodeRow(_StrictModel):
    id: StrictStr
    kind: StrictStr
    name: StrictStr
    summary: StrictStr = ""
    tags: list[StrictStr] = Field(default_factory=list)
    aliases: list[StrictStr] = Field(default_factory=list)
    linked_org_id: StrictStr = ""
    linked_char_id: StrictStr = ""
    linked_board_id: StrictStr = ""
    attributes: dict[StrictStr, Any] = Field(default_factory=dict)
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterEdgeRow(_StrictModel):
    id: StrictStr
    relation_type: StrictStr
    from_id: StrictStr
    to_id: StrictStr
    notes: StrictStr = ""
    qualifiers: dict[StrictStr, Any] = Field(default_factory=dict)
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterEventRow(_StrictModel):
    id: StrictStr
    title: StrictStr
    summary: StrictStr = ""
    era: StrictStr = ""
    participant_ids: list[StrictStr] = Field(default_factory=list)
    location_id: StrictStr = ""
    trigger_ids: list[StrictStr] = Field(default_factory=list)
    consequence_ids: list[StrictStr] = Field(default_factory=list)
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterRuleRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    category: StrictStr = ""
    description: StrictStr = ""
    scope_ids: list[StrictStr] = Field(default_factory=list)
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterGlossaryRow(_StrictModel):
    id: StrictStr
    term: StrictStr
    definition: StrictStr
    aliases: list[StrictStr] = Field(default_factory=list)
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterSourceDocumentRow(_StrictModel):
    id: StrictStr
    title: StrictStr
    source_type: StrictStr
    locator: StrictStr = ""
    published_at: StrictStr = ""
    trust_level: WorldEvidenceGrade = "C"


class WorldMasterClaimRow(_StrictModel):
    id: StrictStr
    subject_id: StrictStr
    predicate: StrictStr
    object_id: StrictStr = ""
    object_literal: StrictStr = ""
    evidence_source_ids: list[StrictStr] = Field(default_factory=list)
    confidence: StrictFloat = 0.5
    source: StrictStr
    valid_from: StrictStr
    valid_to: StrictStr = ""
    evidence_grade: WorldEvidenceGrade = "C"
    visibility: WorldVisibilityLevel = "PUBLIC"


class WorldMasterTaxonomyTermRow(_StrictModel):
    id: StrictStr
    taxonomy: StrictStr
    label: StrictStr
    parent_id: StrictStr = ""
    description: StrictStr = ""


class WorldMasterPayload(_StrictModel):
    schema_version: StrictStr = "world_master.v1"
    version: StrictStr = "1.0.0"
    forbidden_terms: list[StrictStr] = Field(default_factory=list)
    relation_conflict_rules: list[RelationConflictRuleRow] = Field(default_factory=list)
    kind_registry: dict[StrictStr, Any] = Field(default_factory=dict)
    nodes: list[WorldMasterNodeRow] = Field(default_factory=list)
    edges: list[WorldMasterEdgeRow] = Field(default_factory=list)
    events: list[WorldMasterEventRow] = Field(default_factory=list)
    rules: list[WorldMasterRuleRow] = Field(default_factory=list)
    glossary: list[WorldMasterGlossaryRow] = Field(default_factory=list)
    source_documents: list[WorldMasterSourceDocumentRow] = Field(default_factory=list)
    claims: list[WorldMasterClaimRow] = Field(default_factory=list)
    taxonomy_terms: list[WorldMasterTaxonomyTermRow] = Field(default_factory=list)


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def validate_world_master_payload(payload: dict) -> dict:
    try:
        model = WorldMasterPayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid world_master schema: {exc}") from exc

    out = model.model_dump()
    node_ids = {str(row.get("id", "")).strip() for row in out.get("nodes", []) if isinstance(row, dict)}
    if len(node_ids) != len(out.get("nodes", [])):
        raise ValueError("Invalid world_master schema: duplicated node id")
    source_ids = {
        str(row.get("id", "")).strip()
        for row in out.get("source_documents", [])
        if isinstance(row, dict)
    }
    if len(source_ids) != len(out.get("source_documents", [])):
        raise ValueError("Invalid world_master schema: duplicated source_document id")

    for edge in out.get("edges", []):
        if not isinstance(edge, dict):
            continue
        edge_id = str(edge.get("id", "")).strip() or "(unknown)"
        from_id = str(edge.get("from_id", "")).strip()
        to_id = str(edge.get("to_id", "")).strip()
        if from_id not in node_ids:
            raise ValueError(f"Invalid world_master schema: unknown from_id in edge {edge_id}: {from_id}")
        if to_id not in node_ids:
            raise ValueError(f"Invalid world_master schema: unknown to_id in edge {edge_id}: {to_id}")

    for event in out.get("events", []):
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id", "")).strip() or "(unknown)"
        for participant_id in _as_str_list(event.get("participant_ids")):
            if participant_id not in node_ids:
                raise ValueError(
                    f"Invalid world_master schema: unknown participant_id in event {event_id}: {participant_id}"
                )
        location_id = str(event.get("location_id", "")).strip()
        if location_id and location_id not in node_ids:
            raise ValueError(
                f"Invalid world_master schema: unknown location_id in event {event_id}: {location_id}"
            )

    for rule in out.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = str(rule.get("id", "")).strip() or "(unknown)"
        for scope_id in _as_str_list(rule.get("scope_ids")):
            if scope_id not in node_ids:
                raise ValueError(
                    f"Invalid world_master schema: unknown scope_id in rule {rule_id}: {scope_id}"
                )

    for claim in out.get("claims", []):
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("id", "")).strip() or "(unknown)"
        subject_id = str(claim.get("subject_id", "")).strip()
        object_id = str(claim.get("object_id", "")).strip()
        if subject_id not in node_ids:
            raise ValueError(
                f"Invalid world_master schema: unknown subject_id in claim {claim_id}: {subject_id}"
            )
        if object_id and object_id not in node_ids:
            raise ValueError(
                f"Invalid world_master schema: unknown object_id in claim {claim_id}: {object_id}"
            )
        for source_id in _as_str_list(claim.get("evidence_source_ids")):
            if source_id not in source_ids:
                raise ValueError(
                    f"Invalid world_master schema: unknown evidence_source_id in claim {claim_id}: {source_id}"
                )
        confidence = float(claim.get("confidence", 0.0))
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError(
                f"Invalid world_master schema: confidence out of range in claim {claim_id}: {confidence}"
            )

    taxonomy_ids = {
        str(row.get("id", "")).strip() for row in out.get("taxonomy_terms", []) if isinstance(row, dict)
    }
    for row in out.get("taxonomy_terms", []):
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id", "")).strip() or "(unknown)"
        parent_id = str(row.get("parent_id", "")).strip()
        if parent_id and parent_id not in taxonomy_ids:
            raise ValueError(
                f"Invalid world_master schema: unknown parent_id in taxonomy_term {row_id}: {parent_id}"
            )
    return out


def project_world_master_to_world_pack(master_payload: dict) -> dict:
    world_master = validate_world_master_payload(master_payload)

    entities: list[dict] = []
    for node in world_master.get("nodes", []):
        if not isinstance(node, dict):
            continue
        entities.append(
            {
                "id": str(node.get("id", "")).strip(),
                "entity_type": str(node.get("kind", "")).strip(),
                "name": str(node.get("name", "")).strip(),
                "summary": str(node.get("summary", "")).strip(),
                "tags": [str(tag).strip() for tag in node.get("tags", []) if str(tag).strip()],
                "linked_org_id": str(node.get("linked_org_id", "")).strip(),
                "linked_char_id": str(node.get("linked_char_id", "")).strip(),
                "linked_board_id": str(node.get("linked_board_id", "")).strip(),
                "source": str(node.get("source", "")).strip(),
                "valid_from": str(node.get("valid_from", "")).strip(),
                "valid_to": str(node.get("valid_to", "")).strip(),
                "evidence_grade": str(node.get("evidence_grade", "C")).strip(),
            }
        )

    relations: list[dict] = []
    for edge in world_master.get("edges", []):
        if not isinstance(edge, dict):
            continue
        relations.append(
            {
                "id": str(edge.get("id", "")).strip(),
                "relation_type": str(edge.get("relation_type", "")).strip(),
                "from_entity_id": str(edge.get("from_id", "")).strip(),
                "to_entity_id": str(edge.get("to_id", "")).strip(),
                "notes": str(edge.get("notes", "")).strip(),
                "source": str(edge.get("source", "")).strip(),
                "valid_from": str(edge.get("valid_from", "")).strip(),
                "valid_to": str(edge.get("valid_to", "")).strip(),
                "evidence_grade": str(edge.get("evidence_grade", "C")).strip(),
            }
        )

    timeline_events: list[dict] = []
    for event in world_master.get("events", []):
        if not isinstance(event, dict):
            continue
        timeline_events.append(
            {
                "id": str(event.get("id", "")).strip(),
                "title": str(event.get("title", "")).strip(),
                "summary": str(event.get("summary", "")).strip(),
                "era": str(event.get("era", "")).strip(),
                "entity_ids": [str(node_id).strip() for node_id in event.get("participant_ids", []) if str(node_id).strip()],
                "location_entity_id": str(event.get("location_id", "")).strip(),
                "source": str(event.get("source", "")).strip(),
                "valid_from": str(event.get("valid_from", "")).strip(),
                "valid_to": str(event.get("valid_to", "")).strip(),
                "evidence_grade": str(event.get("evidence_grade", "C")).strip(),
            }
        )

    world_rules: list[dict] = []
    for rule in world_master.get("rules", []):
        if not isinstance(rule, dict):
            continue
        world_rules.append(
            {
                "id": str(rule.get("id", "")).strip(),
                "name": str(rule.get("name", "")).strip(),
                "category": str(rule.get("category", "")).strip(),
                "description": str(rule.get("description", "")).strip(),
                "scope_entity_ids": [str(node_id).strip() for node_id in rule.get("scope_ids", []) if str(node_id).strip()],
                "source": str(rule.get("source", "")).strip(),
                "valid_from": str(rule.get("valid_from", "")).strip(),
                "valid_to": str(rule.get("valid_to", "")).strip(),
                "evidence_grade": str(rule.get("evidence_grade", "C")).strip(),
            }
        )

    glossary: list[dict] = []
    for row in world_master.get("glossary", []):
        if not isinstance(row, dict):
            continue
        glossary.append(
            {
                "id": str(row.get("id", "")).strip(),
                "term": str(row.get("term", "")).strip(),
                "definition": str(row.get("definition", "")).strip(),
                "aliases": [str(alias).strip() for alias in row.get("aliases", []) if str(alias).strip()],
                "source": str(row.get("source", "")).strip(),
                "valid_from": str(row.get("valid_from", "")).strip(),
                "valid_to": str(row.get("valid_to", "")).strip(),
                "evidence_grade": str(row.get("evidence_grade", "C")).strip(),
            }
        )

    extensions = {
        "world_master": {
            "schema_version": str(world_master.get("schema_version", "world_master.v1")),
            "kind_registry": dict(world_master.get("kind_registry", {}))
            if isinstance(world_master.get("kind_registry"), dict)
            else {},
            "source_documents": list(world_master.get("source_documents", [])),
            "claims": list(world_master.get("claims", [])),
            "taxonomy_terms": list(world_master.get("taxonomy_terms", [])),
        }
    }

    return {
        "schema_version": "world_schema.v1",
        "version": str(world_master.get("version", "1.0.0")),
        "forbidden_terms": [str(term).strip() for term in world_master.get("forbidden_terms", []) if str(term).strip()],
        "relation_conflict_rules": list(world_master.get("relation_conflict_rules", [])),
        "entities": entities,
        "relations": relations,
        "timeline_events": timeline_events,
        "world_rules": world_rules,
        "glossary": glossary,
        "extensions": extensions,
    }
