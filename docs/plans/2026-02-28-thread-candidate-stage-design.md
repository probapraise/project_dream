# Project Dream Thread Candidate Stage Design

## Goal

시뮬레이션 루프 시작 전에 `thread 후보 생성 -> 선정` 단계를 명시적으로 추가해, `Seed -> Thread -> Comment` 파이프라인의 핵심 흐름을 runlog로 추적 가능하게 만든다.

## Scope

- `sim_orchestrator.run_simulation`에 thread 후보 3개 생성 단계 추가
- 후보 중 1개를 선택하는 선정 로직 추가
- 각 round 로그에 선택된 후보 ID 연결
- 저장 시 `runlog.jsonl`에 `thread_candidate` / `thread_selected` 이벤트 저장
- 관련 테스트 보강
  - `tests/test_phase2_simulation_context.py`
  - `tests/test_infra_store.py`

## Approach

### 1) Deterministic 후보 생성 (Recommended)

- 설명: 현재 Echo 기반 생성 경계 안에서 deterministic 후보를 구성
- 장점: 테스트 안정성 높음, 이후 LLM 기반 랭킹/선정으로 교체 용이
- 단점: 후보 다양성은 제한적

### 2) 즉시 LLM 기반 후보 생성/랭킹

- 설명: 후보 생성과 점수 계산에 LLM 결과를 직접 반영
- 장점: 표현 다양성 향상 가능
- 단점: 비결정성 증가, 회귀 테스트와 디버깅 난이도 상승

선택: 1번.

## Contracts

- 시뮬레이션 반환 필드
  - `thread_candidates: list[dict]`
  - `selected_thread: dict`
- round row 확장
  - `thread_candidate_id: str`
- runlog 이벤트 타입 추가
  - `thread_candidate`
  - `thread_selected`

## Compatibility

- 기존 소비자(`evaluate`, `regress`, Web API)는 필수 이벤트 타입(`round/gate/action`)만 요구하므로 하위 호환 유지.
- 신규 필드는 append-only 형태라 기존 저장 포맷과 충돌하지 않는다.
