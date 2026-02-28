# Project Dream Round Summary Stage Design

## Goal

시뮬레이션 라운드별 상태를 `SummarizeRound` 단계로 집계해 runlog에서 라운드 단위 분석이 가능하도록 한다.

## Scope

- `sim_orchestrator.run_simulation`에 `round_summaries` 산출 추가
- `storage.persist_run`에 `round_summary` 이벤트 저장 추가
- 테스트 보강
  - `tests/test_phase2_simulation_context.py`
  - `tests/test_infra_store.py`

## Approach

### 1) 라운드 후행 집계 (Recommended)

- 설명: 댓글/액션 로그 생성이 끝난 뒤 라운드별 요약을 집계
- 집계 필드: `participant_count`, `report_events`, `policy_events`, `status`, `max_score`
- 장점: 기존 루프를 크게 건드리지 않고 결정적 결과 제공
- 단점: 실시간 스트리밍 요약에는 부적합

### 2) 루프 중 실시간 누적 집계

- 설명: 댓글 생성 시점마다 라운드 집계를 동기 갱신
- 장점: 스트리밍/실시간 UI로 확장 용이
- 단점: 상태 동기화 코드 복잡도 증가

선택: 1번.

## Contracts

- 시뮬레이션 반환 필드 추가
  - `round_summaries: list[dict]`
- runlog 이벤트 타입 추가
  - `round_summary`
