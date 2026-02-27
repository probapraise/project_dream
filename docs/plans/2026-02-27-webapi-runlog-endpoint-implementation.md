# Web API Runlog Endpoint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** runlog를 API/HTTP로 조회하는 read endpoint를 추가한다.

**Architecture:** `infra/store`에 `load_runlog` 추가, `infra/web_api`에 `get_runlog` 추가, `infra/http_server`에 GET 라우트 추가.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- API facade `get_runlog` 테스트
- HTTP `GET /runs/{id}/runlog` 테스트

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_web_api.py tests/test_web_api_http_server.py -q`  
Expected: FAIL (missing method/route)

### Task 2: Implement Store + API + HTTP

**Files:**
- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

### Task 3: Full Verification + Commit

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-runlog-endpoint-design.md docs/plans/2026-02-27-webapi-runlog-endpoint-implementation.md
git commit -m "feat: add web api runlog endpoint for run-level debugging"
```
