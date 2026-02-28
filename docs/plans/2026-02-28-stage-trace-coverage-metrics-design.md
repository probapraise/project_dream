# Project Dream Stage Trace Coverage Metrics Design

## Goal

stage trace 품질을 binary pass/fail 외에 연속 지표로 관측하기 위해 `stage_trace_coverage_rate`를 eval/regression에 추가한다.

## Scope

- `evaluate_run.metrics`에 `stage_trace_coverage_rate` 추가
- `regression_runner`에 평균 지표 `avg_stage_trace_coverage_rate` 집계
- `regression_runner` gates에 `stage_trace_coverage_rate` 추가
- 관련 테스트 보강
  - `tests/test_eval_suite.py`
  - `tests/test_eval_quality_metrics.py`
  - `tests/test_regression_runner.py`

## Approach

### 1) 규칙 기반 coverage 산출 (Recommended)

- 구성요소 5개를 동일 가중치로 계산
  - `thread_candidate` 존재
  - `thread_selected` 존재
  - `end_condition` 존재
  - `round_summary` 라운드 coverage
  - `moderation_decision` 라운드 coverage
- 라운드 coverage는 `min(actual, expected)/expected` (expected는 `ended_round` 우선)
- 장점: missing/partial 상태를 수치로 파악 가능
- 단점: 가중치가 단순(동일 비중)

### 2) 이벤트 행 수 기반 coverage

- 장점: 계산 단순
- 단점: 이벤트 과다 발생 시 왜곡 가능

선택: 1번.

## Contracts

- Eval metric: `stage_trace_coverage_rate` (0.0~1.0)
- Regression totals: `avg_stage_trace_coverage_rate`
- Regression gate: `stage_trace_coverage_rate` (`avg_stage_trace_coverage_rate >= 1.0`)
