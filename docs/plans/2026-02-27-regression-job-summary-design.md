# Project Dream Regression Job Summary Design

## Goal

GitHub Actions `Regression Gate` 실행 결과를 `$GITHUB_STEP_SUMMARY`에 사람이 바로 읽을 수 있는 Markdown 요약으로 기록한다.

## Scope

- 회귀 summary JSON(`runs/regressions/regression-*.json`)를 읽어 Markdown으로 변환
- workflow에서 요약 step 추가 (`if: always()`)
- 회귀 summary 파일이 없을 때도 요약 메시지 출력

## Approaches

### 1) Python 유틸 모듈 + workflow 호출 (Recommended)

- 설명: `project_dream.regression_summary` 모듈을 추가하고 workflow에서 `python -m ...`로 실행
- 장점: 테스트 가능, 유지보수 쉬움, 포맷 변경 유연
- 단점: 코드 파일 1개 추가

### 2) workflow shell inline 처리

- 설명: `cat`/`jq`/`echo`로 summary를 바로 생성
- 장점: 파일 추가 없음
- 단점: 테스트 어려움, 유지보수 취약

### 3) PR 코멘트 액션으로 대체

- 설명: 요약을 PR 댓글로 남김
- 장점: 타임라인 노출
- 단점: 1인 개발 기준 노이즈 증가, 현재 요구와 불일치

선택: 1번.

## Data Contract

입력(`regression.v1`)에서 사용 필드:
- `schema_version`
- `metric_set`
- `pass_fail`
- `totals` (`seed_runs`, `eval_pass_runs`, `unique_communities`)
- `gates` (bool dict)
- `summary_path` (선택)

출력(Markdown):
- 제목 (`Regression Gate Summary`)
- pass/fail status
- metric_set
- totals 핵심 3개
- gate별 pass/fail 리스트
- summary json 경로(있을 때)

## Error Handling

- regression summary 파일이 없으면:
  - workflow 실패로 만들지 않고 안내 메시지 출력
- summary JSON 파싱 실패 시:
  - 파싱 실패 메시지 + 예외 정보 요약 출력

## Workflow Changes

- 기존 `Run Regression Batch Gate` 단계 뒤에:
  - `Render Job Summary` step 추가 (`if: always()`)
  - `$GITHUB_STEP_SUMMARY`를 output file로 전달

## Testing Strategy

- 단위 테스트:
  - 정상 summary에서 Markdown이 핵심 필드를 포함하는지 검증
  - summary 부재 시 fallback Markdown 검증
- 통합 검증:
  - `pytest -q`
  - `regress` 실행 후 summary 렌더러 실행
