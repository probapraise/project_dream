# SQLite Run Repository Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-9` (파일 저장소 외 DB 계층 도입의 1차)
- Implemented:
  - 신규 `SQLiteRunRepository` 추가
    - run 메타데이터 인덱스(`runs.sqlite3`) 유지
    - `persist_run/persist_eval/find_latest_run/get_run` 지원
    - report/eval/runlog 및 regression summary 로드 API는 파일 아티팩트와 호환 유지
  - CLI 저장소 백엔드 토글 추가
    - `simulate/evaluate/eval-export/serve`에
      - `--repo-backend {file,sqlite}`
      - `--sqlite-db-path <path>`
  - API 팩토리 백엔드 선택 보강 검증
    - `ProjectDreamAPI.for_local_filesystem(...)`의 `repository_backend/sqlite_db_path` 경로 테스트 추가

## 2) Files changed

- `src/project_dream/infra/store.py`
- `src/project_dream/infra/web_api.py`
- `src/project_dream/cli.py`
- `tests/test_infra_store_sqlite.py` (new)
- `tests/test_cli_smoke.py`
- `tests/test_cli_evaluate_e2e.py`
- `tests/test_web_api.py`
- `docs/plans/2026-02-28-sqlite-run-repository-handoff.md` (new)

## 3) Verification

- Targeted RED/GREEN cycle:
  - `python -m pytest tests/test_cli_smoke.py tests/test_cli_evaluate_e2e.py::test_cli_simulate_evaluate_eval_export_with_sqlite_backend tests/test_web_api.py::test_web_api_for_local_filesystem_supports_sqlite_backend tests/test_web_api.py::test_web_api_for_local_filesystem_rejects_unknown_backend -q`
  - result: `11 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `138 passed`

## 4) Compatibility notes

- 기본값은 기존과 동일하게 `file` backend이며, 기존 실행 스크립트는 인자 추가 없이 그대로 동작함.
- `sqlite` backend는 옵션형으로 추가되어 이후 벡터DB/그래프 저장소 계층 확장 시 인터페이스를 재사용 가능.

## 5) Next recommended step

- `P2-9` 후속으로 저장소 추상화 확장:
  - run 메타데이터 조회 API(필터/페이지네이션) 추가
  - 회귀/리포트 집계의 DB 인덱스 경로 도입
  - 이후 `P2-10` LangGraph 오케스트레이션 도입 시 실행 상태 추적과 연결
