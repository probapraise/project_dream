# Project Dream Web API HTTP Server Design

## Goal

`infra/web_api` 파사드를 실제 HTTP 엔드포인트로 노출하는 최소 서버 계층을 추가한다.

## Scope

- 표준 라이브러리(`http.server`) 기반 JSON API 서버 추가
- 엔드포인트:
  - `GET /health`
  - `POST /simulate`
  - `POST /evaluate`
- CLI에 `serve` 서브커맨드 추가

## Approach

### 1) Python stdlib HTTP server (Recommended)

- 장점: 의존성 추가 없음, 스캐폴딩 목적에 충분
- 단점: 고급 기능(자동 문서, validation, async) 제한

### 2) FastAPI 도입

- 장점: 생산성/확장성 높음
- 단점: 의존성 및 운영 복잡도 증가, 현재 스코프 대비 과함

선택: 1번.

## API Contract

### `GET /health`
- response: `{"status":"ok","service":"project-dream"}`

### `POST /simulate`
- request:
```json
{
  "seed": {
    "seed_id": "SEED-API-001",
    "title": "...",
    "summary": "...",
    "board_id": "B07",
    "zone_id": "D"
  },
  "rounds": 3
}
```
- response:
```json
{
  "run_id": "run-...",
  "run_dir": "..."
}
```

### `POST /evaluate`
- request:
```json
{
  "run_id": "run-...",
  "metric_set": "v2"
}
```
- response: `eval.v1` payload

## Error Handling

- unknown path: `404`
- invalid JSON/body: `400`
- execution exception: `500` + message

## Testing Strategy

- 로컬 ephemeral port에서 서버를 띄워 실제 HTTP 요청 테스트
- health/simulate/evaluate 엔드포인트 응답 검증
- 서버 종료 루틴 포함
