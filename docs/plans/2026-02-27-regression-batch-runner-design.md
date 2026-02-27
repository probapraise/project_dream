# Project Dream Regression Batch Runner Design

## Goal

10개 시드를 자동 실행해 회귀 품질을 한 번에 점검하는 `regress` 배치 러너를 추가한다.

## Why Now

- 현재 `simulate`/`evaluate`는 단일 run 중심이라 변경 시 회귀 리스크를 빠르게 파악하기 어렵다.
- 다음 단계(quality metric-set v2, report 품질 고도화) 전에 자동 안전망이 필요하다.

## Approaches Considered

### 1) New CLI Command `regress` (Recommended)

- 설명: `simulate` + `evaluate`를 내부 함수로 호출해 여러 seed를 배치 실행한다.
- 장점: 기존 명령과 계약을 깨지 않고 확장 가능, CI 연동 쉬움, 단일 summary 산출 가능.
- 단점: 새 모듈/CLI 분기 추가 필요.

### 2) External Shell/Python Script

- 설명: CLI를 서브프로세스로 반복 호출하는 스크립트 추가.
- 장점: 본 코드 변경 최소.
- 단점: 출력 파싱 취약, 테스트/재사용성 낮음, 유지보수 비용 증가.

### 3) Extend `evaluate` with batch mode

- 설명: `evaluate`에 seed/simulate 책임까지 혼합한다.
- 장점: 명령 수를 줄일 수 있음.
- 단점: 커맨드 책임이 섞여 복잡도 증가, 향후 v2/v3 확장 시 분리 난이도 상승.

선택: 1번(`regress`) 확정.

## Scope

- `project-dream regress` 명령 추가
- seed 디렉토리에서 최대 N개 seed(기본 10) 자동 실행
- run별 `report.json`, `eval.json` 생성
- 배치 summary JSON 생성 + pass/fail 게이트 판정

## Non-Goals

- 병렬 실행/멀티프로세싱
- 외부 DB 저장
- metric-set v2 구현

## Architecture

- 신규 모듈 `regression_runner.py`에서 배치 오케스트레이션 담당
- CLI는 인자 파싱과 결과 exit code 결정만 담당
- 기존 `run_simulation`, `build_report_v1`, `evaluate_run`, `persist_run`, `persist_eval` 재사용

## Data Flow

1. seeds 디렉토리에서 `*.json` 파일 정렬 후 최대 `max_seeds` 선택
2. 각 seed에 대해 시뮬레이션 실행
3. run 디렉토리에 runlog/report 저장
4. 해당 run 평가(`metric_set`) 후 eval 저장
5. run별 요약 누적 후 배치 요약 생성
6. `runs/regressions/regression-*.json`에 summary 저장

## Regression Gates (v1)

- `format_missing_zero`:
  - 모든 run의 report 필수 섹션 누락 합계가 0
- `community_coverage`:
  - 전체 배치에서 관측된 고유 community 수가 최소 2
- `conflict_frame_runs`:
  - `conflict_map.claim_a`/`claim_b`가 모두 존재하는 run 수가 최소 2
- `moderation_hook_runs`:
  - 운영 개입(action) + 떡밥(foreshadowing) 동시 충족 run 수가 최소 1
- `validation_warning_runs`:
  - `risk_checks`가 기록된 run 수가 최소 1

기본 임계치:
- `min_community_coverage=2`
- `min_conflict_frame_runs=2`
- `min_moderation_hook_runs=1`
- `min_validation_warning_runs=1`

## Extensibility Contract

- summary에 `schema_version: regression.v1`와 `metric_set` 명시
- 임계치는 CLI 옵션으로 주입 가능하게 설계
- 향후 metric-set v2는 evaluate 경로 재사용만으로 자동 적용
- 향후 병렬화는 `run_regression_batch` 내부 루프 교체로 국소 변경 가능

## Error Handling

- seed 파일이 없으면 `FileNotFoundError`
- seed 파싱 실패는 즉시 예외 처리(입력 품질 문제를 조기 노출)
- CLI는 회귀 게이트 실패 시 non-zero exit

## Testing Strategy

- 단위 테스트:
  - 배치 summary에 게이트/카운트가 기대대로 반영되는지
  - seed 부족/미존재 처리
- CLI E2E:
  - `regress` 실행 후 summary 파일 생성 확인
  - pass/fail에 따른 종료 코드 확인
