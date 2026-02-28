# Project Dream Persona Pack Casting Design

## Goal

`dev_spec` 6.4에 맞춰 `persona_service`를 Pack 기반 캐스팅으로 개선하고, 시뮬레이션에서 페르소나 ID(`Pxx`)를 우선 사용하도록 만든다.

## Scope

- `select_participants`에 Pack 기반 우선순위 캐스팅 추가
  - 우선순위: `board_id + zone_id` 일치 > `board_id` 일치 > 기타
  - 결과는 seed/round 기반으로 결정론적(deterministic) 순서 유지
- `render_voice(persona_id, zone_id)` API 추가
  - archetype 스타일에 따른 말투 제약 반환
- `sim_orchestrator`가 packs 전달 시 Pack 기반 참가자 선택 사용
- 관련 테스트 추가/보강

## Approaches

### 1) In-place 확장 (Recommended)

- 설명: 기존 `persona_service` 시그니처를 확장하고 fallback 경로를 유지
- 장점: 변경 범위 작고 기존 테스트/흐름 영향 최소화
- 단점: persona 메모리까지는 아직 미포함

### 2) 신규 캐스팅 엔진 모듈 분리

- 설명: `persona_selector.py`를 새로 만들어 로직 분리
- 장점: 장기 유지보수에 유리
- 단점: 현재 단계에서는 과설계

### 3) DB/스토리지 기반 메모리까지 동시 도입

- 설명: persona_memory 누적/조회까지 이번 단계에 포함
- 장점: `dev_spec` 전체 충족에 가까움
- 단점: 저장 계약 확장 범위가 커져 리스크 증가

선택: 1번.

## Data Flow

1. `sim_orchestrator`가 `select_participants(seed, round_idx, packs=...)` 호출
2. `persona_service`가 packs의 `personas -> communities`를 참조해 후보군 정렬
3. 결정론적 회전으로 라운드별 참가자 순서를 생성
4. `run_simulation`는 상위 3명을 사용해 댓글/액션 로그 생성

## Compatibility

- packs가 없을 때는 기존 fallback(`AG-*`) 유지
- 기존 호출부는 인자 추가 없이 동작

## Testing Strategy

- `tests/test_persona_service.py` 신규
  - Pack 기반 캐스팅 우선순위 검증
  - fallback 경로 검증
  - `render_voice` 계약 검증
- `tests/test_phase2_simulation_context.py` 보강
  - packs 사용 시 `persona_id` 형식이 `P`로 시작하는지 검증
