# P1-2 Meme Half-Life Model Implementation (2026-03-01)

## 1) Goal

- 밈 확산 모델을 시뮬레이션에 최소 구현한다.
- 경로: `허브 보드 -> 밈공장 -> 역류(backflow)`.
- 반감기 프로필: `explosive`, `weekly`, `institutional`.

---

## 2) RED

추가 테스트:

- `tests/test_phase2_simulation_context.py`
  - `test_simulation_emits_meme_flow_logs_with_hub_factory_backflow`
  - `test_simulation_selects_meme_decay_profile_by_dominant_axis`
- `tests/test_infra_store.py`
  - `test_file_run_repository_persists_meme_flow_rows_when_present`

실패 확인:

```bash
./.venv/bin/python -m pytest -q tests/test_phase2_simulation_context.py tests/test_infra_store.py
```

실패 요약:

- `sim_result`에 `meme_flow_logs` 키 없음
- 프로필 선택 결과 비어 있음
- runlog에 `type=meme_flow` row 미기록

---

## 3) Root Cause

- 밈은 기존에 `meme_seed_id`만 선택되어 round row에 태깅될 뿐,
  확산 단계/감쇠(반감기) 상태를 계산하는 런타임 로직이 없었다.
- 저장 계층(`storage.persist_run`)도 밈 전용 이벤트 row 타입을 직렬화하지 않았다.

---

## 4) GREEN

수정 파일:

- `src/project_dream/sim_orchestrator.py`
  - `meme_flow_logs`를 round-loop stage payload에 추가
  - 밈 컨텍스트/프로필/반감기 계산 helper 추가
  - 라운드별 밈 확산 로그(허브->공장->역류) 생성
  - round row에 `meme_decay_profile`, `meme_heat`, `meme_half_life`, `meme_phase` 기록
  - `thread_state`에 밈 모델 상태(`meme_decay_profile`, `meme_half_life`, `meme_factory_board_id`) 추가
- `src/project_dream/storage.py`
  - `meme_flow_logs`를 runlog에 `type: "meme_flow"`로 저장

---

## 5) Verification

타깃:

```bash
./.venv/bin/python -m pytest -q tests/test_phase2_simulation_context.py tests/test_infra_store.py
```

- 결과: `25 passed`

전체:

```bash
./.venv/bin/python -m pytest -q
```

- 결과: `207 passed`

---

## 6) Next Stage

- P1-3 후보:
  - 보드별 문화 가중치 오버라이드(냉소/싸움/정리/규정 인용) 정교화
  - 다이얼과 문화 가중치 상호작용 지표를 eval metric으로 노출
