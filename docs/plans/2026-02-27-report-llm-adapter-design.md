# Project Dream Report LLM Adapter Design

## Goal

`report` 생성 경로(요약, 대화 후보)에 `llm_client` 어댑터 경계를 확장해, comment와 동일하게 LLM 공급자 교체가 가능하도록 만든다.

## Scope

- `build_report_v1(...)`에 `llm_client` 주입 포인트 추가
- summary 생성 시 LLM client 호출
- dialogue 후보 line 생성 시 LLM client 호출
- 기본값은 `EchoLLMClient`로 유지하여 현재 출력 하위호환

## Approach

### 1) `build_report_v1` 내부 주입 (Recommended)

- 장점: 변경 범위 최소, 기존 call-site 유지
- 단점: report_generator가 인프라 의존(LLM client)을 직접 참조

### 2) 별도 report generation service 도입

- 장점: 계층 분리 명확
- 단점: 현 단계에서 구조 과도

선택: 1번.

## Interface Contract

- `build_report_v1(seed, sim_result, packs, llm_client=None, template_set="v1")`
- `llm_client is None`이면 `EchoLLMClient()` 사용
- 호출 task:
  - `report_summary`
  - `report_dialogue_candidate`

## Template Contract

`prompt_templates`에 아래 키 추가:
- `report_dialogue_candidate` (기본: `{text}`)

기존 `report_summary` 템플릿은 재사용.

## Compatibility

- 기존 코드에서 인자 추가 없이 동일 동작
- 기존 테스트 기대치 유지
- 커스텀 client 주입 시 summary/line 오버라이드 가능

## Testing Strategy

- report 생성 테스트에 custom fake client 주입 검증 추가
- summary가 fake 결과로 대체되는지 검증
- dialogue line이 task 호출을 통해 생성되는지 검증
