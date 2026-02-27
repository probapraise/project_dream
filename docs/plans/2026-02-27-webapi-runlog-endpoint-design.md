# Project Dream Web API Runlog Endpoint Design

## Goal

run 디버깅을 위해 API에서 runlog 이벤트 목록을 직접 조회할 수 있게 한다.

## Scope

- API facade 메서드 추가: `get_runlog(run_id)`
- HTTP 엔드포인트 추가: `GET /runs/{run_id}/runlog`
- 저장소에 runlog 로딩 메서드 추가

## Endpoint Contract

### `GET /runs/{run_id}/runlog`

response:
```json
{
  "run_id": "run-...",
  "rows": [
    {"type": "round", "...": "..."},
    {"type": "gate", "...": "..."},
    {"type": "action", "...": "..."}
  ]
}
```

## Error Handling

- run 미존재: `404`
- runlog 파일 미존재: `404`

## Compatibility

- 기존 API 계약과 독립
- 기존 CLI 영향 없음

## Testing Strategy

- API facade 테스트에 runlog 조회 추가
- HTTP 통합 테스트에 `GET /runs/{id}/runlog` 추가
