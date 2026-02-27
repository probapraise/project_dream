from pydantic import BaseModel, Field


class Dial(BaseModel):
    U: int = 30
    E: int = 25
    M: int = 15
    S: int = 15
    H: int = 15


class SeedInput(BaseModel):
    seed_id: str
    title: str
    summary: str
    board_id: str
    zone_id: str
    dial: Dial = Field(default_factory=Dial)


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


class EvalCheck(BaseModel):
    name: str
    passed: bool
    details: str


class EvalResult(BaseModel):
    schema_version: str = "eval.v1"
    run_id: str
    seed_id: str
    pass_fail: bool
    checks: list[EvalCheck]
    metrics: dict[str, int | float]
