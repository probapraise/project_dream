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


class BoardPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    boards: list[BoardRow] = Field(default_factory=list)


class CommunityPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    communities: list[CommunityRow] = Field(default_factory=list)


class RulePackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    rules: list[RuleRow] = Field(default_factory=list)


class EntityPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    orgs: list[OrgRow] = Field(default_factory=list)
    chars: list[CharRow] = Field(default_factory=list)


class PersonaPackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    archetypes: list[dict] = Field(default_factory=list)
    personas: list[PersonaRow] = Field(default_factory=list)


class TemplatePackPayload(_StrictModel):
    version: StrictStr = "1.0.0"
    thread_templates: list[ThreadTemplateRow] = Field(default_factory=list)
    comment_flows: list[CommentFlowRow] = Field(default_factory=list)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def validate_pack_payload(payload: dict, model_cls: type[_ModelT], pack_name: str) -> dict:
    try:
        model = model_cls.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid {pack_name} schema: {exc}") from exc
    return model.model_dump()
