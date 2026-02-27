# Web API Regression Summary Endpoint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 최신 회귀 summary JSON을 API/HTTP로 조회하는 read endpoint를 추가한다.

**Architecture:** `infra/store`에서 `runs/regressions/regression-*.json` 최신 파일을 로딩하고, `infra/web_api`와 `infra/http_server`에 조회 경로를 연결한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- API facade `latest_regression_summary` 테스트
- HTTP `GET /regressions/latest` 테스트

**Step 2: Run and confirm fail**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_web_api.py::test_web_api_latest_regression_summary tests/test_web_api_http_server.py::test_http_server_health_simulate_evaluate -q`  
Expected: FAIL (missing method/route)

### Task 2: Implement Store + API + HTTP

**Files:**
- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

### Task 3: Full Verification + Commit

**Step 1: Run full tests**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-regression-summary-endpoint-design.md docs/plans/2026-02-27-webapi-regression-summary-endpoint-implementation.md
git commit -m "feat: add web api latest regression summary endpoint"
```
