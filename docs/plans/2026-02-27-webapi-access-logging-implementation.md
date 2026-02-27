# Web API Access Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** HTTP 요청별 구조화 로그와 인증 실패 구분 로그를 추가해 운영 추적성을 강화한다.

**Architecture:** `infra/http_server`에 `request_logger` 훅을 도입해 요청 단위 로그를 생성하고, `cli serve`에서 stderr JSON logger를 주입한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Test

**Files:**
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing test**

- `create_server(..., request_logger=...)`로 로그 수집
- `health`, 인증실패 요청, 인증성공 요청을 보내고 필드 검증

**Step 2: Run and confirm fail**

Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_web_api_http_server.py::test_http_server_emits_structured_access_logs -q`  
Expected: FAIL (missing `request_logger` support)

### Task 2: Implement HTTP/CLI Logging

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
git add src/project_dream/infra/http_server.py src/project_dream/cli.py README.md tests/test_web_api_http_server.py docs/plans/2026-02-27-webapi-access-logging-design.md docs/plans/2026-02-27-webapi-access-logging-implementation.md
git commit -m "feat: add structured access logging for web api server"
```
