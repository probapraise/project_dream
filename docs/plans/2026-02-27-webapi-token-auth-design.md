# Project Dream Web API Token Auth Design

## Goal

환경 이동이 잦은 개인 사용 시나리오에서도 API 노출 실수를 줄이기 위해 HTTP 인증 경계를 추가한다.

## Scope

- 인증 제외: `GET /health`
- 인증 필수: 그 외 모든 HTTP 엔드포인트(`GET`, `POST`)
- 인증 방식: `Authorization: Bearer <token>`
- 서버 토큰 입력: `serve --api-token` 또는 환경변수 `PROJECT_DREAM_API_TOKEN`

## Auth Rules

- 토큰 누락/불일치: `401`
- 응답: `{ "error": "unauthorized" }`
- `health`는 토큰 없이 항상 `200`

## CLI Contract

- `project-dream serve` 실행 시 토큰이 반드시 필요
- 우선순위: `--api-token` > `PROJECT_DREAM_API_TOKEN`
- 둘 다 없으면 즉시 종료(사용법 에러)

## Compatibility

- 애플리케이션 서비스/저장소/평가 로직 영향 없음
- Web API facade는 그대로, HTTP 서버 경계에서만 인증 적용

## Testing Strategy

- HTTP 통합 테스트:
  - 무인증 `health` 성공
  - 무인증/오토큰(non-health) `401`
  - 정상 토큰으로 기존 시뮬/평가/회귀/조회 흐름 성공
- CLI 테스트:
  - `serve`에서 토큰 미설정 시 실패 확인
