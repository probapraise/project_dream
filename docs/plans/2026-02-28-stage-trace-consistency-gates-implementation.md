# Stage Trace Consistency Gates Implementation Plan

**Goal:** runlog stage trace의 라운드 정합성을 평가/회귀 게이트에서 자동 검증한다.

**Architecture:** `eval_suite`가 일관성 체크를 계산하고, `regression_runner`가 체크 결과를 totals/gate로 집계한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_eval_suite.py`
- Modify: `tests/test_regression_runner.py`

### Step 1: Add failing tests

- `end_condition.ended_round`가 실제 stage 라운드 집계와 다르면 eval 실패
- 회귀 summary에 `stage_trace_consistent_runs` totals/gate 포함

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py -q
```

Expected: FAIL (`runlog.stage_trace_consistency`, `stage_trace_consistent_runs` 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/eval_suite.py`
- Modify: `src/project_dream/regression_runner.py`

### Step 1: Eval consistency check

- `runlog.stage_trace_consistency` 체크 추가
- 검증:
  - `end_condition` 단일성
  - `ended_round` 유효성
  - `round`, `round_summary`, `moderation_decision` 라운드 ID 집합 일치
- metrics에 `stage_trace_consistent` 플래그 추가

### Step 2: Regression consistency gate

- eval checks에서 consistency 여부 추출
- totals에 `stage_trace_consistent_runs` 추가
- gates에 `stage_trace_consistent_runs` 추가

### Step 3: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py -q
```

Expected: PASS

---

## Task 3: Verification

### Step 1: Regression-sensitive test set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py -q
```

Expected: PASS

### Step 2: Full suite

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Expected: all tests pass
