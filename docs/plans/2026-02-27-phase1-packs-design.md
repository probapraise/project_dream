# Project Dream Phase 1 Packs Design

## Goal

`dev_spec`의 Phase 1(MVP 최소 충족) 요구를 만족하도록 Pack 데이터와 검증 경계를 확장한다.

## Scope

- `packs/`에 다음 파일 추가
  - `board_pack.json` (B01~B18)
  - `community_pack.json` (COM-PLZ-001~004)
  - `rule_pack.json` (RULE-* 최소 15개)
  - `entity_pack.json` (org 5+, char 10+)
  - `persona_pack.json` (archetype 최소 골격)
  - `template_pack.json` (T1~T12, P1~P6 최소 골격)
- `pack_service` 확장
  - 다중 팩 로딩
  - 참조 무결성 검사
  - 최소 개수 조건 검사
- 테스트 강화
  - 개수 조건
  - ID 패턴 및 참조 검증

## Non-Goals

- LLM 연동 고도화
- 환경 엔진 규칙 확장
- API 레이어 추가

## Contracts

- ID 패턴 고정: `Bxx`, `COM-PLZ-xxx`, `RULE-*`, `ORG-*`, `CHAR-*`, `AG-*`, `T1~T12`, `P1~P6`
- 추가 필드 허용: Pack 데이터는 스키마 확장을 전제로 하고, 검증은 필수 필드와 참조 무결성 위주로 유지

## Risks and Mitigation

- 데이터 확장 시 로더 파손 위험: 로더 테스트를 데이터와 함께 버전 잠금
- 추후 고도화 시 재작성 위험: 인터페이스 유지 + 추가 필드 허용
