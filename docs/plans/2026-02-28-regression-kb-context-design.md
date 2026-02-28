# Project Dream Regression KB Context Design

## Goal

회귀 배치 실행(`run_regression_batch`)도 앱 시뮬레이션 경로와 동일하게 `kb_index.retrieve_context` 결과를 사용해 `corpus`를 채운다.

## Problem

- 현재 `regression_runner`는 `run_simulation(..., corpus=[])`를 고정 사용한다.
- 이로 인해 게이트/유사도/정합성 동작이 실제 운영 경로(`app_service`)와 불일치한다.

## Scope

- `regression_runner`에 `build_index`/`retrieve_context` 연동
- seed별 컨텍스트를 구성해 `run_simulation`에 전달
- 회귀 테스트 추가로 비어 있지 않은 corpus 전달을 검증

## Approach

### 1) Reuse Existing Retrieval API (Recommended)

- 설명: `app_service`와 동일한 `build_index` + `retrieve_context` 호출을 적용
- 장점: 동작 일관성 확보, 중복 최소화
- 단점: retrieve 비용이 seed 수만큼 발생

### 2) Keep Empty Corpus for Regression

- 설명: 현 상태 유지
- 장점: 실행 단순
- 단점: 실제 경로와 괴리, 회귀 품질 저하

선택: 1번.

## Testing Strategy

- `tests/test_regression_runner.py`에 신규 테스트 추가
  - seed별 `run_simulation` 호출 시 corpus가 retrieve 결과를 쓰는지 검증
  - spy/mocking으로 값 전달 계약만 확인
