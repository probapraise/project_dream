# Project Dream Stage Trace Consistency Gates Design

## Goal

stage trace 이벤트의 "존재"뿐 아니라 "정합성"까지 검증해, 라운드 수/요약 수/운영 판단 수 불일치가 발생하면 평가 및 회귀에서 즉시 실패하도록 한다.

## Scope

- `evaluate_run`에 `runlog.stage_trace_consistency` 체크 추가
- `regression_runner` summary에 `stage_trace_consistent_runs` totals/gate 추가
- 관련 테스트 보강
  - `tests/test_eval_suite.py`
  - `tests/test_regression_runner.py`

## Approach

### 1) Eval 체크 기반 정합성 판정 (Recommended)

- 설명: eval이 runlog 전반 정합성을 판단하고, 회귀 러너는 체크 결과를 집계
- 검증 규칙:
  - `end_condition`은 정확히 1개
  - `ended_round` > 0
  - `ended_round == 실제 round id 개수`
  - `round ids == round_summary ids == moderation_decision ids`
- 장점: 단일 판정 기준 유지
- 단점: 체크 규칙 변경 시 회귀 집계 키도 동기화 필요

### 2) 회귀 러너 개별 파싱

- 설명: 회귀 러너가 runlog를 다시 읽어 별도 정합성 판단
- 장점: eval 의존도 감소
- 단점: 규칙 중복으로 관리 비용 증가

선택: 1번.

## Contracts

- Eval check: `runlog.stage_trace_consistency`
- Regression totals: `stage_trace_consistent_runs`
- Regression gate: `stage_trace_consistent_runs == seed_runs`
