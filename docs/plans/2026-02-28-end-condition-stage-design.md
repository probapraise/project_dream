# Project Dream End Condition Stage Design

## Goal

시뮬레이션 루프에 종료 조건을 명시해 `언제/왜 종료됐는지`를 결과와 runlog에서 추적 가능하게 만든다.

## Scope

- `run_simulation`에 종료 조건 판단 추가
- 종료 메타데이터를 `thread_state`와 최상위 결과에 기록
- 저장 시 `runlog.jsonl`에 `end_condition` 이벤트 기록
- 테스트 보강
  - `tests/test_phase2_simulation_context.py`
  - `tests/test_infra_store.py`

## Approach

### 1) 최소 종료 규칙 고정 (Recommended)

- 설명: MVP에서는 2가지 종료만 지원
  - `round_limit` (지정 라운드 소진)
  - `moderation_lock` (상태가 `locked/ghost/sanctioned`에 도달)
- 장점: 규칙이 단순하고 디버깅이 쉽다
- 단점: 갈등 수렴/품질 기반 종료는 아직 미지원

### 2) 복합 점수 기반 종료

- 설명: 신고량, 점수, 갈등 다양성 등을 종합해 종료
- 장점: 더 현실적 종료 가능
- 단점: 파라미터 조정 비용이 크고 비결정성이 증가

선택: 1번.

## Contracts

- 시뮬레이션 반환 필드
  - `end_condition: {termination_reason, ended_round, ended_early, status}`
- `thread_state` 확장
  - `termination_reason`
  - `ended_round`
  - `ended_early`
- runlog 이벤트 타입 추가
  - `end_condition`
