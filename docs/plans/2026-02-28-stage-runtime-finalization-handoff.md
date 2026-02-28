# Stage Runtime Finalization Handoff (2026-02-28)

## 1) Done in this session

- Target: `P2-10` 후속 (stage runtime finalization)
- Implemented:
  - `sim_orchestrator`에 stage-level 도메인 정규화 함수 추가
    - `run_stage_node_thread_candidate`
    - `run_stage_node_round_loop`
    - `run_stage_node_moderation`
    - `run_stage_node_end_condition`
  - `orchestrator_runtime` stage handler가 위 도메인 함수 호출하도록 전환
  - stage node 공통 재시도 실행기 추가
    - `max_stage_retries` 지원 (`run_simulation_with_backend`)
    - 재시도/성공/최종실패 checkpoint 기록
  - `graph_node_trace` 확장
    - `node_attempts`
    - `stage_checkpoints`
  - batch 수동/StateGraph parity 회귀 테스트 추가

## 2) Files changed

- `src/project_dream/sim_orchestrator.py`
- `src/project_dream/orchestrator_runtime.py`
- `tests/test_orchestrator_runtime.py`
- `docs/plans/2026-02-28-stage-runtime-finalization-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_orchestrator_runtime.py tests/test_sim_orchestrator_stage_nodes.py -q`
  - result: `18 passed`
- Full regression:
  - `python -m pytest -q`
  - result: `167 passed`

## 4) Notes

- 기존 `max_retries`(gate retry)와 신규 `max_stage_retries`(stage node retry)는 역할이 다르다.
- 수동/manual과 langgraph/stategraph 모두 동일한 stage retry/handler 경로를 사용한다.

## 5) Next recommended step

- stage checkpoint 메타를 runlog/repository 레벨로 선택 저장할지 정책 확정
- stage failure를 API 에러 코드/응답 스키마로 표준화
