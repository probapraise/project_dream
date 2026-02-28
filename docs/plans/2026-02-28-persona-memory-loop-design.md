# Project Dream Persona Memory Loop Design

## Goal

`dev_spec` 6.4의 `persona_memory` 요구를 MVP 수준으로 반영해, 각 페르소나가 라운드 간 자신의 이전 발화 요약을 기억하도록 한다.

## Scope

- `sim_orchestrator`에 페르소나별 메모 누적 구조 추가
- 댓글 생성 시 이전 메모를 `memory_hint`로 전달
- run 결과에 `persona_memory`와 라운드별 `memory_before`/`memory_after` 기록
- `gen_engine.generate_comment`가 `memory_hint`를 프롬프트에 반영

## Approach

### 1) Orchestrator In-Memory Loop (Recommended)

- 설명: 시뮬레이션 실행 중 메모를 dict로 누적하고, 생성 프롬프트에 힌트로 주입
- 장점: 저장소/스키마 변경 최소, 즉시 적용 가능
- 단점: 실행 간 지속 저장은 없음

### 2) 외부 저장소 기반 메모리

- 설명: runlog/DB에서 persona state를 읽고 써서 실행 간 연속성 제공
- 장점: 장기 일관성 강화
- 단점: 현재 MVP 범위를 넘어서는 구조 변경 필요

선택: 1번.

## Data Flow

1. 라운드 시작 시 `persona_id`별 `memory_before` 요약 추출
2. `generate_comment(..., memory_hint=memory_before)` 호출
3. 게이트 통과 후 최종 텍스트를 메모 엔트리로 누적
4. `memory_after`를 라운드 로그에 기록
5. 최종 결과에 `persona_memory` 맵 포함

## Testing Strategy

- `tests/test_persona_memory_loop.py`
  - 2라운드 실행에서 2라운드 호출의 `memory_hint`가 비어있지 않은지 검증
  - 결과에 `persona_memory`가 기록되는지 검증
- `tests/test_generator.py`
  - `memory_hint` 인자 전달 시 프롬프트에 포함되는지 검증
