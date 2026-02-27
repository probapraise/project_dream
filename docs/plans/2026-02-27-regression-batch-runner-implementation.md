# Regression Batch Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 10개 seed를 자동 실행하고 회귀 품질 게이트를 판정하는 `project-dream regress` 커맨드를 추가한다.

**Architecture:** `regression_runner.py`에 배치 오케스트레이션을 분리하고, CLI는 인자 전달/종료코드만 담당한다. 기존 simulate/evaluate 모듈을 재사용해 중복 구현을 피한다.

**Tech Stack:** Python 3.12+, argparse, pydantic, pytest

---

### Task 1: Regression Runner RED Tests

**Files:**
- Create: `tests/test_regression_runner.py`
- Test: `tests/test_regression_runner.py`

**Step 1: Write the failing test**

```python
def test_run_regression_batch_produces_summary_and_passes(tmp_path: Path):
    ...
    summary = run_regression_batch(...)
    assert summary["schema_version"] == "regression.v1"
    assert summary["totals"]["seed_runs"] == 2
    assert "format_missing_zero" in summary["gates"]
```

```python
def test_run_regression_batch_raises_when_no_seed_files(tmp_path: Path):
    ...
    with pytest.raises(FileNotFoundError):
        run_regression_batch(...)
```

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py -q`  
Expected: FAIL with import error or missing `run_regression_batch`

**Step 3: Write minimal implementation**

- `src/project_dream/regression_runner.py` 생성
- seed 파일 로딩/반복 실행/summary 반환의 최소 동작 구현

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_regression_runner.py src/project_dream/regression_runner.py
git commit -m "test/feat: add regression batch runner core"
```

### Task 2: CLI RED Tests for `regress`

**Files:**
- Create: `tests/test_cli_regress_e2e.py`
- Modify: `src/project_dream/cli.py`
- Test: `tests/test_cli_regress_e2e.py`

**Step 1: Write the failing test**

```python
def test_cli_regress_writes_summary_and_returns_zero(tmp_path: Path):
    ...
    exit_code = main(["regress", "--seeds-dir", str(seeds_dir), "--output-dir", str(runs_dir)])
    assert exit_code == 0
    assert len(list((runs_dir / "regressions").glob("regression-*.json"))) == 1
```

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_cli_regress_e2e.py -q`  
Expected: FAIL because `regress` command is unknown

**Step 3: Write minimal implementation**

- `cli.py`에 `regress` 서브커맨드 인자 추가
- `run_regression_batch(...)` 호출
- summary pass/fail에 따라 `0/2` 반환

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_cli_regress_e2e.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_regress_e2e.py src/project_dream/cli.py
git commit -m "feat: add regress CLI command"
```

### Task 3: Add 10 Regression Seed Fixtures

**Files:**
- Create: `examples/seeds/regression/seed_001.json`
- Create: `examples/seeds/regression/seed_002.json`
- Create: `examples/seeds/regression/seed_003.json`
- Create: `examples/seeds/regression/seed_004.json`
- Create: `examples/seeds/regression/seed_005.json`
- Create: `examples/seeds/regression/seed_006.json`
- Create: `examples/seeds/regression/seed_007.json`
- Create: `examples/seeds/regression/seed_008.json`
- Create: `examples/seeds/regression/seed_009.json`
- Create: `examples/seeds/regression/seed_010.json`

**Step 1: Write the failing test**

```python
def test_regression_seed_fixture_count():
    seeds = sorted(Path("examples/seeds/regression").glob("seed_*.json"))
    assert len(seeds) == 10
```

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py::test_regression_seed_fixture_count -q`  
Expected: FAIL if fixture count is not 10

**Step 3: Write minimal implementation**

- 10개 seed 파일 생성 (Phase1 board/community 범위 내 값 사용)

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py::test_regression_seed_fixture_count -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add examples/seeds/regression tests/test_regression_runner.py
git commit -m "chore: add 10 regression seed fixtures"
```

### Task 4: Full Verification and Smoke Run

**Files:**
- Modify: `README.md`

**Step 1: Add usage snippet**

```md
python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10
```

**Step 2: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 3: Run regression smoke command**

Run: `./.venv/bin/python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10`  
Expected: summary JSON 생성, 종료코드 0 또는 게이트 실패 시 2

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add regress command usage"
```
