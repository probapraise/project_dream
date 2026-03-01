# P1-3 Board Culture Dial Interaction Implementation (2026-03-01)

## 1) Goal

- 보드별 문화(`board.emotion`)와 다이얼 축(`U/E/M/S/H`) 상호작용을 점수 계산에 반영한다.
- 시뮬레이션 round row에 문화 가중치 추적 필드를 기록한다.
- eval(v2)에서 문화-다이얼 정렬 지표를 노출한다.

---

## 2) RED

추가 테스트:

- `tests/test_env_engine.py`
  - `test_board_emotion_and_dial_interaction_affect_score`
- `tests/test_phase2_simulation_context.py`
  - `test_simulation_applies_board_culture_weight_by_dial_axis`
- `tests/test_eval_quality_metrics.py`
  - v2 metric에 문화 지표 키 포함 검증

RED 확인:

```bash
./.venv/bin/python -m pytest -q tests/test_env_engine.py tests/test_phase2_simulation_context.py tests/test_eval_quality_metrics.py
```

실패 원인:

- `compute_score`가 `board_emotion`, `dial_dominant_axis`를 받지 않음
- round row에 `board_emotion`, `culture_weight_multiplier` 필드가 없음
- eval(v2)에 문화 지표가 없음

---

## 3) GREEN

수정 파일:

- `src/project_dream/env_engine.py`
  - 문화 프로필 매핑(`emotion -> social/order/conflict`)
  - 프로필별 축 가중치 테이블 추가
  - `compute_culture_weight()` 추가
  - `compute_score()`에 `board_emotion`, `dial_dominant_axis` 옵션 인자 추가
- `src/project_dream/sim_orchestrator.py`
  - 보드 감정 조회 및 문화 가중치 계산 연결
  - 정책 전이 점수 계산 시 문화 가중치 반영
  - round row / thread_state에 `board_emotion`, `culture_weight_multiplier` 기록
- `src/project_dream/eval_suite.py`
  - v2 metrics 확장:
    - `culture_dial_alignment_rate`
    - `culture_weight_avg`

---

## 4) Verification

타깃:

```bash
./.venv/bin/python -m pytest -q tests/test_env_engine.py tests/test_phase2_simulation_context.py tests/test_eval_quality_metrics.py
```

- 결과: `26 passed`

전체:

```bash
./.venv/bin/python -m pytest -q
```

- 결과: `209 passed`

---

## 5) Next Stage

- P1-4 후보:
  - 페르소나 레지스터 스위치(트리거 -> 전환) 데이터화
  - regress-live baseline diff에 문화/밈/교차유입 요약 자동 포함
