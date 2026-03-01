# P1-5 Regress-Live Baseline Diff Hardening (2026-03-01)

## 1) Goal

- `regress-live` 기준선 비교를 P1 후속 기능(교차유입/밈흐름/문화-다이얼)까지 확장한다.
- 회귀 요약(`regression.v1`)과 CI 요약 markdown에서 신규 지표를 같은 계약으로 노출한다.

---

## 2) RED

추가/강화 테스트:

- `tests/test_regression_runner.py`
  - totals에 신규 지표 키 존재/범위 검증
- `tests/test_cli_regress_live.py`
  - baseline 파일에 신규 지표 기록 검증
  - `cross_inflow_rate` 저하 시 non-zero 종료 검증
- `tests/test_regression_summary.py`
  - markdown totals에 신규 지표 노출 검증

RED 확인:

```bash
./.venv/bin/pytest -q tests/test_regression_runner.py tests/test_cli_regress_live.py tests/test_regression_summary.py
```

결과: 4개 실패 (`cross_inflow_rate`, `meme_flow_rate`, `avg_culture_*` 미노출)

---

## 3) GREEN

수정 파일:

- `src/project_dream/regression_runner.py`
  - 신규 집계 추가:
    - `cross_inflow_runs/events/rate`
    - `meme_flow_runs/events/rate`
    - `avg_culture_dial_alignment_rate`
    - `avg_culture_weight`
  - run 단위 요약에도 관련 필드 추가
  - `metric_set=v1`에서도 동작하도록 culture 지표 fallback 계산(round row 기반)
- `src/project_dream/cli.py`
  - `_build_regress_live_metrics`에 신규 지표 포함
  - `_compare_regress_live_baseline` rate 비교 키 확장
- `src/project_dream/regression_summary.py`
  - markdown totals에 신규 지표 라인 추가

---

## 4) Verification

타깃:

```bash
./.venv/bin/pytest -q tests/test_regression_runner.py tests/test_cli_regress_live.py tests/test_regression_summary.py
```

- 결과: `17 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_cli_smoke.py tests/test_regression_summary.py tests/test_regression_runner.py tests/test_cli_regress_live.py
```

- 결과: `30 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `220 passed`

---

## 5) Impact

- `regress-live` baseline 비교가 P1 핵심 동작(교차유입/밈흐름/문화 정렬) 저하를 더 빨리 탐지한다.
- 지표가 regression JSON, baseline JSON, markdown 요약에서 동일 키로 유지되어 운영/자동화 연결이 단순해진다.
