# Project Dream Context Trace Gates Design

## Goal

`runlog`의 context 추적을 평가 및 회귀 게이트에 포함해, KB 컨텍스트 경로가 깨지면 즉시 실패하도록 만든다.

## Scope

- `evaluate_run`에 `runlog.context_trace_present` 체크 추가
- `regression_runner` summary에 `context_trace_runs` totals/gate 추가
- 관련 테스트 보강
  - `tests/test_eval_suite.py`
  - `tests/test_regression_runner.py`

## Approach

### 1) Eval Check + Regression Gate (Recommended)

- 설명: 평가 결과의 체크 항목을 회귀 집계가 참조해 context trace 보장
- 장점: 단일 기준(`evaluate_run`) 재사용, 회귀/CLI/WebAPI 모두 동일 규칙 적용
- 단점: 체크 이름 변경 시 회귀 코드 동반 수정 필요

### 2) Regression에서 runlog 직접 파싱

- 설명: 회귀 러너가 각 runlog를 직접 읽어 context row를 확인
- 장점: eval 의존성 축소
- 단점: 파싱 중복 및 기준 이원화

선택: 1번.

## Contracts

- Eval check name: `runlog.context_trace_present`
- Eval details: `context_rows=<count>`
- Regression totals: `context_trace_runs`
- Regression gate: `context_trace_runs == seed_runs`
