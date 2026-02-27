# Project Dream Eval Regression Design

## Goal

고정 seed 실행 결과의 구조 회귀를 자동 검증하고 `eval.json`으로 저장한다.

## Scope

- `evaluate` CLI 커맨드 추가
- `eval_suite` 모듈 추가 (`evaluate_run`, `evaluate_latest_run`)
- `EvalResult` 스키마 추가
- 검증 항목
  - runlog 타입 이벤트 존재 (`round`, `gate`, `action`)
  - report schema version (`report.v1`)
  - 필수 섹션 존재 (`lens_summaries`, `highlights_top10`, `conflict_map`, `dialogue_candidates`, `risk_checks`)
  - 최소 수량 조건 (lens 4, dialogue 3~5, highlights 1~10)

## Contracts

- 출력 파일: `runs/<run_id>/eval.json`
- 고정 인터페이스: `evaluate_run(run_dir) -> EvalResult`
- 확장점: 이후 품질 지표 평가기는 같은 `EvalResult.metrics` 키를 확장
