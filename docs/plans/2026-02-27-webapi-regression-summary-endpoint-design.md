# Project Dream Web API Regression Summary Endpoint Design

## Goal

회귀 실행 결과를 최신 summary 파일 기준으로 즉시 조회할 수 있게 한다.

## Scope

- 저장소 메서드 추가: `load_latest_regression_summary()`
- API facade 메서드 추가: `latest_regression_summary()`
- HTTP 엔드포인트 추가: `GET /regressions/latest`

## Endpoint Contract

### `GET /regressions/latest`

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

## Compatibility

- 기존 `POST /regress` 계약 유지
- 기존 run read endpoint(`runs/*`)와 독립
- CLI 변경 없음

## Testing Strategy

- API facade 테스트에 최신 회귀 summary 조회 케이스 추가
- HTTP 통합 테스트에 `GET /regressions/latest` 케이스 추가
