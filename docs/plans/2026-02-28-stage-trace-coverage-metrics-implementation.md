# Stage Trace Coverage Metrics Implementation Plan

**Goal:** stage trace completeness를 수치화한 `stage_trace_coverage_rate`를 eval/regression에 반영한다.

**Architecture:** `eval_suite`에서 per-run coverage를 계산하고, `regression_runner`가 평균값을 집계해 gate로 사용한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_eval_suite.py`
- Modify: `tests/test_eval_quality_metrics.py`
- Modify: `tests/test_regression_runner.py`

### Step 1: Add failing tests

- valid eval run에서 `stage_trace_coverage_rate == 1.0`
- v1/v2 metrics에 `stage_trace_coverage_rate` 존재
- regression totals에 `avg_stage_trace_coverage_rate`, gates에 `stage_trace_coverage_rate` 존재

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_regression_runner.py -q
```

Expected: FAIL (`stage_trace_coverage_rate`, `avg_stage_trace_coverage_rate` 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/eval_suite.py`
- Modify: `src/project_dream/regression_runner.py`

### Step 1: Eval coverage metric

- `stage_trace_coverage_rate` 계산
  - candidate/selected/end_condition 존재성
  - round_summary/moderation_decision 라운드 coverage
- metrics에 `stage_trace_coverage_rate` 추가

### Step 2: Regression aggregation + gate

- run별 coverage 누적 및 평균 계산
- totals에 `avg_stage_trace_coverage_rate` 추가
- gates에 `stage_trace_coverage_rate` 추가

### Step 3: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_regression_runner.py -q
```

Expected: PASS

---

## Task 3: Verification

### Step 1: Regression-sensitive test set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py tests/test_infra_store.py -q
```

Expected: PASS

### Step 2: Full suite

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Expected: all tests pass
