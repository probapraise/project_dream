# Project Dream MVP

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
python -m project_dream.cli simulate --seed examples/seeds/seed_001.json --output-dir runs --rounds 3
python -m project_dream.cli evaluate --runs-dir runs --metric-set v2
python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10
python -m project_dream.cli serve --api-token local-dev-token
# or: export PROJECT_DREAM_API_TOKEN=local-dev-token && python -m project_dream.cli serve
```

`evaluate`는 스키마 체크와 함께 report 내용 품질 체크(중재포인트/떡밥/대사필드/severity 표준값)를 함께 검증합니다.
`serve`는 `GET /health`를 제외한 모든 API 호출에 `Authorization: Bearer <token>` 헤더가 필요합니다.
`serve` 실행 중에는 요청 로그가 stderr에 JSON 라인으로 출력되며, `method/path/status/latency_ms/auth_ok/event` 필드를 포함합니다.

## CI Regression Gate

GitHub Actions(`Regression Gate`)가 PR 및 `main` push에서 `pytest`와 `regress(metric-set v2)`를 자동 실행합니다.
