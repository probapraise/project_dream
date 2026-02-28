# Vector Backend Env Defaults Handoff (2026-02-28)

## 1) Done in this session

- Target: 3차 후속 (벡터 백엔드 운영 편의 고도화)
- Implemented:
  - CLI 벡터 옵션 기본값을 환경변수에서 읽도록 확장
    - `PROJECT_DREAM_VECTOR_BACKEND` (`memory|sqlite`)
    - `PROJECT_DREAM_VECTOR_DB_PATH` (optional path)
  - 환경변수 값 검증 추가
    - `PROJECT_DREAM_VECTOR_BACKEND`가 미지원 값이면 `build_parser()`에서 `ValueError`
  - 운영 문서 반영
    - `.env.example`에 벡터 기본값 항목 추가
    - `README.md` Local Ops 섹션에 벡터 env 기본값 사용법 추가
  - E2E 포함 테스트 보강
    - env 기본값이 `simulate/regress/regress-live/serve` parser 기본값에 반영되는지 검증
    - `simulate/regress` 실행 시 env 기반 sqlite 벡터 DB 파일 생성 및 회귀 summary 설정 반영 검증

## 2) Changed files

- `src/project_dream/cli.py`
- `tests/test_cli_smoke.py`
- `tests/test_cli_simulate_e2e.py`
- `tests/test_cli_regress_e2e.py`
- `.env.example`
- `README.md`
- `docs/plans/2026-02-28-vector-backend-env-defaults-handoff.md` (new)

## 3) Verification

- Targeted:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_cli_smoke.py tests/test_cli_simulate_e2e.py tests/test_cli_regress_e2e.py -q`
  - result: `18 passed`
- Broader CLI/API:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_cli_regress_live.py tests/test_cli_smoke.py tests/test_cli_regress_e2e.py tests/test_cli_simulate_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `39 passed`
- Full:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`
  - result: `179 passed`

## 4) Notes

- CLI 플래그(`--vector-backend`, `--vector-db-path`)를 명시하면 env 기본값보다 우선한다.
- env 미설정 시 기존 기본값(`memory`, `None`) 동작을 유지한다.

## 5) Next recommended step

- 4차 후속:
  - `scripts/dev_serve.sh`, `scripts/regress_live.sh`에서 벡터 옵션을 명시적으로 전달하는 플래그 지원 추가
  - smoke API 스크립트에 sqlite 벡터 모드 점검 케이스 추가
