# P1 Closeout Check (2026-02-28)

## 1) Scope checked

- `P1-5` Pack schema strict validation (Pydantic)
- `P1-6` KB hybrid retrieval (sparse + dense + hybrid score)
- `P1-7` Report post-generation gate
- `P1-8` External eval export (promptfoo/ragas/tracing-ready)

## 2) Completion status

- `P1-5`: done
  - strict schema validation layer + `extra=forbid` + type enforcement
  - evidence: `docs/plans/2026-02-28-pack-schema-strict-validation-handoff.md`
- `P1-6`: done
  - `score_sparse/score_dense/score_hybrid` 도입
  - evidence: `docs/plans/2026-02-28-kb-hybrid-retrieval-handoff.md`
- `P1-7`: done
  - report payload에 `report_gate.v1` 포함, regression gate 집계 반영
  - evidence: `docs/plans/2026-02-28-report-gate-handoff.md`
- `P1-8`: done
  - `eval-export` CLI 및 external eval bundle 산출물 도입
  - evidence: `docs/plans/2026-02-28-external-eval-export-handoff.md`

## 3) Verification snapshot

- command:
  - `./.venv/bin/python -m pytest -q`
- result:
  - `130 passed`

## 4) Remaining backlog after P1

- `P2-9`: 파일 저장소 외 DB/벡터DB 계층 도입
- `P2-10`: LangGraph 오케스트레이션 도입

## 5) Recommended next step

- `P2-9`부터 시작:
  - 파일 저장소 계약 유지 + SQLite repository 추가(옵션형)
  - 이후 `RunRepository` 선택을 CLI/API에서 토글 가능하게 확장.
