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
