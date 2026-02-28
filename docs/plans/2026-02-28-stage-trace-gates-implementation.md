# Stage Trace Gates Implementation Plan

**Goal:** runlog 단계 trace 누락을 평가/회귀 단계에서 자동 실패로 처리한다.

**Architecture:** `eval_suite`가 stage trace 체크를 계산하고, `regression_runner`가 해당 체크를 집계해 gate를 산출한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_eval_suite.py`
- Modify: `tests/test_eval_quality_metrics.py`
- Modify: `tests/test_eval_report_quality_rules.py`
- Modify: `tests/test_regression_runner.py`

### Step 1: Add failing tests

- stage 이벤트 누락 시 eval 실패 (`runlog.stage_trace_present=False`)
- 회귀 summary에 `stage_trace_runs` totals/gate 존재
- eval fixture runlog를 최신 stage 이벤트 포함 형태로 갱신

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py -q
```

Expected: FAIL (stage trace 체크/집계 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/eval_suite.py`
- Modify: `src/project_dream/regression_runner.py`

### Step 1: Eval stage trace check

- required stage event type 목록 상수화
- `runlog.stage_trace_present` 체크 추가
- metrics에 stage trace row 수 집계 추가

### Step 2: Regression stage trace gate

- eval checks에서 `runlog.stage_trace_present` 여부 추출
- totals에 `stage_trace_runs` 추가
- gates에 `stage_trace_runs` 추가

### Step 3: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py -q
```

Expected: PASS

---

## Task 3: Verification

### Step 1: Regression-sensitive test set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py -q
```

Expected: PASS

### Step 2: Full suite

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Expected: all tests pass
