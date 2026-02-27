# Project Dream Phase 2A Design: Environment State Machine

## Goal

플랫폼 환경 규칙을 상태머신으로 고도화하여 `hidden -> locked -> ghost -> sanctioned` 전이를 명시적으로 처리한다.

## Scope

- `env_engine`에 상태 전이 함수 추가
  - 입력: 현재 상태, 보고/위반/항소/운영 액션
  - 출력: 다음 상태 + 액션 로그 이벤트
- `sim_orchestrator`에서 전이 함수 사용
- runlog에 `prev_status`, `next_status`, `reason_rule_id` 포함
- 회귀 테스트 추가

## Contracts

- Status: `visible`, `hidden`, `locked`, `ghost`, `sanctioned`
- Action: `REPORT`, `HIDE_PREVIEW`, `LOCK_THREAD`, `GHOST_THREAD`, `SANCTION_USER`, `APPEAL`
- 이벤트 스키마 필수 키:
  - `action_type`
  - `prev_status`
  - `next_status`
  - `reason_rule_id`

## Non-Goals

- 리포트 템플릿 고도화
- eval_suite 자동화
