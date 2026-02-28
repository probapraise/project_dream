# SQLite Regression Summary Index Implementation Plan

**Goal:** SQLite 저장소에서 회귀 summary 목록/최신/ID 조회를 DB 인덱스 중심으로 제공한다.

**Architecture:** repository가 summary payload를 DB에 upsert하고, API/service는 repository 계약만 사용한다. 조회는 DB-first, 파일은 동기화/fallback 소스로 처리한다.

**Tech Stack:** Python, sqlite3, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_infra_store_sqlite.py`
- Modify: `tests/test_web_api.py`

### Step 1: Add failing tests

- `SQLiteRunRepository.persist_regression_summary`가 존재하고 파일 삭제 후에도
  - `list_regression_summaries`
  - `load_latest_regression_summary`
  - `load_regression_summary`
  조회가 가능한지 검증
- `ProjectDreamAPI` + sqlite backend에서 `regress` 후 summary 파일을 삭제해도
  - 목록/최신/ID 조회가 유지되는지 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store_sqlite.py tests/test_web_api.py -q
```

Observed: FAIL (`persist_regression_summary` 미구현, 파일 삭제 시 목록 0건)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/app_service.py`

### Step 1: Repository contract extension

- `RunRepository` protocol에 `persist_regression_summary(summary)` 추가
- `FileRunRepository`는 no-op 구현

### Step 2: SQLite summary index

- `regression_summaries` table + index 추가
- `persist_regression_summary` 구현
  - summary 메타 + payload JSON upsert
- `_sync_regression_indexes_from_files` 추가
  - 디스크 summary를 DB로 동기화
- 조회 로직 보강
  - `list_regression_summaries`: DB-first
  - `load_latest_regression_summary`: DB-first
  - `load_regression_summary`: 파일 우선, 없으면 DB payload fallback

### Step 3: Service wiring

- `app_service.regress_and_persist`에서 `run_regression_batch` 반환값을 repository에 인덱싱 후 반환

### Step 4: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store_sqlite.py tests/test_web_api.py -q
```

Observed: PASS (`18 passed`)

---

## Task 3: Verification

### Step 1: Integration-focused set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_app_service_kb_context.py tests/test_web_api_http_server.py tests/test_cli_regress_e2e.py tests/test_regression_runner.py -q
```

Observed: PASS (`13 passed`)

### Step 2: Full regression

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Observed: PASS (`161 passed`)
