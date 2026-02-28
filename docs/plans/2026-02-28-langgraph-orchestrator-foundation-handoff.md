# LangGraph Orchestrator Foundation Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-10` 1차 기반 (`manual -> langgraph` 전환 준비)
- Implemented:
  - 신규 런타임 분기 모듈 `orchestrator_runtime.py`
    - `run_simulation_with_backend(..., backend=...)`
    - 지원 backend: `manual`, `langgraph`
    - `langgraph` 선택 시 의존성 체크(`langgraph` 미설치면 명확한 RuntimeError)
  - 실행 경로 연결
    - `app_service.simulate_and_persist`에 `orchestrator_backend` 인자 추가
    - `regression_runner.run_regression_batch`에 `orchestrator_backend` 인자 추가
    - `web_api.simulate/regress` 및 HTTP `/simulate`, `/regress` body에 backend 전달 지원
  - CLI 확장
    - `simulate`, `regress`, `regress-live`에 `--orchestrator-backend {manual,langgraph}` 추가
    - 기본값은 `manual`로 유지(기존 동작 호환)

## 2) Files changed

- `src/project_dream/orchestrator_runtime.py` (new)
- `src/project_dream/app_service.py`
- `src/project_dream/regression_runner.py`
- `src/project_dream/infra/web_api.py`
- `src/project_dream/infra/http_server.py`
- `src/project_dream/cli.py`
- `tests/test_orchestrator_runtime.py` (new)
- `tests/test_app_service_kb_context.py`
- `tests/test_regression_runner.py`
- `tests/test_cli_smoke.py`
- `docs/plans/2026-02-28-langgraph-orchestrator-foundation-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_cli_smoke.py tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_orchestrator_runtime.py -q`
  - result: `23 passed`
- Integration:
  - `python -m pytest tests/test_cli_simulate_e2e.py tests/test_cli_evaluate_e2e.py tests/test_cli_regress_e2e.py tests/test_cli_regress_live.py tests/test_web_api.py tests/test_web_api_http_server.py tests/test_orchestrator.py -q`
  - result: `24 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `146 passed`

## 4) Compatibility and limitations

- 기본 backend는 여전히 `manual`이라 기존 호출은 무변경으로 동작한다.
- `langgraph` backend는 현재 “의존성 확인 + 기존 오케스트레이터 재사용” 단계이며,
  - 실제 StateGraph 기반 단계별 노드 분해는 후속 작업으로 남긴다.

## 5) Next recommended step

- `P2-10` 2차:
  - 시뮬레이션 스테이지를 LangGraph 노드(`thread_candidate -> round_loop -> moderation -> end_condition`)로 분해
  - stage trace와 graph node trace 매핑 검증 테스트 추가
  - `manual/langgraph` 결과 동등성 회귀 테스트 도입
