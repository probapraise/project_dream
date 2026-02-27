# Project Dream Eval Quality V1 Design

## Goal

평가 파이프라인에 품질 지표 세트 `v1`을 추가한다.

## Scope

- `metric_set` 개념 도입 (`v1` 기본)
- `v1` 품질 지표 3개
  - `moderation_intervention_rate`
  - `gate_rewrite_rate`
  - `community_dispersion`
- CLI `evaluate --metric-set` 옵션 추가
- 결과는 `eval.json`의 `metrics` 및 `metric_set`으로 저장

## Extensibility Contract

- `METRIC_SET_REGISTRY: dict[str, callable]` 고정
- 새 지표 세트(향후 `v2`)는 레지스트리에 함수 추가만으로 연동
- 기존 `evaluate_run(run_dir, metric_set=...)` 인터페이스 유지
