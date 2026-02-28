# Vector Script Hardening Handoff (2026-02-28)

## 1) Done in this session

- Target: 4차 후속 (운영 스크립트 벡터 옵션 전달 강화)
- Implemented:
  - `scripts/dev_serve.sh`
    - `PROJECT_DREAM_VECTOR_BACKEND`, `PROJECT_DREAM_VECTOR_DB_PATH` 지원
    - CLI 실행 시 `--vector-backend/--vector-db-path` 명시 전달
  - `scripts/regress_live.sh`
    - `PROJECT_DREAM_LIVE_VECTOR_BACKEND`, `PROJECT_DREAM_LIVE_VECTOR_DB_PATH` 지원
    - 미설정 시 `PROJECT_DREAM_VECTOR_*`로 fallback
    - `--update-baseline`/vector 옵션을 배열 기반으로 안정적으로 조립
  - `scripts/smoke_api.sh`
    - `PROJECT_DREAM_SMOKE_VECTOR_SQLITE_CHECK=1`일 때 sqlite 벡터 모드 추가 점검
    - `PROJECT_DREAM_SMOKE_VECTOR_DB_PATH` 경로에 DB 파일 생성 여부 검증

## 2) Changed files

- `scripts/dev_serve.sh`
- `scripts/regress_live.sh`
- `scripts/smoke_api.sh`
- `.env.example`
- `README.md`
- `tests/test_local_ops_scripts.py` (new)
- `docs/plans/2026-02-28-vector-script-hardening-handoff.md` (new)

## 3) Verification

- RED->GREEN target:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_local_ops_scripts.py -q`
  - result: `3 passed`
- Related:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_cli_smoke.py tests/test_cli_regress_live.py tests/test_local_ops_scripts.py -q`
  - result: `20 passed`
- Full:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`
  - result: `182 passed`

## 4) Notes

- 스크립트는 CLI env 기본값 의존 대신, 운영에서 혼동이 없도록 벡터 옵션을 명시적으로 전달한다.
- `smoke_api.sh` 기본 동작은 유지되며, sqlite 벡터 점검은 opt-in이다.
