# Web API Read Endpoints Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** run 결과를 조회하는 API/HTTP read 엔드포인트를 추가한다.

**Architecture:** `infra/store`에 JSON 로더를 추가하고, `infra/web_api`에서 조회 메서드를 제공한 뒤 `infra/http_server` GET 라우트로 연결한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- API facade 조회 메서드 테스트
- HTTP GET read endpoints 테스트

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_web_api.py tests/test_web_api_http_server.py -q`  
Expected: FAIL (missing methods/routes)

### Task 2: Implement Store + API + HTTP Routes

**Files:**
- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

**Step 1: Add store JSON load helpers**

- `load_report(run_id)`
- `load_eval(run_id)`

**Step 2: Add API facade read methods**

- `latest_run()`, `get_report(run_id)`, `get_eval(run_id)`

**Step 3: Add HTTP GET routes**

- `/runs/latest`
- `/runs/<run_id>/report`
- `/runs/<run_id>/eval`

### Task 3: Full Verification + Commit

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-read-endpoints-design.md docs/plans/2026-02-27-webapi-read-endpoints-implementation.md
git commit -m "feat: add web api read endpoints for latest run report and eval"
```
