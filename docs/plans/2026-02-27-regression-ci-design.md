# Project Dream Regression CI Design

## Goal

GitHub Actions에서 `pytest`와 `regress`를 자동 실행해 PR 단계에서 회귀 품질 게이트를 강제한다.

## Scope

- 신규 workflow: `.github/workflows/regression-gate.yml`
- 트리거: `pull_request`, `push` (`main`)
- 실행 순서:
  1) Python 환경 구성
  2) 의존성 설치
  3) `pytest -q`
  4) `project_dream.cli regress` 실행(`metric-set v2`)
  5) 회귀 summary artifact 업로드

## Why This Approach

- 로컬에서 이미 검증한 흐름을 CI에 그대로 재사용 가능
- gate 실패 시 PR 상태 체크에서 즉시 차단 가능
- run artifact를 남겨 디버깅 비용 감소

## Workflow Contract

- 회귀 명령은 non-zero 종료 시 job 실패로 처리
- 기본 커맨드:
  - `python -m pytest -q`
  - `python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10 --metric-set v2`
- artifact 대상:
  - `runs/regressions/*.json`
  - `runs/run-*/eval.json`
  - `runs/run-*/report.json`

## Non-Goals

- 병렬 분산 실행 최적화
- flaky seed 자동 재시도
- 코멘트 봇/Slack 연동

## Extensibility

- 향후 `workflow_dispatch`(수동 실행) 추가 가능
- matrix 도입 시 Python 버전/metric-set 확장 가능
- artifact에 `report.md`/`runlog.jsonl` 추가 가능
