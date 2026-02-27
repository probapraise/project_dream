# Project Dream Web API Access Logging Design

## Goal

운영 환경 변화가 잦은 상황에서 HTTP 요청 문제를 빠르게 추적할 수 있도록 구조화된 접근 로그를 추가한다.

## Scope

- HTTP 서버에 요청 단위 structured log 추가
- 인증 실패(401, auth false) 이벤트를 일반 요청과 구분
- CLI `serve` 실행 시 stderr JSON 라인 로그 출력

## Log Contract

각 요청마다 다음 필드를 기록한다.

- `event`: `http_request` 또는 `http_auth_failure`
- `method`: `GET` / `POST`
- `path`: 쿼리 제거된 path
- `status`: 응답 상태코드
- `latency_ms`: 요청 처리 시간(ms)
- `auth_ok`: 인증 성공 여부

## Error/Resilience

- 로그 핸들러 내부 실패는 요청 처리에 영향 주지 않음
- 인증 실패는 기존과 동일하게 `401` 응답 유지

## Compatibility

- 기존 API 응답 계약/HTTP 라우트 계약 유지
- 인증 정책(health 제외 토큰 필수) 유지

## Testing Strategy

- HTTP 통합 테스트에서 로그 수집 콜백으로 필드/이벤트 검증
- 전체 테스트 스위트로 회귀 확인
