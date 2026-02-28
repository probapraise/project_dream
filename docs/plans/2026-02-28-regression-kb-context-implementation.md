# Regression KB Context Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 회귀 배치 러너가 seed별 KB 컨텍스트를 조회해 `run_simulation`의 `corpus`로 사용하도록 만든다.

**Architecture:** `regression_runner.py`에서 packs를 로드한 뒤 인덱스를 1회 구축하고, 각 seed 루프에서 `retrieve_context`를 호출한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Test

**Files:**
- Modify: `tests/test_regression_runner.py`

**Step 1: Add failing test**

- spy `run_simulation`으로 전달된 `corpus`를 캡처
- `retrieve_context` mock 결과(`["ctx-B07-D"]`)가 그대로 전달되는지 검증

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py::test_run_regression_batch_uses_retrieved_context_corpus -q`  
Expected: FAIL (현재 `corpus=[]`)

### Task 2: Implement Runner Integration

**Files:**
- Modify: `src/project_dream/regression_runner.py`

**Step 1: KB index wiring**

- `build_index`, `retrieve_context` import
- packs 로드 후 인덱스 생성
- seed 루프마다 context 조회 후 `run_simulation(..., corpus=context["corpus"])`

**Step 2: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_regression_runner.py tests/test_cli_regress_e2e.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/regression_runner.py tests/test_regression_runner.py docs/plans/2026-02-28-regression-kb-context-design.md docs/plans/2026-02-28-regression-kb-context-implementation.md
git commit -m "feat: use kb retrieval context in regression batch simulation"
```
