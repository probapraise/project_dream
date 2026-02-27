# Project Dream Report Quality Rules Design

## Goal

`evaluate` 단계에서 report 구조 적합성뿐 아니라 내용 품질 최소 기준을 검증한다.

## Scope

- `report.v1` 품질 규칙 4개를 추가
- 기존 `evaluate_run`의 `checks`에 품질 규칙 결과를 포함
- 품질 규칙 실패 시 `pass_fail=false` 반영

## Approaches

### 1) Evaluate 내부에 정적 규칙 함수 추가 (Recommended)

- 설명: `eval_suite.py`에 report 품질 규칙 함수(`_report_quality_checks_v1`)를 추가하고 기존 check 목록에 append
- 장점: 구현 단순, 현재 구조와 자연스럽게 결합, 테스트 작성 용이
- 단점: 규칙 수가 많아지면 파일이 비대해질 수 있음

### 2) 독립 모듈(`report_quality.py`)로 분리

- 설명: 규칙 계산을 별도 모듈에서 수행
- 장점: 책임 분리가 명확
- 단점: 현재 규모에서는 과설계, 파일 수만 증가

### 3) Metric-set별 규칙 동적 연동

- 설명: v1/v2 metric set에 따라 서로 다른 품질 규칙 세트 사용
- 장점: 장기적으로 유연
- 단점: 현재 요구보다 복잡도가 과도

선택: 1번.

## Quality Rules v1

### Rule 1: `report.conflict_map.mediation_points_count`

- 조건: `conflict_map.mediation_points` 길이 >= 1
- 의도: 최소 중재 포인트 제시 보장

### Rule 2: `report.foreshadowing_count`

- 조건: `foreshadowing` 길이 >= 1
- 의도: 후속 전개 가능성(떡밥) 보장

### Rule 3: `report.dialogue_candidate_fields`

- 조건: `dialogue_candidates`의 모든 항목에 `speaker`/`line` 비어있지 않음
- 의도: 대사 후보 품질 하한 보장

### Rule 4: `report.risk_checks.severity_values`

- 조건: 모든 `risk_checks.severity` 값이 `{low, medium, high}` 중 하나
- 의도: 리스크 심각도 표기 표준화

## Data Contract

- 기존 `EvalResult.checks` 포맷 유지 (`name`, `passed`, `details`)
- 새 규칙도 동일 포맷으로 추가
- 기존 `metrics` 필드 구조는 변경하지 않음

## Error Handling

- report 필드가 비어 있거나 누락된 경우 품질 규칙은 `passed=false`
- 예외를 던지지 않고 check 실패로 표면화

## Testing Strategy

- 정상 report에서 새 품질 체크 4개가 모두 pass 되는지 검증
- 의도적으로 `severity`를 invalid 값으로 바꿔 fail 동작 검증
- 전체 회귀 테스트 실행으로 기존 동작 보존 확인
