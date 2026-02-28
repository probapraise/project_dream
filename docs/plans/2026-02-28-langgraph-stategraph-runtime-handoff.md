# LangGraph StateGraph Runtime Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-10` 3차 (langgraph backend에서 실제 StateGraph 노드 실행)
- Implemented:
  - `orchestrator_runtime`에 langgraph StageGraph 실행 경로 추가
    - `langgraph.graph`에서 `StateGraph/START/END` 동적 로드
    - 노드 체인:
      - `thread_candidate`
      - `round_loop`
      - `moderation`
      - `end_condition`
    - compiled graph `invoke` 후 실행 노드 이력(`executed_nodes`) 수집
  - `graph_node_trace.v1` 확장
    - `execution_mode` (`manual` | `stategraph`)
    - `node_order`
    - `executed_nodes`
  - `manual` 경로는 기존 실행 유지 + trace만 확장

## 2) Files changed

- `src/project_dream/orchestrator_runtime.py`
- `tests/test_orchestrator_runtime.py`
- `docs/plans/2026-02-28-langgraph-stategraph-runtime-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_orchestrator_runtime.py -q`
  - result: `5 passed`
- Integration:
  - `python -m pytest tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_cli_smoke.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `39 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `147 passed`

## 4) Notes

- 실제 business simulation 계산은 기존 `run_simulation`을 재사용한다.
- 이번 단계는 backend 경로에서 StateGraph 노드 체인 실행/관측을 추가한 것이며,
  - 후속 단계에서 stage별 계산을 독립 node function으로 분리 가능.

## 5) Next recommended step

- `P2-10` 4차:
  - `run_simulation` 내부 주요 단계를 node별 pure function으로 분해
  - manual/langgraph 양쪽이 동일 node function을 공유하도록 통합
