# Web API Regressions List Endpoint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 회귀 summary 파일 목록을 최신순으로 조회하는 API/HTTP read endpoint를 추가한다.

**Architecture:** `infra/store`에서 summary 파일을 메타데이터 목록으로 변환하고, `infra/web_api`에서 노출, `infra/http_server`에서 `GET /regressions` 및 `limit` 쿼리를 처리한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- API facade `list_regression_summaries` 테스트
- HTTP `GET /regressions` + `GET /regressions?limit=1` 테스트

**Step 2: Run and confirm fail**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_web_api.py::test_web_api_list_regression_summaries tests/test_web_api_http_server.py::test_http_server_health_simulate_evaluate -q`  
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
git add src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-regressions-list-endpoint-design.md docs/plans/2026-02-27-webapi-regressions-list-endpoint-implementation.md
git commit -m "feat: add web api regressions list endpoint"
```
