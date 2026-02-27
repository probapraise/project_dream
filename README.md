# Project Dream MVP

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
python -m project_dream.cli simulate --seed examples/seeds/seed_001.json --output-dir runs --rounds 3
```
