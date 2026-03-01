from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BoardRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    topic: StrictStr = ""
    emotion: StrictStr = ""
    taboos: list[StrictStr] = Field(default_factory=list)
    memes: list[StrictStr] = Field(default_factory=list)


class CommunityRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    board_id: StrictStr
    zone_id: StrictStr = "A"
    identity: list[StrictStr] = Field(default_factory=list)
    biases: list[StrictStr] = Field(default_factory=list)
    preferred_evidence: list[StrictStr] = Field(default_factory=list)
    taboos: list[StrictStr] = Field(default_factory=list)


class RuleRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    category: StrictStr = ""
    summary: StrictStr = ""


class GateSafetyRuleIds(_StrictModel):
    pii_phone: StrictStr = "RULE-PLZ-SAFE-01"
    taboo_term: StrictStr = "RULE-PLZ-SAFE-02"
    seed_forbidden: StrictStr = "RULE-PLZ-SAFE-03"


class GateLoreRuleIds(_StrictModel):
    evidence_missing: StrictStr = "RULE-PLZ-LORE-01"
    consistency_conflict: StrictStr = "RULE-PLZ-LORE-02"


class ContradictionTermGroup(_StrictModel):
    positives: list[StrictStr] = Field(default_factory=list)
    negatives: list[StrictStr] = Field(default_factory=list)


class GateSafetyPolicy(_StrictModel):
    phone_pattern: StrictStr = r"01[0-9]-\d{3,4}-\d{4}"
    taboo_words: list[StrictStr] = Field(
        default_factory=lambda: ["실명", "서명 단서", "사망 조롱"]
    )
    rule_ids: GateSafetyRuleIds = Field(default_factory=GateSafetyRuleIds)


class GateLorePolicy(_StrictModel):
    evidence_keywords: list[StrictStr] = Field(
        default_factory=lambda: ["정본", "증거", "로그", "출처", "근거"]
    )
    context_keywords: list[StrictStr] = Field(
        default_factory=lambda: ["주장", "판단", "사실", "정황", "의혹"]
    )
    contradiction_term_groups: list[ContradictionTermGroup] = Field(
        default_factory=lambda: [
            ContradictionTermGroup(positives=["확정", "단정"], negatives=["추정", "의혹", "가능성"]),
            ContradictionTermGroup(positives=["사실"], negatives=["루머", "소문"]),
        ]
    )
    rule_ids: GateLoreRuleIds = Field(default_factory=GateLoreRuleIds)


class GatePolicy(_StrictModel):
    safety: GateSafetyPolicy = Field(default_factory=GateSafetyPolicy)
    lore: GateLorePolicy = Field(default_factory=GateLorePolicy)


class OrgRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    tags: list[StrictStr] = Field(default_factory=list)


class CharRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    main_com: StrictStr = ""
    affiliations: list[StrictStr] = Field(default_factory=list)


class PersonaRow(_StrictModel):
    id: StrictStr
    char_id: StrictStr = ""
    archetype_id: StrictStr = ""
    main_com: StrictStr = ""


class ArchetypeRow(_StrictModel):
    id: StrictStr
    name: StrictStr = ""
    style: StrictStr = ""
    default_register_profile_id: StrictStr = ""


class RegisterProfileRow(_StrictModel):
    id: StrictStr
    sentence_length: StrictStr = "medium"
    endings: list[StrictStr] = Field(default_factory=list)
    frequent_words: list[StrictStr] = Field(default_factory=list)
    taboo_words: list[StrictStr] = Field(default_factory=list)


class RegisterSwitchConditions(_StrictModel):
    archetype_ids: list[StrictStr] = Field(default_factory=list)
    dial_axis_in: list[StrictStr] = Field(default_factory=list)
    meme_phase_in: list[StrictStr] = Field(default_factory=list)
    status_in: list[StrictStr] = Field(default_factory=list)
    reports_gte: StrictInt = 0
    evidence_hours_lte: StrictInt = 9999
    round_gte: StrictInt = 0


class RegisterSwitchRuleRow(_StrictModel):
    id: StrictStr
    priority: StrictInt = 0
    apply_profile_id: StrictStr
    conditions: RegisterSwitchConditions = Field(default_factory=RegisterSwitchConditions)


class EscalationCondition(_StrictModel):
    reports_gte: StrictInt = 0
    round_gte: StrictInt = 0
    status_in: list[StrictStr] = Field(default_factory=list)


class EscalationRule(_StrictModel):
    condition: EscalationCondition
    action_type: StrictStr
    reason_rule_id: StrictStr


class ThreadTemplateRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    intended_boards: list[StrictStr] = Field(default_factory=list)
    default_comment_flow: StrictStr = "P1"
    crosspost_routes: list[StrictStr] = Field(default_factory=list)
    title_patterns: list[StrictStr] = Field(default_factory=list)
    trigger_tags: list[StrictStr] = Field(default_factory=list)
    taboos: list[StrictStr] = Field(default_factory=list)


class CommentFlowRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    phases: list[StrictStr] = Field(default_factory=list)
    body_sections: list[StrictStr] = Field(default_factory=list)
    escalation_rules: list[EscalationRule] = Field(default_factory=list)


class EventCardRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    intended_boards: list[StrictStr] = Field(default_factory=list)
    trigger_tags: list[StrictStr] = Field(default_factory=list)
    summary: StrictStr = ""


class MemeSeedRow(_StrictModel):
    id: StrictStr
    name: StrictStr
    intended_boards: list[StrictStr] = Field(default_factory=list)
    style_tags: list[StrictStr] = Field(default_factory=list)
    summary: StrictStr = ""


class BoardPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    boards: list[BoardRow] = Field(default_factory=list)


class CommunityPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    communities: list[CommunityRow] = Field(default_factory=list)


class RulePackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    rules: list[RuleRow] = Field(default_factory=list)
    gate_policy: GatePolicy = Field(default_factory=GatePolicy)


class PackManifestPayload(_StrictModel):
    schema_version: StrictStr = "pack_manifest.v1"
    pack_version: StrictStr = "1.0.0"
    checksum_algorithm: StrictStr = "sha256"
    files: dict[StrictStr, StrictStr] = Field(default_factory=dict)


class EntityPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    orgs: list[OrgRow] = Field(default_factory=list)
    chars: list[CharRow] = Field(default_factory=list)


class PersonaPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    archetypes: list[ArchetypeRow] = Field(default_factory=list)
    personas: list[PersonaRow] = Field(default_factory=list)
    register_profiles: list[RegisterProfileRow] = Field(default_factory=list)
    register_switch_rules: list[RegisterSwitchRuleRow] = Field(default_factory=list)


class TemplatePackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    thread_templates: list[ThreadTemplateRow] = Field(default_factory=list)
    comment_flows: list[CommentFlowRow] = Field(default_factory=list)
    event_cards: list[EventCardRow] = Field(default_factory=list)
    meme_seeds: list[MemeSeedRow] = Field(default_factory=list)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def validate_pack_payload(payload: dict, model_cls: type[_ModelT], pack_name: str) -> dict:
    try:
        model = model_cls.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid {pack_name} schema: {exc}") from exc
    return model.model_dump()
