# Project Dream Web API Regressions List Endpoint Design

## Goal

회귀 summary 히스토리를 한 번에 조회해 비교/디버깅 속도를 높인다.

## Scope

- 저장소 메서드 추가: `list_regression_summaries(limit=None)`
- API facade 메서드 추가: `list_regression_summaries(limit=None)`
- HTTP 엔드포인트 추가: `GET /regressions`
- 쿼리 파라미터: `limit` (선택)

## Endpoint Contract

### `GET /regressions`

response:
```json
{
  "count": 2,
  "items": [
    {
      "summary_id": "regression-20260227-....json",
      "summary_path": "runs/regressions/regression-20260227-....json",
      "generated_at_utc": "2026-02-27T15:00:00+00:00",
      "metric_set": "v2",
      "pass_fail": true,
      "seed_runs": 3
    }
  ]
}
```

- 정렬: 최신 파일 우선(desc)
- `limit` 지정 시 상위 N개만 반환

## Error Handling

- `limit < 1`: `400`

## Compatibility

- 기존 `GET /regressions/latest`, `GET /regressions/{summary_id}` 유지
- 기존 run 조회/시뮬레이션/평가/회귀 계약 유지

## Testing Strategy

- API facade 테스트: 목록 조회 + limit 조회
- HTTP 통합 테스트: `GET /regressions`, `GET /regressions?limit=1`
