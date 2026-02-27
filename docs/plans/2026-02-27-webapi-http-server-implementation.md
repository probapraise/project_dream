# Web API HTTP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `ProjectDreamAPI`를 HTTP로 호출 가능한 최소 서버를 추가한다.

**Architecture:** `infra/http_server.py`에 request handler + server factory를 구현하고 CLI `serve`로 실행한다.

**Tech Stack:** Python stdlib (`http.server`, `urllib`), pytest

---

### Task 1: RED Tests

**Files:**
- Create: `tests/test_web_api_http_server.py`

**Step 1: Write failing integration tests**

- GET `/health` returns 200 + status ok
- POST `/simulate` returns run_id
- POST `/evaluate` returns eval payload

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_web_api_http_server.py -q`  
Expected: FAIL (server module missing)

### Task 2: Implement HTTP Server Layer

**Files:**
- Create: `src/project_dream/infra/http_server.py`

**Step 1: Implement request handler and JSON responses**

**Step 2: Implement server factory**

- `create_server(api, host, port)`

**Step 3: Run target tests**

Run: `./.venv/bin/python -m pytest tests/test_web_api_http_server.py -q`  
Expected: PASS

### Task 3: Wire CLI `serve`

**Files:**
- Modify: `src/project_dream/cli.py`

**Step 1: Add `serve` subcommand**

- args: `--host`, `--port`, `--runs-dir`, `--packs-dir`

**Step 2: Call HTTP serve function**

### Task 4: Full Verification + Commit

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/http_server.py src/project_dream/cli.py tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-http-server-design.md docs/plans/2026-02-27-webapi-http-server-implementation.md
git commit -m "feat: add stdlib http server adapter for project web api"
```
