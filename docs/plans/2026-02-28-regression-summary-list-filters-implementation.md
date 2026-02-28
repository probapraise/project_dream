# Regression Summary List Filters Implementation Plan

**Goal:** 회귀 summary 목록 조회에 필터/페이지네이션 계약을 도입하고 DB 인덱스 경로를 API까지 노출한다.

**Architecture:** repository가 query를 처리하고 API/HTTP는 파라미터 전달만 수행한다. SQLite는 인덱스 테이블 기반으로 처리한다.

**Tech Stack:** Python, sqlite3, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_infra_store.py`
- Modify: `tests/test_infra_store_sqlite.py`
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

### Step 1: Add failing tests

- file/sqlite 저장소의 `list_regression_summaries`에
  - `total/offset/limit` 응답
  - `metric_set`, `pass_fail` 필터
  - `offset` 페이지네이션
  검증 추가
- API 및 HTTP `/regressions`에 동일 계약 검증 추가

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q
```

Observed: FAIL (`total` 미포함 및 query 확장 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/infra/store.py`
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

### Step 1: Repository contract and implementations

- `RunRepository.list_regression_summaries` 시그니처 확장
- `FileRunRepository`
  - 필터(`metric_set/pass_fail`) 적용
  - 페이지네이션(`limit/offset`) 적용
  - 응답에 `total/limit/offset` 추가
- `SQLiteRunRepository`
  - DB where/offset/limit 처리
  - 동일 응답 스키마 반환

### Step 2: API/HTTP wiring

- `ProjectDreamAPI.list_regression_summaries` 파라미터 확장
- `GET /regressions` query 파싱 확장
  - `pass_fail` 문자열 파싱(`true/false/1/0/yes/no`)

### Step 3: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q
```

Observed: PASS (`27 passed`)

---

## Task 3: Verification

### Step 1: Integration-focused set

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_app_service_kb_context.py tests/test_cli_regress_e2e.py tests/test_regression_runner.py tests/test_cli_smoke.py -q
```

Observed: PASS (`21 passed`)

### Step 2: Full regression

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Observed: PASS (`163 passed`)
