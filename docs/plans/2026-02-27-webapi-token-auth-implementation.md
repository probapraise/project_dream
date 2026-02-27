# Web API Token Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `health`를 제외한 HTTP 엔드포인트에 Bearer 토큰 인증을 강제한다.

**Architecture:** `infra/http_server`에서 요청 전 인증 가드를 수행하고, `cli serve`에서 토큰 주입(`--api-token`/env fallback) 및 미설정 에러를 처리한다.

**Tech Stack:** Python, argparse, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api_http_server.py`
- Modify: `tests/test_cli_smoke.py`

**Step 1: Add failing tests**

- non-health 엔드포인트 무인증 요청 `401`
- 올바른 Bearer 토큰 요청 성공
- `serve` 토큰 미설정 시 실행 실패

**Step 2: Run and confirm fail**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_web_api_http_server.py::test_http_server_health_simulate_evaluate tests/test_cli_smoke.py::test_cli_serve_requires_api_token_when_not_set -q`  
Expected: FAIL (auth not enforced / missing CLI guard)

### Task 2: Implement HTTP Auth + CLI Wiring

**Files:**
- Modify: `src/project_dream/infra/http_server.py`
- Modify: `src/project_dream/cli.py`
- Modify: `README.md`

### Task 3: Verification + Commit

**Step 1: Run full tests**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/http_server.py src/project_dream/cli.py README.md tests/test_web_api_http_server.py tests/test_cli_smoke.py docs/plans/2026-02-27-webapi-token-auth-design.md docs/plans/2026-02-27-webapi-token-auth-implementation.md
git commit -m "feat: enforce bearer token auth on web api endpoints"
```
