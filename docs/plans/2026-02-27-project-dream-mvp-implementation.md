# Project Dream MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `dev_spec`의 균형형 최소 세트(MVP)를 Python CLI로 구현하여 Pack 로딩, 3라운드 시뮬레이션, 3중 게이트, 리포트 출력을 단일 실행으로 제공한다.

**Architecture:** 모듈러 모놀리스 구조로 `pack_service`, `gen_engine`, `gate_pipeline`, `env_engine`, `sim_orchestrator`, `report_generator`, `storage`를 분리한다. 엔진 교체를 위해 모듈 간 경계는 Pydantic 모델과 프로토콜에 의존한다.

**Tech Stack:** Python 3.12+, Pydantic v2, argparse, pytest, RapidFuzz

---

`@superpowers/test-driven-development`  
`@superpowers/verification-before-completion`

### Task 1: Bootstrap Python Project + CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/project_dream/__init__.py`
- Create: `src/project_dream/cli.py`
- Create: `tests/test_cli_smoke.py`

**Step 1: Write the failing test**

```python
# tests/test_cli_smoke.py
from project_dream.cli import build_parser


def test_cli_supports_simulate_command():
    parser = build_parser()
    args = parser.parse_args(["simulate", "--seed", "seed.json"])
    assert args.command == "simulate"
    assert args.seed == "seed.json"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_smoke.py::test_cli_supports_simulate_command -v`  
Expected: FAIL with `ModuleNotFoundError` or missing symbol

**Step 3: Write minimal implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "project-dream"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.8", "rapidfuzz>=3.9"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
# src/project_dream/cli.py
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-dream")
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate")
    sim.add_argument("--seed", required=True)
    sim.add_argument("--packs-dir", required=False, default="packs")
    sim.add_argument("--output-dir", required=False, default="runs")
    sim.add_argument("--rounds", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_smoke.py::test_cli_supports_simulate_command -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/project_dream/__init__.py src/project_dream/cli.py tests/test_cli_smoke.py
git commit -m "chore: bootstrap python project and cli skeleton"
```

### Task 2: Define Core Pydantic Models

**Files:**
- Create: `src/project_dream/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
from project_dream.models import SeedInput, Dial


def test_seed_input_defaults_and_validation():
    seed = SeedInput(
        seed_id="SEED-001",
        title="중계망 먹통 사건",
        summary="장터기둥이 갑자기 다운됨",
        board_id="B07",
        zone_id="D",
    )
    assert seed.dial == Dial(U=30, E=25, M=15, S=15, H=15)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_seed_input_defaults_and_validation -v`  
Expected: FAIL due to missing `models.py`

**Step 3: Write minimal implementation**

```python
# src/project_dream/models.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_seed_input_defaults_and_validation -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/models.py tests/test_models.py
git commit -m "feat: add core pydantic models"
```

### Task 3: Implement Pack Service with Reference Validation

**Files:**
- Create: `src/project_dream/pack_service.py`
- Create: `tests/fixtures/packs/board_pack.json`
- Create: `tests/fixtures/packs/community_pack.json`
- Create: `tests/test_pack_service.py`

**Step 1: Write the failing test**

```python
# tests/test_pack_service.py
from pathlib import Path
from project_dream.pack_service import load_packs


def test_pack_service_validates_board_reference():
    packs = load_packs(Path("tests/fixtures/packs"))
    assert "B01" in packs.boards
    assert packs.communities["COM-PLZ-001"]["board_id"] == "B01"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pack_service.py::test_pack_service_validates_board_reference -v`  
Expected: FAIL due to missing service

**Step 3: Write minimal implementation**

```python
# src/project_dream/pack_service.py
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoadedPacks:
    boards: dict[str, dict]
    communities: dict[str, dict]


def load_packs(base_dir: Path) -> LoadedPacks:
    board_pack = json.loads((base_dir / "board_pack.json").read_text(encoding="utf-8"))
    community_pack = json.loads((base_dir / "community_pack.json").read_text(encoding="utf-8"))

    boards = {b["id"]: b for b in board_pack["boards"]}
    communities = {c["id"]: c for c in community_pack["communities"]}

    for com in communities.values():
        if com["board_id"] not in boards:
            raise ValueError(f"Unknown board_id: {com['board_id']}")
    return LoadedPacks(boards=boards, communities=communities)
```

```json
// tests/fixtures/packs/board_pack.json
{"boards":[{"id":"B01","name":"첫마루"}]}
```

```json
// tests/fixtures/packs/community_pack.json
{"communities":[{"id":"COM-PLZ-001","name":"첫마루 렌즈","board_id":"B01"}]}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pack_service.py::test_pack_service_validates_board_reference -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/pack_service.py tests/fixtures/packs/board_pack.json tests/fixtures/packs/community_pack.json tests/test_pack_service.py
git commit -m "feat: add pack loading and reference validation"
```

### Task 4: Add Deterministic Generator + Persona Selection

**Files:**
- Create: `src/project_dream/persona_service.py`
- Create: `src/project_dream/gen_engine.py`
- Create: `tests/test_generator.py`

**Step 1: Write the failing test**

```python
# tests/test_generator.py
from project_dream.models import SeedInput
from project_dream.persona_service import select_participants
from project_dream.gen_engine import generate_comment


def test_generator_is_deterministic_for_same_seed():
    seed = SeedInput(seed_id="SEED-001", title="사건", summary="요약", board_id="B01", zone_id="A")
    participants = select_participants(seed, round_idx=1)
    c1 = generate_comment(seed, participants[0], round_idx=1)
    c2 = generate_comment(seed, participants[0], round_idx=1)
    assert c1 == c2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_generator.py::test_generator_is_deterministic_for_same_seed -v`  
Expected: FAIL due to missing modules

**Step 3: Write minimal implementation**

```python
# src/project_dream/persona_service.py
from project_dream.models import SeedInput


def select_participants(seed: SeedInput, round_idx: int) -> list[str]:
    base = ["AG-01", "AG-02", "AG-03", "AG-04", "AG-05"]
    shift = (hash(seed.seed_id) + round_idx) % len(base)
    return base[shift:] + base[:shift]
```

```python
# src/project_dream/gen_engine.py
from project_dream.models import SeedInput


def generate_comment(seed: SeedInput, persona_id: str, round_idx: int) -> str:
    return (
        f"[{seed.board_id}/{seed.zone_id}] "
        f"R{round_idx} {persona_id}: {seed.title}에 대한 반응 - {seed.summary}"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_generator.py::test_generator_is_deterministic_for_same_seed -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/persona_service.py src/project_dream/gen_engine.py tests/test_generator.py
git commit -m "feat: add deterministic persona selection and generator"
```

### Task 5: Implement 3-Gate Pipeline (Safety/Similarity/Lore)

**Files:**
- Create: `src/project_dream/gate_pipeline.py`
- Create: `tests/test_gate_pipeline.py`

**Step 1: Write the failing test**

```python
# tests/test_gate_pipeline.py
from project_dream.gate_pipeline import run_gates


def test_gate_pipeline_masks_pii_and_reports_rewrite():
    corpus = ["안전한 문장"]
    result = run_gates("내 연락처는 010-1234-5678", corpus=corpus)
    assert result["final_text"] != "내 연락처는 010-1234-5678"
    assert any(not g["passed"] for g in result["gates"])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_gate_pipeline.py::test_gate_pipeline_masks_pii_and_reports_rewrite -v`  
Expected: FAIL due to missing module

**Step 3: Write minimal implementation**

```python
# src/project_dream/gate_pipeline.py
import re
from rapidfuzz.fuzz import ratio


PHONE_PATTERN = re.compile(r"01[0-9]-\d{3,4}-\d{4}")
TABOO_WORDS = ["실명", "서명 단서", "사망 조롱"]


def run_gates(text: str, corpus: list[str], similarity_threshold: int = 85) -> dict:
    gates = []
    current = text

    # Gate 1: Safety
    safety_pass = True
    if PHONE_PATTERN.search(current):
        safety_pass = False
        current = PHONE_PATTERN.sub("[REDACTED-PHONE]", current)
    if any(w in current for w in TABOO_WORDS):
        safety_pass = False
        current = current.replace("사망 조롱", "부적절 표현")
    gates.append({"gate_name": "safety", "passed": safety_pass, "reason": "pii/taboo check"})

    # Gate 2: Similarity
    max_sim = max((ratio(current, c) for c in corpus), default=0)
    sim_pass = max_sim < similarity_threshold
    if not sim_pass:
        current = f"{current} (재작성)"
    gates.append({"gate_name": "similarity", "passed": sim_pass, "reason": f"max_similarity={max_sim}"})

    # Gate 3: Lore Consistency (rule-based MVP)
    lore_pass = "정본" in current or "증거" in current
    if not lore_pass:
        current = f"{current} / 증거 기준 미기재"
    gates.append({"gate_name": "lore", "passed": lore_pass, "reason": "requires evidence context"})

    return {"final_text": current, "gates": gates}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_gate_pipeline.py::test_gate_pipeline_masks_pii_and_reports_rewrite -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/gate_pipeline.py tests/test_gate_pipeline.py
git commit -m "feat: add safety similarity lore gate pipeline"
```

### Task 6: Build Environment Engine (Score + Moderation State)

**Files:**
- Create: `src/project_dream/env_engine.py`
- Create: `tests/test_env_engine.py`

**Step 1: Write the failing test**

```python
# tests/test_env_engine.py
from project_dream.env_engine import compute_score, apply_report_threshold


def test_preserve_token_has_strong_visibility_effect():
    score_a = compute_score(up=3, comments=2, views=10, preserve=0, reports=0, trust=1)
    score_b = compute_score(up=3, comments=2, views=10, preserve=5, reports=0, trust=1)
    assert score_b > score_a


def test_report_threshold_transitions_to_hidden():
    state = apply_report_threshold(status="visible", reports=12, threshold=10)
    assert state == "hidden"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_env_engine.py -v`  
Expected: FAIL due to missing module

**Step 3: Write minimal implementation**

```python
# src/project_dream/env_engine.py
def compute_score(
    up: int,
    comments: int,
    views: int,
    preserve: int,
    reports: int,
    trust: int,
    urgent: int = 0,
) -> float:
    w1, w2, w3, w4, w5, w6 = 1.0, 1.3, 0.2, 3.0, 1.8, 1.1
    return (up * w1) + (comments * w2) + (views * w3) + (preserve * w4) - (reports * w5) + (trust * w6) + urgent


def apply_report_threshold(status: str, reports: int, threshold: int) -> str:
    if reports >= threshold:
        return "hidden"
    return status
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_env_engine.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/env_engine.py tests/test_env_engine.py
git commit -m "feat: add environment scoring and moderation transition"
```

### Task 7: Implement Orchestrator (3-Round Simulation + Retry Guard)

**Files:**
- Create: `src/project_dream/sim_orchestrator.py`
- Create: `tests/test_orchestrator.py`

**Step 1: Write the failing test**

```python
# tests/test_orchestrator.py
from project_dream.models import SeedInput
from project_dream.sim_orchestrator import run_simulation


def test_orchestrator_runs_three_rounds_minimum():
    seed = SeedInput(seed_id="SEED-001", title="사건", summary="요약", board_id="B01", zone_id="A")
    result = run_simulation(seed=seed, rounds=3, corpus=["샘플"])
    assert len(result["rounds"]) >= 3
    assert len(result["gate_logs"]) >= 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py::test_orchestrator_runs_three_rounds_minimum -v`  
Expected: FAIL due to missing module

**Step 3: Write minimal implementation**

```python
# src/project_dream/sim_orchestrator.py
from project_dream.gen_engine import generate_comment
from project_dream.gate_pipeline import run_gates
from project_dream.persona_service import select_participants


def run_simulation(seed, rounds: int, corpus: list[str], max_retries: int = 2) -> dict:
    round_logs = []
    gate_logs = []

    for r in range(1, rounds + 1):
        participants = select_participants(seed, round_idx=r)[:3]
        for p in participants:
            text = generate_comment(seed, p, round_idx=r)
            last = None
            for _ in range(max_retries + 1):
                last = run_gates(text, corpus=corpus)
                if all(g["passed"] for g in last["gates"]):
                    break
                text = last["final_text"]
            round_logs.append({"round": r, "persona_id": p, "text": last["final_text"]})
            gate_logs.append({"round": r, "persona_id": p, "gates": last["gates"]})

    return {"rounds": round_logs, "gate_logs": gate_logs}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py::test_orchestrator_runs_three_rounds_minimum -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/sim_orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add 3-round simulation orchestrator with retry guard"
```

### Task 8: Add Report Generator + Storage + CLI Integration

**Files:**
- Create: `src/project_dream/report_generator.py`
- Create: `src/project_dream/storage.py`
- Modify: `src/project_dream/cli.py`
- Create: `tests/test_cli_simulate_e2e.py`
- Create: `examples/seeds/seed_001.json`

**Step 1: Write the failing test**

```python
# tests/test_cli_simulate_e2e.py
import json
from pathlib import Path
from project_dream.cli import main


def test_cli_simulate_writes_run_outputs(tmp_path: Path):
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(json.dumps({
        "seed_id": "SEED-001",
        "title": "먹통 사건",
        "summary": "장터기둥 장애",
        "board_id": "B07",
        "zone_id": "D"
    }), encoding="utf-8")

    rc = main(["simulate", "--seed", str(seed_file), "--output-dir", str(tmp_path / "runs"), "--rounds", "3"])
    assert rc == 0
    assert any((tmp_path / "runs").glob("*/runlog.jsonl"))
    assert any((tmp_path / "runs").glob("*/report.md"))
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_simulate_e2e.py::test_cli_simulate_writes_run_outputs -v`  
Expected: FAIL because `simulate` command has no execution path

**Step 3: Write minimal implementation**

```python
# src/project_dream/report_generator.py
def build_report(seed, sim_result: dict) -> dict:
    return {
        "seed_id": seed.seed_id,
        "summary": f"{seed.title} / 라운드 {len(sim_result['rounds'])}",
        "highlights": sim_result["rounds"][:10],
        "risks": [g for g in sim_result["gate_logs"] if any(not x["passed"] for x in g["gates"])],
    }
```

```python
# src/project_dream/storage.py
import json
from datetime import datetime
from pathlib import Path


def persist_run(output_dir: Path, sim_result: dict, report: dict) -> Path:
    run_id = datetime.utcnow().strftime("run-%Y%m%d-%H%M%S")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "runlog.jsonl").open("w", encoding="utf-8") as f:
        for row in sim_result["rounds"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(f"# Report\n\n{report['summary']}\n", encoding="utf-8")
    return run_dir
```

```python
# src/project_dream/cli.py (simulate path only)
import json
from pathlib import Path
from project_dream.models import SeedInput
from project_dream.sim_orchestrator import run_simulation
from project_dream.report_generator import build_report
from project_dream.storage import persist_run


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "simulate":
        seed = SeedInput.model_validate_json(Path(args.seed).read_text(encoding="utf-8"))
        sim_result = run_simulation(seed=seed, rounds=args.rounds, corpus=[])
        report = build_report(seed, sim_result)
        persist_run(Path(args.output_dir), sim_result, report)
    return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_simulate_e2e.py::test_cli_simulate_writes_run_outputs -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/project_dream/report_generator.py src/project_dream/storage.py src/project_dream/cli.py tests/test_cli_simulate_e2e.py examples/seeds/seed_001.json
git commit -m "feat: wire simulate command to run orchestrator and persist report"
```

### Task 9: Verification Before Completion

**Files:**
- Modify: `README.md` (if absent, create with run instructions)
- Modify: `docs/plans/2026-02-27-project-dream-mvp-design.md` (optional links only)

**Step 1: Write the failing test**

```python
# tests/test_contracts.py
from pathlib import Path


def test_readme_contains_quickstart():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "pytest" in text
    assert "simulate" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_contracts.py::test_readme_contains_quickstart -v`  
Expected: FAIL if README missing/incomplete

**Step 3: Write minimal implementation**

```markdown
# README.md

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
python -m project_dream.cli simulate --seed examples/seeds/seed_001.json --output-dir runs --rounds 3
```
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_contracts.py::test_readme_contains_quickstart -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add README.md tests/test_contracts.py
git commit -m "docs: add quickstart and contract check"
```

## Final Verification Checklist

Run in order:

1. `pytest -q`
2. `python -m project_dream.cli simulate --seed examples/seeds/seed_001.json --output-dir runs --rounds 3`
3. `ls -la runs`
4. `find runs -maxdepth 2 -type f | sort`

Expected:

- 모든 테스트 PASS
- `runs/<run_id>/runlog.jsonl`, `report.json`, `report.md` 생성
- 실행 에러 없음
