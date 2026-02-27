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
```

`evaluate`는 스키마 체크와 함께 report 내용 품질 체크(중재포인트/떡밥/대사필드/severity 표준값)를 함께 검증합니다.
