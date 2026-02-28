# LangGraph Stage Graph Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-10` 2차 (stage-node trace 매핑 + backend 동등성 검증)
- Implemented:
  - `orchestrator_runtime`에서 backend 실행 결과에 `graph_node_trace.v1` 자동 첨부
    - node order:
      - `thread_candidate`
      - `round_loop`
      - `moderation`
      - `end_condition`
    - node별 `event_type/event_count` 집계 포함
  - `manual/langgraph` 경로 동등성 테스트 추가
    - 핵심 산출물(`thread_state`, `selected_thread`, `end_condition`, round/gate/action 길이) 동등성 검증
  - runlog 직렬화 확장
    - `storage.persist_run`에서 `graph_node_trace`를 `type=graph_node` 이벤트로 저장

## 2) Files changed

- `src/project_dream/orchestrator_runtime.py`
- `src/project_dream/storage.py`
- `tests/test_orchestrator_runtime.py`
- `tests/test_infra_store.py`
- `tests/test_infra_store_sqlite.py`
- `docs/plans/2026-02-28-langgraph-stage-graph-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_orchestrator_runtime.py tests/test_infra_store.py tests/test_infra_store_sqlite.py -q`
  - result: `12 passed`
- Integration:
  - `python -m pytest tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_cli_smoke.py tests/test_cli_simulate_e2e.py tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `35 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `147 passed`

## 4) Compatibility and notes

- 기본 backend(`manual`) 동작은 유지된다.
- `langgraph` backend는 여전히 의존성 체크(`langgraph` 패키지 설치 필요)를 수행한다.
- graph-node trace는 backend와 무관하게 산출되어 runlog 분석에서 stage-node 관측이 가능하다.

## 5) Next recommended step

- `P2-10` 3차:
  - 실제 LangGraph `StateGraph` 노드 구현으로 `run_simulation` 내부 단계를 물리적으로 분리
  - 현재 `graph_node_trace` 집계 기반 검증을 graph 실행 이력 기반 검증으로 전환
