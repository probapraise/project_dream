# P1-1 Cross Inflow Stage Implementation (2026-03-01)

## 1) Goal

- 교차 유입(stage) 로그를 시뮬레이션 결과와 runlog에 남기고,
- report `story_checklist.board_migration_clue`가 이를 근거로 `risk`를 표기하도록 연결한다.

---

## 2) RED (Failing Tests)

추가 테스트:

- `tests/test_phase2_simulation_context.py`
  - `test_simulation_emits_cross_inflow_stage_logs`
- `tests/test_report_v1.py`
  - `test_report_v1_story_checklist_marks_board_migration_from_cross_inflow`

실패 재현:

```bash
./.venv/bin/python -m pytest -q tests/test_phase2_simulation_context.py tests/test_report_v1.py
```

결과:

- `cross_inflow_logs`가 빈 배열
- `board_migration_clue.status == "missing"` (기대: `risk`)

---

## 3) Root Cause

- 기본 시드(`B07`) 경로에서 라운드별 `report_total=0`, `moderation_action=NO_OP`가 유지되어
  기존 교차 유입 트리거(운영개입/신고압력) 조건이 충족되지 않음.
- report 체크리스트 계산이 `rounds.thread_state`의 `board_id`만 사용하여
  `cross_inflow_logs`를 판정 근거에 반영하지 않음.

---

## 4) GREEN (Implementation)

수정 파일:

- `src/project_dream/sim_orchestrator.py`
  - `cross_inflow_logs`를 round loop stage payload/assembly에 포함
  - `_select_cross_inflow_target_board`, `_collect_cross_inflow_logs` 추가
  - 교차 유입 트리거를 운영개입/신고압력 + 라운드 유입압력(지속 POST_COMMENT)까지 확장
- `src/project_dream/storage.py`
  - runlog에 `type: "cross_inflow"` row 저장
- `src/project_dream/report_generator.py`
  - `cross_inflow_logs`를 `story_checklist.board_migration_clue` 계산에 반영
  - `details`에 `cross_inflow=<bool>`를 실제 교차 유입 여부로 표기

---

## 5) Verification

타깃:

```bash
./.venv/bin/python -m pytest -q tests/test_phase2_simulation_context.py tests/test_report_v1.py
```

- 결과: `22 passed`

전체:

```bash
./.venv/bin/python -m pytest -q
```

- 결과: `204 passed`

---

## 6) Next Stage

- P1-2로 진행:
  - 밈 반감기 모델(폭발형/주간형/제도형)
  - 보드 문화 가중치와 결합한 도달/감쇠 룰 검증
