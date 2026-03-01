# P1-9 Regression Job Summary Inline Failure Brief (2026-03-01)

## 1) Goal

- `job-summary.md` 상단에 `regress-live-diff.md`의 핵심 실패 항목을 인라인 표시한다.
- summary 문서 하나만으로 PASS/FAIL 상태와 핵심 실패 원인을 빠르게 파악 가능하게 한다.

---

## 2) RED

추가 테스트:

- `tests/test_regression_summary.py`
  - `render_summary_markdown`이 `regress_live_diff_brief` 입력을 받으면
    `### Regress-Live Diff Brief` 섹션을 렌더링하는지 검증
  - `write_job_summary`가 실제 diff 파일(`### Failures`)을 읽어 brief를 자동 주입하는지 검증

실패 확인:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py
```

결과: brief 섹션이 없어 실패.

---

## 3) GREEN

수정 파일:

- `src/project_dream/regression_summary.py`
  - `extract_regress_live_diff_brief(markdown)` 추가
    - diff markdown에서 `status`와 `Failures` 목록을 파싱
    - 최대 3개 실패 항목 추출
  - `render_summary_markdown` 확장
    - `regress_live_diff_brief`가 있으면 상단에 brief 섹션 렌더링
  - `write_job_summary` 확장
    - diff 파일 존재 시 brief를 자동 파싱하여 summary payload에 주입
- `tests/test_regression_summary.py`
  - 렌더링/자동 주입 검증 테스트 추가

---

## 4) Verification

타깃:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py
```

- 결과: `7 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py tests/test_cli_regress_live.py tests/test_cli_smoke.py
```

- 결과: `27 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `225 passed`

---

## 5) Impact

- `job-summary.md`에서 회귀 게이트 결과와 regress-live 실패 요지를 한 번에 확인할 수 있다.
- diff 원문 링크는 유지되므로 상세 분석 경로도 그대로 보장된다.
