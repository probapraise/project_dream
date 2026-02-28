# External Eval Stack Export Handoff (2026-02-28)

## 1) Done in this session

- Target: `P1-8 외부 평가 스택(promptfoo/ragas/tracing) 연동`
- Implemented:
  - 신규 `eval_export` 모듈 추가
    - `export_external_eval_bundle(run_dir, output_dir=None, max_contexts=5)`
    - outputs:
      - `promptfoo_cases.jsonl`
      - `ragas_samples.jsonl`
      - `trace_events.jsonl`
      - `manifest.json` (`external_eval_export.v1`)
  - CLI 명령 추가:
    - `project-dream eval-export --runs-dir ... --run-id ... --output-dir ... --max-contexts ...`
  - parser/smoke/e2e/unit 테스트 추가

## 2) Files changed

- `src/project_dream/eval_export.py` (new)
- `src/project_dream/cli.py`
- `tests/test_eval_export.py` (new)
- `tests/test_cli_eval_export_e2e.py` (new)
- `tests/test_cli_smoke.py`

## 3) Verification

- Targeted:
  - `pytest tests/test_eval_export.py tests/test_cli_eval_export_e2e.py tests/test_cli_smoke.py tests/test_cli_evaluate_e2e.py -q`
  - result: `10 passed`
- Integration:
  - `pytest tests/test_eval_export.py tests/test_eval_suite.py tests/test_web_api.py tests/test_regression_runner.py -q`
  - result: `21 passed`
- Full:
  - `pytest -q`
  - result: `130 passed`

## 4) Usage

```bash
./.venv/bin/python -m project_dream.cli eval-export --runs-dir runs
./.venv/bin/python -m project_dream.cli eval-export --runs-dir runs --run-id <run_id> --output-dir runs/exports/<run_id>
```

## 5) Next recommended step

- P1 마감 정리:
  - `P1-5/6/7/8` 구현 상태를 하나의 progress 문서로 통합
  - 이후 `P2`(저장소/오케스트레이션)로 전환할지, 현재 브랜치 머지 후 안정화할지 결정.
