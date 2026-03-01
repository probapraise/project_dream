# P1-7 Regression Job Summary Diff Link Integration (2026-03-01)

## 1) Goal

- `project_dream.regression_summary`가 생성하는 `job-summary.md`에
  `regress-live-diff.md` 링크를 자동 노출한다.
- 로컬/CI에서 회귀 요약 문서 하나만 열어도 baseline diff 위치를 바로 확인 가능하게 한다.

---

## 2) RED

추가 테스트:

- `tests/test_regression_summary.py`
  - `render_summary_markdown`이 `regress_live_diff_path`를 포함하면 링크 라인을 출력하는지 검증
  - `write_job_summary`가 `runs/regressions/regress-live-diff.md` 파일 존재 시 자동 링크를 추가하는지 검증

실패 확인:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py
```

결과: diff 경로 라인 미출력으로 실패.

---

## 3) GREEN

수정 파일:

- `src/project_dream/regression_summary.py`
  - `find_regress_live_diff(regressions_dir)` 추가
  - `render_summary_markdown`에 `regress_live_diff_path` 출력 추가
  - `write_job_summary`에서 diff 파일 존재 시 summary payload에 경로 주입
- `tests/test_regression_summary.py`
  - 위 동작 검증 테스트 추가

---

## 4) Verification

타깃:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

- 결과: `25 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_regression_runner.py tests/test_regression_summary.py tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

- 결과: `33 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `223 passed`

---

## 5) Impact

- `job-summary.md`가 regression gate 상태 + regress-live diff 파일 경로를 함께 담게 되어 점검 동선이 짧아진다.
- diff 파일이 없을 때는 기존 출력과 동일하게 동작해 회귀 리스크가 낮다.
