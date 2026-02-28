# Run List Pagination Implementation Plan

**Goal:** run 메타데이터 목록 조회를 필터/페이지네이션 가능하게 확장한다.

**Architecture:** repository(`FileRunRepository`, `SQLiteRunRepository`)가 `list_runs`를 제공하고, API/HTTP는 해당 계약을 그대로 노출한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_infra_store.py`
- Modify: `tests/test_infra_store_sqlite.py`
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

### Step 1: Add failing tests

- file/sqlite repository에서 `list_runs(limit, offset, seed_id, board_id, status)` 검증
- API 계층 `ProjectDreamAPI.list_runs()` 검증
- HTTP `GET /runs` 및 query param 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q
```

Observed: `list_runs` 미구현 및 `/runs` 404로 4개 테스트 실패.

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

### Step 1: Repository contract + implementations

- `RunRepository` protocol에 `list_runs` 추가
- `FileRunRepository`
  - run 디렉터리 스캔 + metadata 추출(report/eval/runlog)
  - 필터/페이지네이션 적용
- `SQLiteRunRepository`
  - SQL WHERE/LIMIT/OFFSET 기반 필터/페이지네이션 적용

### Step 2: API/HTTP wiring

- `ProjectDreamAPI.list_runs` 추가
- `GET /runs` 라우트 추가
  - `limit`, `offset`, `seed_id`, `board_id`, `status` query 지원

### Step 3: Fix metadata priority bug

- file backend에서 `status`는 `moderation_decision`보다 `end_condition` 값을 우선하도록 보정

### Step 4: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q
```

Observed: PASS (`23 passed`).

---

## Task 3: Verification

### Step 1: Full regression

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Observed: PASS (`159 passed`).
