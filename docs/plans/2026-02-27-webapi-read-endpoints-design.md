# Project Dream Web API Read Endpoints Design

## Goal

생성/평가 실행 결과를 API에서 조회할 수 있도록 read 엔드포인트를 추가한다.

## Scope

- API facade 메서드 추가
  - `latest_run()`
  - `get_report(run_id)`
  - `get_eval(run_id)`
- HTTP 엔드포인트 추가
  - `GET /runs/latest`
  - `GET /runs/{run_id}/report`
  - `GET /runs/{run_id}/eval`
- 저장소에 JSON 로드 메서드 추가

## Endpoint Contract

### `GET /runs/latest`
- response:
```json
{
  "run_id": "run-...",
  "run_dir": "..."
}
```

### `GET /runs/{run_id}/report`
- response: `report.v1` payload

### `GET /runs/{run_id}/eval`
- response: `eval.v1` payload

## Error Handling

- run 미존재: `404`
- report/eval 파일 미존재: `404`
- invalid path: `404`

## Compatibility

- 기존 `/health`, `/simulate`, `/evaluate`, `/regress` 계약 유지
- 기존 CLI 영향 없음

## Testing Strategy

- API facade 단위 테스트:
  - latest/report/eval 조회
- HTTP 통합 테스트:
  - 시뮬/평가 후 조회 엔드포인트 응답 검증
