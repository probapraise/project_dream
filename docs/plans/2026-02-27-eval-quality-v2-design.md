# Project Dream Eval Quality V2 Design

## Goal

`metric_set=v2`를 도입해, 기존 `v1` 지표를 유지하면서 품질 관찰 범위를 확장한다.

## Selected Approach

`v1 + 신규 지표 3개` 방식으로 진행한다.

- 기존 지표(`moderation_intervention_rate`, `gate_rewrite_rate`, `community_dispersion`)는 그대로 유지
- 신규 지표 3개를 추가해 분석 밀도를 높임
- `evaluate_run(..., metric_set="v2")`로 선택 가능

## Why This Approach

- 기존 운영 흐름을 깨지 않음(완전 하위호환)
- 빠르게 도입 가능하고 리스크가 낮음
- 이후 `v3` 또는 점수형 지표(가중치 모델)로 확장하기 쉬움

## V2 Metrics

### 1) `lore_pass_rate`

- 정의: lore gate 통과 비율
- 계산: `passed_lore / total_lore`
- 범위: `[0, 1]`

### 2) `moderation_escalation_depth`

- 정의: 운영 조치의 최대 단계 깊이(visible 기준 상대 깊이)
- 단계 매핑:
  - `HIDE_PREVIEW` = 0.25
  - `LOCK_THREAD` = 0.5
  - `GHOST_THREAD` = 0.75
  - `SANCTION_USER` = 1.0
- 범위: `[0, 1]`

### 3) `dialogue_speaker_diversity`

- 정의: dialogue 후보 발화자 다양성
- 계산: `unique_speakers / dialogue_count`
- 범위: `[0, 1]`

## Extensibility Contract

- `METRIC_SET_REGISTRY` 키 기반 확장 유지
- v2는 내부적으로 `v1` 계산을 재사용해 중복을 방지
- 기존 CLI 옵션/인터페이스 변경 없음 (`--metric-set` 재사용)

## Testing Strategy

- `metric_set=v2` 결과에 v1+v2 지표가 모두 포함되는지 검증
- v2 신규 지표가 모두 `[0,1]` 범위인지 검증
- 기존 v1 테스트/CLI 회귀가 깨지지 않는지 전체 테스트로 확인
