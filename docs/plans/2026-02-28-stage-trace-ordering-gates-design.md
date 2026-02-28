# Project Dream Stage Trace Ordering Gates Design

## Goal

stage trace 이벤트가 존재/정합성만 맞는 것이 아니라, 실행 흐름 순서까지 올바른지 검증해 runlog 해석 가능성을 높인다.

## Scope

- `evaluate_run`에 `runlog.stage_trace_ordering` 체크 추가
- `regression_runner` summary에 `stage_trace_ordered_runs` totals/gate 추가
- `storage.persist_run`의 runlog 직렬화 순서를 실행 흐름 기준으로 정렬
- 관련 테스트 보강
  - `tests/test_eval_suite.py`
  - `tests/test_regression_runner.py`

## Approach

### 1) Ordering 체크 + 저장 순서 정렬 (Recommended)

- ordering 규칙
  - `context`, `thread_candidate`, `thread_selected`는 `round` 이전
  - `round/gate/action` 블록 이후 `round_summary`
  - `round_summary` 이후 `moderation_decision`
  - 마지막에 `end_condition`
- 장점: runlog를 시간축으로 그대로 읽을 수 있음
- 단점: 기존 fixture 순서 일부 조정 필요

### 2) 체크만 추가하고 저장 순서는 유지

- 장점: 저장 코드 변경 최소화
- 단점: 실제 생성 runlog가 ordering 체크를 통과하지 못해 운영 이득이 낮음

선택: 1번.

## Contracts

- Eval check: `runlog.stage_trace_ordering`
- Regression totals: `stage_trace_ordered_runs`
- Regression gate: `stage_trace_ordered_runs == seed_runs`
