# P1-8 Regress-Live Stderr Brief Summary (2026-03-01)

## 1) Goal

- `regress-live` 비교 실행 시 stderr에 핵심 3~5줄 요약을 자동 출력한다.
- 파일(`regress-live-diff.md`)을 열기 전에도 PASS/FAIL과 핵심 변화량을 빠르게 확인할 수 있게 한다.

---

## 2) RED

추가 테스트:

- `tests/test_cli_regress_live.py`
  - FAIL 비교 시 stderr에 `diff status: FAIL`, `top failure` 출력 검증
  - PASS 비교 시 stderr에 핵심 지표 3개 출력 검증

실패 확인:

```bash
./.venv/bin/pytest -q tests/test_cli_regress_live.py
```

결과: status/요약 라인 미출력으로 실패.

---

## 3) GREEN

수정 파일:

- `src/project_dream/cli.py`
  - `_emit_regress_live_brief_summary(...)` 추가
  - 출력 내용:
    - `diff status` (`PASS`/`FAIL`/`SKIPPED`)
    - 핵심 지표 3개:
      - `eval_pass_rate`
      - `cross_inflow_rate`
      - `avg_culture_weight`
    - 실패 시 `top failure` 1줄
  - baseline 없음(SKIPPED), 비교 PASS/FAIL 공통으로 요약 출력 연결
- `tests/test_cli_regress_live.py`
  - stderr 캡처 기반 검증 추가

---

## 4) Verification

타깃:

```bash
./.venv/bin/pytest -q tests/test_cli_regress_live.py
```

- 결과: `7 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_cli_regress_live.py tests/test_cli_smoke.py tests/test_regression_summary.py
```

- 결과: `25 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `223 passed`

---

## 5) Impact

- `regress-live` 결과를 터미널에서 즉시 판독할 수 있어 운영 피드백 루프가 짧아진다.
- 기존 diff markdown 산출/판정 로직은 유지되어 회귀 리스크가 낮다.
