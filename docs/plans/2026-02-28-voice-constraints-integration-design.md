# Project Dream Voice Constraints Integration Design

## Goal

`persona_service.render_voice`를 시뮬레이션 생성 경로에 실제로 연결해, 페르소나별 말투 제약이 런타임 프롬프트에 반영되도록 한다.

## Scope

- `sim_orchestrator`에서 `render_voice(persona_id, zone_id, packs=...)` 호출
- `generate_comment`에 `voice_constraints` 전달
- prompt에 안정적인 보이스 힌트(`sentence_length`, `endings`, `taboo_count`)를 추가
- 테스트로 전달/반영 동작 보장

## Approach

### 1) Prompt Hint Injection (Recommended)

- 설명: 보이스 제약 전체를 그대로 넣지 않고 핵심 요약 힌트만 프롬프트에 부착
- 장점: 구현 단순, 테스트 가능, 런타임 동작 가시성 높음
- 단점: 강제력은 낮고 힌트 수준

### 2) Post-generation Rewrite

- 설명: 생성 후 말미/문장 길이를 규칙 기반으로 강제 수정
- 장점: 제약 준수율 높음
- 단점: 규칙 부작용 및 문장 품질 저하 위험

선택: 1번.

## Safety/Regression Consideration

- lore 게이트 키워드(`근거/증거/로그`)를 보이스 힌트에 넣지 않는다.
- 힌트는 `voice=style:<...>;endings:<...>;taboo_count:<n>` 형식으로 제한한다.

## Testing Strategy

- `tests/test_generator.py`
  - `voice_constraints` 입력 시 prompt에 `voice=` 힌트가 포함되는지 검증
- `tests/test_voice_constraints_integration.py`
  - `sim_orchestrator`가 `render_voice` 결과를 `generate_comment`로 전달하는지 검증
