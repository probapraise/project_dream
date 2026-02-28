# Run Context Persistence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 시뮬레이션/회귀 실행에 사용된 KB 컨텍스트를 runlog에 저장해 실행 근거를 추적 가능하게 한다.

**Architecture:** app/regression 레이어에서 context를 `sim_result`에 주입하고, storage 레이어에서 `type=context` row를 직렬화한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_infra_store.py`
- Modify: `tests/test_web_api.py`

**Step 1: Add failing tests**

- context 정보가 있는 sim_result를 persist하면 runlog에 context row가 기록되는지
- simulate 후 `get_runlog` 응답에 context row가 포함되는지

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_infra_store.py tests/test_web_api.py::test_web_api_read_endpoints -q`  
Expected: FAIL (context row 미기록)

### Task 2: Implement Persistence

**Files:**
- Modify: `src/project_dream/app_service.py`
- Modify: `src/project_dream/regression_runner.py`
- Modify: `src/project_dream/storage.py`

**Step 1: Inject context into sim_result**

- app/regression 경로에서 `context_bundle`, `context_corpus`를 sim_result에 포함

**Step 2: Persist context row**

- `persist_run`에서 context가 존재하면 runlog 상단에 `type=context` row 기록

**Step 3: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_infra_store.py tests/test_web_api.py::test_web_api_read_endpoints -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/app_service.py src/project_dream/regression_runner.py src/project_dream/storage.py tests/test_infra_store.py tests/test_web_api.py docs/plans/2026-02-28-run-context-persistence-design.md docs/plans/2026-02-28-run-context-persistence-implementation.md
git commit -m "feat: persist retrieval context in runlog artifacts"
```
