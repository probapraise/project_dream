# Round Loop Node Split Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-10` 5차 (round loop 내부 세부 node 함수 분해)
- Implemented in `sim_orchestrator`:
  - round loop node order 상수 추가
    - `ROUND_LOOP_NODE_ORDER = (generate_comment, gate_retry, policy_transition, emit_logs)`
  - node helper 함수 분리
    - `_round_node_generate_comment(...)`
    - `_round_node_gate_retry(...)`
    - `_round_node_policy_transition(...)`
    - `_round_node_emit_logs(...)`
  - `run_simulation` 내부 루프를 helper 호출 체인으로 리팩터링
  - round row에 `round_loop_nodes` trace 필드 추가
- Stage payload 타입 고정 강화
  - `SimulationStagePayloads` 및 stage별 `TypedDict` 추가

## 2) Files changed

- `src/project_dream/sim_orchestrator.py`
- `tests/test_sim_orchestrator_stage_nodes.py`
- `docs/plans/2026-02-28-round-loop-node-split-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_sim_orchestrator_stage_nodes.py tests/test_orchestrator_runtime.py -q`
  - result: `12 passed`
- Integration:
  - `python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py tests/test_infra_store_sqlite.py tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_cli_simulate_e2e.py tests/test_cli_regress_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py -q`
  - result: `42 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `154 passed`

## 4) Notes

- 도메인 계산 결과는 유지하고 구조만 node helper 체인으로 분해했다.
- helper 단위 분리로 이후 langgraph node function 이식 시 매핑이 단순해졌다.

## 5) Next recommended step

- `P2-10` 6차:
  - 현재 helper node들을 langgraph state node와 1:1 연결해 manual/langgraph 모두 동일 helper를 직접 실행하도록 통합
