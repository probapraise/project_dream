from pydantic import BaseModel, Field


class Dial(BaseModel):
    U: int = 30
    E: int = 25
    M: int = 15
    S: int = 15
    H: int = 15


class EpisodeSeed(BaseModel):
    seed_id: str
    title: str
    summary: str
    board_id: str
    zone_id: str
    dial: Dial = Field(default_factory=Dial)
    public_facts: list[str] = Field(default_factory=list)
    hidden_facts: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    sensitivity_tags: list[str] = Field(default_factory=list)
    evidence_grade: str = "B"
    evidence_type: str = "log"
    evidence_expiry_hours: int = 72


class SeedInput(EpisodeSeed):
    pass


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    reason: str
    rewritten_text: str | None = None


class ReportConflictMap(BaseModel):
    claim_a: str
    claim_b: str
    third_interest: str
    mediation_points: list[str]


class ReportRiskCheck(BaseModel):
    category: str
    severity: str
    details: str


class ReportV1(BaseModel):
    schema_version: str = "report.v1"
    seed_id: str
    title: str
    summary: str
    lens_summaries: list[dict]
    highlights_top10: list[dict]
    conflict_map: ReportConflictMap
    dialogue_candidates: list[dict]
    foreshadowing: list[str]
    risk_checks: list[ReportRiskCheck]
    seed_constraints: dict = Field(default_factory=dict)
    evidence_watch: dict = Field(default_factory=dict)


class EvalCheck(BaseModel):
    name: str
    passed: bool
    details: str


class EvalResult(BaseModel):
    schema_version: str = "eval.v1"
    metric_set: str = "v1"
    run_id: str
    seed_id: str
    pass_fail: bool
    checks: list[EvalCheck]
    metrics: dict[str, int | float]
