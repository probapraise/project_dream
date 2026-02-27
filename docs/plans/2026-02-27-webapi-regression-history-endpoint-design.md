# Project Dream Web API Regression History Endpoint Design

## Goal

회귀 실행 결과를 파일 ID 기준으로 직접 조회해 비교/디버깅 편의성을 높인다.

## Scope

- 저장소 메서드 추가: `load_regression_summary(summary_id)`
- API facade 메서드 추가: `get_regression_summary(summary_id)`
- HTTP 엔드포인트 추가: `GET /regressions/{summary_id}`

## Endpoint Contract

### `GET /regressions/{summary_id}`

- `summary_id`는 `regression-...json` 파일명 또는 `.json` 제거한 stem 허용

response:
```json
{
  "schema_version": "regression.v1",
  "metric_set": "v2",
  "pass_fail": true,
  "totals": {"seed_runs": 3},
  "gates": {"format_missing_zero": true},
  "runs": [],
  "summary_path": "runs/regressions/regression-....json"
}
```

## Error Handling

- summary 파일 미존재: `404`
- path 구분자 포함 등 잘못된 ID: `400`

## Compatibility

- 기존 `GET /regressions/latest` 유지
- 기존 `POST /regress`, `GET /runs/*` 계약 유지
- CLI 변경 없음

## Testing Strategy

- API facade 테스트에 filename/stem 조회 케이스 추가
- HTTP 통합 테스트에 `GET /regressions/{summary_id}` 추가
