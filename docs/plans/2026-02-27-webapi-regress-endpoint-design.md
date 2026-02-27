# Project Dream Web API Regress Endpoint Design

## Goal

HTTP API에서 회귀 배치 실행을 직접 호출할 수 있도록 `POST /regress` 엔드포인트를 추가한다.

## Scope

- `ProjectDreamAPI.regress(...)` 메서드 추가
- HTTP 서버에 `POST /regress` 라우팅 추가
- 회귀 summary JSON 응답 반환
- API/HTTP 테스트 추가

## Endpoint Contract

### `POST /regress`

request body:
```json
{
  "seeds_dir": "examples/seeds/regression",
  "rounds": 4,
  "max_seeds": 10,
  "metric_set": "v2",
  "min_community_coverage": 2,
  "min_conflict_frame_runs": 2,
  "min_moderation_hook_runs": 1,
  "min_validation_warning_runs": 1
}
```

response:
- `regression.v1` summary payload

## Architecture

- `app_service.py`에 `regress_and_persist(...)` 유즈케이스 추가
- `ProjectDreamAPI.regress(...)`는 유즈케이스 호출만 담당
- HTTP handler는 body 파싱 후 API 메서드 호출

## Error Handling

- invalid body: `400`
- file/path issue: `404`
- internal error: `500`

## Compatibility

- 기존 `health/simulate/evaluate` 계약 불변
- CLI `regress` 명령과 같은 내부 로직을 API에서도 재사용

## Testing Strategy

- `tests/test_web_api.py`:
  - API facade `regress()` 호출 검증
- `tests/test_web_api_http_server.py`:
  - `POST /regress` end-to-end 검증
