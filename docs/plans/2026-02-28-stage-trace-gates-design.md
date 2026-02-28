# Project Dream Stage Trace Gates Design

## Goal

시뮬레이션 단계 이벤트(trace)가 누락되면 평가/회귀에서 즉시 감지되도록 `eval_suite`와 `regression_runner` 게이트를 강화한다.

## Scope

- `evaluate_run`에 `runlog.stage_trace_present` 체크 추가
- `regression_runner` summary에 `stage_trace_runs` totals/gate 추가
- 관련 테스트 보강
  - `tests/test_eval_suite.py`
  - `tests/test_eval_quality_metrics.py`
  - `tests/test_eval_report_quality_rules.py`
  - `tests/test_regression_runner.py`

## Approach

### 1) Eval check 기반 재사용 (Recommended)

- 설명: stage trace 판정은 `evaluate_run`이 단일 책임으로 수행하고, 회귀 러너는 해당 체크를 집계
- 장점: 규칙 원천이 하나라서 CLI/Web/API/Regression에 일관 적용
- 단점: 체크 이름 변경 시 러너도 함께 수정 필요

### 2) Regression에서 runlog 직접 파싱

- 설명: 회귀 러너가 매 runlog를 직접 읽어 stage 이벤트 확인
- 장점: eval 의존성 축소
- 단점: 파싱/규칙 중복으로 관리 비용 증가

선택: 1번.

## Contracts

- Eval check name: `runlog.stage_trace_present`
- Required stage event types:
  - `thread_candidate`
  - `thread_selected`
  - `round_summary`
  - `moderation_decision`
  - `end_condition`
- Regression totals: `stage_trace_runs`
- Regression gate: `stage_trace_runs == seed_runs`
