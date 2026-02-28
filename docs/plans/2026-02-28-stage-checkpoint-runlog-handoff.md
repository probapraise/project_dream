# Stage Checkpoint Runlog Handoff (2026-02-28)

## 1) Done in this session

- Target: stage retry/checkpoint 실행 메타를 저장소/API에서 조회 가능하게 노출
- Implemented:
  - `storage.persist_run` 확장
    - `graph_node_attempt` 이벤트 기록 (`node_attempts` 기반)
    - `stage_checkpoint` 이벤트 기록 (`stage_checkpoints` 기반)
  - `FileRunRepository.list_runs` 메타 확장
    - `stage_retry_count`
    - `stage_failure_count`
    - `max_stage_attempts`
  - `SQLiteRunRepository` 인덱스/목록 메타 확장
    - runs 테이블 컬럼 추가 + 마이그레이션(ALTER TABLE)
      - `stage_retry_count`
      - `stage_failure_count`
      - `max_stage_attempts`
    - run index upsert/list 응답에 동일 필드 반영
  - API 계층은 repository passthrough 구조라 별도 라우트 변경 없이 `/runs` 응답에 자동 반영

## 2) Files changed

- `src/project_dream/storage.py`
- `src/project_dream/infra/store.py`
- `tests/test_infra_store.py`
- `tests/test_infra_store_sqlite.py`
- `tests/test_web_api.py`
- `tests/test_web_api_http_server.py`
- `docs/plans/2026-02-28-stage-checkpoint-runlog-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `27 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `167 passed`

## 4) Notes

- 기존 runlog 소비자는 새로운 event type을 무시해도 동작하도록 append-only 방식으로 추가했다.
- SQLite는 기존 DB에도 `ALTER TABLE`로 컬럼을 추가하므로 재초기화 없이 반영된다.

## 5) Next recommended step

- `/runs/{id}/runlog` 응답에 `type`별 요약 카운트(예: checkpoint retry/fail count)를 함께 제공할지 여부 결정
- stage failure를 API 에러 스키마에 표준 매핑하는 정책 정의
