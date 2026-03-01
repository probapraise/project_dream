# P1-10 Regression Job Summary TL;DR Line (2026-03-01)

## 1) Goal

- CI `GITHUB_STEP_SUMMARY`에 한 줄로 읽히는 regress-live 결과 TL;DR을 추가한다.
- 사용자는 summary를 열자마자 `상태 + 대표 실패 원인`을 즉시 파악할 수 있어야 한다.

---

## 2) RED

추가 테스트:

- `tests/test_regression_summary.py`
  - `regress_live_diff_brief`가 있을 때
    `- regress_live_tldr: \`<STATUS> | <top failure>\`` 라인 출력 검증
  - `write_job_summary` 경로에서도 동일 라인 출력 검증

실패 확인:

```bash
./.venv/bin/pytest -q tests/test_regression_summary.py
```

결과: TL;DR 라인이 없어 실패.

---

## 3) GREEN

수정 파일:

- `src/project_dream/regression_summary.py`
  - `build_regress_live_tldr(brief)` 추가
    - 포맷: `STATUS | first_failure`
    - 실패 항목이 없으면 `STATUS | none`
  - `render_summary_markdown`의 `Regress-Live Diff Brief` 섹션 상단에
    `regress_live_tldr` 한 줄 출력
- `tests/test_regression_summary.py`
  - TL;DR 라인 기대값 추가

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

- GitHub summary 상단에서 회귀 상태를 한 줄로 즉시 파악 가능하다.
- 상세 실패 목록/원문 diff 링크는 유지되어 진단 흐름을 해치지 않는다.
