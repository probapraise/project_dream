# Gate Pipeline Rule Consistency Handoff (2026-02-28)

## 1) Done in this session

- Target: `P0-3 Gate pipeline 고도화`
- Implemented in `run_gates`:
  - gate별 `violations` 상세 리포트 추가
  - 위반 레코드에 `rule_id`, `code`, `message`, `severity`, `entity_refs` 포함
  - 결과 상단에 전체 집계 `violations` 추가
  - lore gate에 consistency checker 추가
    - 상충 표현(예: `확정` + `추정`) 탐지
    - `RULE-PLZ-LORE-02` 위반 기록
  - 증거 기준 누락 시 `RULE-PLZ-LORE-01` 위반 기록
  - safety 위반을 룰 ID로 분리
    - `RULE-PLZ-SAFE-01` (전화번호)
    - `RULE-PLZ-SAFE-02` (금칙어)
  - similarity 임계치 초과 시
    - `RULE-PLZ-SIM-01` 위반 기록

## 2) Files changed

- `src/project_dream/gate_pipeline.py`
- `tests/test_gate_pipeline_hardening.py`

## 3) Root-cause note

- 기존 lore 통과/실패는 evidence 키워드 기준만 보던 구조라, 상충 주장(확정/추정 동시 진술)이 누락되던 문제가 있었음.
- consistency checker를 lore gate에 병합해 정합성 위반을 별도 룰 ID로 기록하도록 보강.

## 4) Verification

- Targeted:
  - `pytest tests/test_gate_pipeline.py tests/test_gate_pipeline_hardening.py -q`
  - result: `8 passed`
- Full:
  - `pytest -q`
  - result: `116 passed`

## 5) Next recommended step

- `P0-4 Template/Flow 상세 스키마 실행 반영`
  - `title_patterns`, `body_sections`, `trigger_tags`, `taboos`, `escalation_rules`
  - 최소 적용부터(읽기 -> prompt/render 반영 -> 상태 전이 훅 연결) TDD로 진행.

