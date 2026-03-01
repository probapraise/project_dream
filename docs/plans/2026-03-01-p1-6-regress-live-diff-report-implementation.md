# P1-6 Regress-Live Diff Report Automation (2026-03-01)

## 1) Goal

- `regress-live` 실행 시 baseline 비교 결과를 markdown으로 자동 산출한다.
- PASS/FAIL/비교스킵(SKIPPED) 상태를 사람이 바로 확인 가능하게 한다.

---

## 2) RED

추가 테스트:

- `tests/test_cli_smoke.py`
  - `regress-live` 기본 옵션에 `--diff-output-file` 존재 확인
- `tests/test_cli_regress_live.py`
  - baseline 비교 FAIL 시 diff markdown 생성/상태 표시 확인
  - baseline 비교 PASS 시 diff markdown 생성/지표 포함 확인

실패 확인:

```bash
./.venv/bin/pytest -q tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

결과: `--diff-output-file` 미지원 및 diff 파일 미생성으로 실패.

---

## 3) GREEN

수정 파일:

- `src/project_dream/cli.py`
  - 옵션 추가:
    - `regress-live --diff-output-file` (default: `runs/regressions/regress-live-diff.md`)
  - 신규 함수:
    - `_render_regress_live_diff_markdown(...)`
    - `_write_regress_live_diff(...)`
    - metric 포맷/키 정렬 helper
  - 동작:
    - baseline 없음 -> `SKIPPED` diff markdown 생성
    - baseline 있음 + 비교 수행 -> PASS/FAIL diff markdown 생성
    - stderr에 diff 파일 경로 출력

---

## 4) Verification

타깃:

```bash
./.venv/bin/pytest -q tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

- 결과: `20 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_regression_runner.py tests/test_regression_summary.py tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

- 결과: `31 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `221 passed`

---

## 5) Impact

- 회귀 품질 저하 판단 근거가 로그(stderr)뿐 아니라 파일(`regress-live-diff.md`)로 축적된다.
- baseline 재생성 없이도 현재 실행의 비교 상세(delta/failures)를 즉시 확인 가능하다.
