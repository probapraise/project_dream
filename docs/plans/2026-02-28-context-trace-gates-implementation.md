# Context Trace Gates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 실행 컨텍스트 추적(`type=context`)이 없는 run은 평가/회귀에서 자동 실패하도록 강제한다.

**Architecture:** `eval_suite`가 context trace 존재를 체크하고, `regression_runner`가 해당 체크를 집계해 게이트를 만든다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_eval_suite.py`
- Modify: `tests/test_regression_runner.py`

**Step 1: Add failing tests**

- context row 없는 runlog는 eval 실패
- regression summary에 `context_trace_runs` totals/gate 존재

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py -q`  
Expected: FAIL (체크/게이트 미구현)

### Task 2: Implement Eval/Regression Gates

**Files:**
- Modify: `src/project_dream/eval_suite.py`
- Modify: `src/project_dream/regression_runner.py`

**Step 1: Eval check**

- `runlog.context_trace_present` 체크 추가
- metrics에 `context_rows` 추가

**Step 2: Regression gate**

- eval checks에서 context trace 여부 추출
- totals에 `context_trace_runs` 추가
- gates에 `context_trace_runs` 추가

**Step 3: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_eval_suite.py tests/test_regression_runner.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/eval_suite.py src/project_dream/regression_runner.py tests/test_eval_suite.py tests/test_regression_runner.py docs/plans/2026-02-28-context-trace-gates-design.md docs/plans/2026-02-28-context-trace-gates-implementation.md
git commit -m "feat: enforce context trace checks in eval and regression gates"
```
