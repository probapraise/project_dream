# Stage Observability And Error Schema Handoff (2026-02-28)

## 1) Done in this session

- Target: 인프라 고도화 1차 (`runlog 관측 고도화 + stage failure API 에러 표준화`)
- Implemented:
  - `RunRepository.load_runlog` 응답 확장 (`summary` 추가)
    - `summary.row_counts`: type별 runlog row 개수
    - `summary.stage.retry_count`
    - `summary.stage.failure_count`
    - `summary.stage.max_attempts`
  - stage 실행 실패 표준 예외 추가
    - `orchestrator_runtime.StageNodeExecutionError`
    - retry 소진 시 node/attempt 정보 포함해 발생
  - HTTP 에러 스키마 표준화
    - `POST /simulate`, `POST /regress` 경로에서 stage 실패 시:
      - `error=stage_execution_failed`
      - `error_code=ORCH_STAGE_FAILED`
      - `stage_node`
      - `attempts`
      - `message`

## 2) Files changed

- `src/project_dream/infra/store.py`
- `src/project_dream/orchestrator_runtime.py`
- `src/project_dream/infra/http_server.py`
- `tests/test_infra_store.py`
- `tests/test_infra_store_sqlite.py`
- `tests/test_web_api.py`
- `tests/test_web_api_http_server.py`
- `docs/plans/2026-02-28-runlog-observability-stage-error-implementation.md` (new)
- `docs/plans/2026-02-28-stage-observability-error-schema-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_orchestrator_runtime.py tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `40 passed`
- Full:
  - `python -m pytest -q`
  - result: `168 passed`

## 4) Notes

- `summary`는 append-only 확장이라 기존 runlog 소비자와 하위 호환된다.
- stage 실패 매핑은 generic `internal_error`와 분리되어 운영 관측/알림 라우팅이 쉬워진다.

## 5) Next recommended step

- 인프라 고도화 2차:
  - 벡터 인덱스 백엔드 추상화 도입(현재 in-memory/파일 기반 검색 경로와 분리)
  - 최소 구현으로 local sqlite/duckdb 메타 인덱스 + pluggable provider 인터페이스 설계
