# Project Dream Moderation Stage Design

## Goal

시뮬레이션의 `MaybeModeration` 노드를 명시 데이터로 노출해, 라운드별 운영 판단(`NO_OP` 포함)을 결과와 runlog에서 추적 가능하게 만든다.

## Scope

- `run_simulation` 반환값에 `moderation_decisions` 추가
- 각 라운드마다 운영 판단 1건 기록
- `storage.persist_run`에 `moderation_decision` 이벤트 저장
- 테스트 보강
  - `tests/test_phase2_simulation_context.py`
  - `tests/test_infra_store.py`

## Approach

### 1) 라운드 단위 단일 결정 기록 (Recommended)

- 설명: 한 라운드에서 최종적으로 관측된 운영 액션을 1건으로 기록
- 필드: `round`, `action_type`, `reason_rule_id`, `status_before`, `status_after`, `report_total`
- 장점: runlog 해석이 단순하고 대시보드 집계가 쉬움
- 단점: 한 라운드 내 다중 정책전이를 모두 보존하지는 않음(상세는 기존 action 로그 참조)

### 2) 정책전이 전체를 별도 배열로 보존

- 설명: 라운드 내 모든 정책전이를 전부 moderation 이벤트로 저장
- 장점: 세밀한 분석 가능
- 단점: 중복 이벤트 증가, 요약 소비자 복잡도 증가

선택: 1번.

## Contracts

- 시뮬레이션 반환 필드 추가
  - `moderation_decisions: list[dict]`
- runlog 이벤트 타입 추가
  - `moderation_decision`
