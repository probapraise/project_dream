# Stage Trace Ordering Gates Implementation Plan

**Goal:** runlog stage 이벤트 순서가 실행 흐름과 일치하는지 평가/회귀에서 자동 검증한다.

**Architecture:** `eval_suite`가 ordering 체크를 계산하고, `regression_runner`가 결과를 집계한다. `storage.persist_run`은 순서가 일관된 runlog를 기록한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_eval_suite.py`
- Modify: `tests/test_regression_runner.py`

### Step 1: Add failing tests

- ordering 위반(run/end_condition 순서 교란) 시 eval 실패
- 회귀 summary에 `stage_trace_ordered_runs` totals/gate 포함

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py -q
```

Expected: FAIL (`runlog.stage_trace_ordering`, `stage_trace_ordered_runs` 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/eval_suite.py`
- Modify: `src/project_dream/regression_runner.py`
- Modify: `src/project_dream/storage.py`

### Step 1: Eval ordering check

- `runlog.stage_trace_ordering` 체크 추가
- index 기반 규칙 검증(사전 단계/코어 단계/사후 단계 순서)
- metrics에 ordering flag 추가

### Step 2: Regression ordering gate

- eval checks에서 ordering 여부 추출
- totals에 `stage_trace_ordered_runs` 추가
- gates에 `stage_trace_ordered_runs` 추가

### Step 3: Storage serialization ordering

- runlog 직렬화 순서 정렬
  - context/candidate/selected
  - round/gate/action
  - round_summary
  - moderation_decision
  - end_condition

### Step 4: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py tests/test_infra_store.py -q
```

Expected: PASS

---

## Task 3: Verification

### Step 1: Regression-sensitive test set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py tests/test_eval_suite.py tests/test_eval_quality_metrics.py tests/test_eval_report_quality_rules.py tests/test_regression_runner.py tests/test_infra_store.py -q
```

Expected: PASS

### Step 2: Full suite

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Expected: all tests pass
