# Project Dream Stage Node Handler Parity Design

## Goal

`orchestrator_runtime`의 manual/langgraph 백엔드가 동일한 stage helper 함수를 실행하도록 통합해, 백엔드별 로직 드리프트를 줄인다.

## Scope

- `orchestrator_runtime`에 stage node helper 함수 추가
  - `thread_candidate`, `round_loop`, `moderation`, `end_condition`
- manual 백엔드가 stage helper 체인을 직접 실행하도록 변경
- langgraph 백엔드가 동일 stage helper를 node 실행 시 호출하도록 변경
- 회귀 테스트 보강
  - `tests/test_orchestrator_runtime.py`

## Approach

### 1) runtime 내부 stage helper 함수 도입 + 동적 handler 매핑 (Recommended)

- stage마다 `_run_stage_node_*` 함수를 두고, `_resolve_stage_node_handler`로 현재 핸들러를 조회한다.
- manual/langgraph 모두 같은 핸들러 조회 경로를 사용한다.
- 장점: monkeypatch/확장 용이, 백엔드 동작 일치성 보장.
- 단점: 현재 stage helper는 pass-through 기반이라 계산 로직 이관은 다음 단계 필요.

### 2) static dict 매핑으로 고정

- 장점: 코드 단순.
- 단점: 테스트 monkeypatch 반영이 어렵고 런타임 확장성이 낮다.

선택: 1번.

## Contracts

- stage 실행 순서: `SIMULATION_STAGE_NODE_ORDER` 유지
- manual/langgraph 모두 stage helper 실행 결과를 `assemble_sim_result_from_stage_payloads`로 조립
- `graph_node_trace` 스키마/필드 유지
