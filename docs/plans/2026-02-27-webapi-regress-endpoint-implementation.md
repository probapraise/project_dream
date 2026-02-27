# Web API Regress Endpoint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** API/HTTP 레이어에서 회귀 배치(`regress`)를 실행하고 summary를 반환한다.

**Architecture:** `app_service.regress_and_persist` 유즈케이스를 만들고 `ProjectDreamAPI.regress`와 `http_server` `/regress` 라우트에서 호출한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- API facade `regress()` 호출 테스트
- HTTP `POST /regress` 호출 테스트

**Step 2: Run tests and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_web_api.py tests/test_web_api_http_server.py -q`  
Expected: FAIL (`regress` not found)

### Task 2: Implement Service + API + HTTP

**Files:**
- Modify: `src/project_dream/app_service.py`
- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

**Step 1: Add `regress_and_persist(...)`**

**Step 2: Add `ProjectDreamAPI.regress(...)`**

**Step 3: Add `/regress` route**

### Task 3: Verification + Commit

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/app_service.py src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-regress-endpoint-design.md docs/plans/2026-02-27-webapi-regress-endpoint-implementation.md
git commit -m "feat: add web api regress endpoint backed by shared regression service"
```
