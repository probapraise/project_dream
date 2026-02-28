# Runlog Observability And Stage Error Schema Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `/runs/{id}/runlog`에 요약 메타를 제공하고 stage 실행 실패를 API 에러 스키마로 표준화한다.

**Architecture:** 저장소 계층(`RunRepository.load_runlog`)에서 runlog row 요약을 계산해 API 응답에 그대로 노출한다. 오케스트레이터 런타임은 stage 실패를 구조화된 예외로 내보내고 HTTP 서버가 해당 예외를 표준 에러 payload로 매핑한다.

**Tech Stack:** Python, pytest, stdlib `http.server`, repository pattern

---

### Task 1: Runlog Summary RED

**Files:**
- Modify: `tests/test_infra_store.py`
- Modify: `tests/test_infra_store_sqlite.py`
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Write the failing tests**

- `load_runlog` 응답에 `summary` 키 존재 검증
- `summary.row_counts`에 `stage_checkpoint`, `graph_node_attempt` 카운트 검증
- `summary.stage.retry_count/failure_count/max_attempts` 검증
- API/HTTP `/runs/{id}/runlog` 응답에 동일 필드 노출 검증

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q`

Expected: `summary` 미구현으로 FAIL.

### Task 2: Runlog Summary GREEN

**Files:**
- Modify: `src/project_dream/infra/store.py`

**Step 1: Write minimal implementation**

- 공통 헬퍼 추가:
  - row type 카운트 집계
  - stage retry/failure/max_attempts 집계
- `FileRunRepository.load_runlog`와 `SQLiteRunRepository.load_runlog`이 `{run_id, rows, summary}` 반환

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q`

Expected: PASS.

### Task 3: Stage Failure Error Schema RED

**Files:**
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Write the failing test**

- stage node handler 강제 실패 시 `POST /simulate` 응답이
  - status `500`
  - `error=stage_execution_failed`
  - `error_code=ORCH_STAGE_FAILED`
  - `stage_node`, `attempts` 포함
  를 만족하는지 검증

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_api_http_server.py -q`

Expected: generic `internal_error` payload로 FAIL.

### Task 4: Stage Failure Error Schema GREEN

**Files:**
- Modify: `src/project_dream/orchestrator_runtime.py`
- Modify: `src/project_dream/infra/http_server.py`

**Step 1: Write minimal implementation**

- `StageNodeExecutionError` 예외 클래스 추가 (`node_id`, `attempts`, `message`)
- stage retry 소진 시 해당 예외 발생
- HTTP 서버가 예외를 catch해 표준 payload 반환

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_web_api_http_server.py -q`

Expected: PASS.

### Task 5: Regression Verification And Commit

**Files:**
- Modify: `docs/plans/2026-02-28-stage-observability-error-schema-handoff.md` (new)

**Step 1: Run full regression**

Run: `python -m pytest -q`

Expected: all tests pass.

**Step 2: Document and commit**

- 변경사항/검증 결과를 handoff 문서에 기록
- 커밋 후 PR 생성
