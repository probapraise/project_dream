# Context Compression Handoff (2026-02-28)

## 1) Snapshot (Ground Truth)

- Repository: `/home/ljhljh/project_dream`
- Branch: `main`
- HEAD: `2c0c6c5` (`origin/main`과 동기화됨)
- Working tree: clean
- Latest verification:
  - Command: `./.venv/bin/python -m pytest -q`
  - Result: `104 passed`

## 2) What Is Already Implemented (High-level)

- Core packs + loader + minimum requirements:
  - `board/community/rule/entity/persona/template` pack 로딩/참조 검증
- Simulation loop:
  - thread candidate/selection
  - round loop
  - gate retry
  - moderation stage + end condition
  - stage trace/runlog persistence
- Report/eval/regression:
  - `report.v1`, `eval.v1`, regression summary
  - CI regression gate
- Web API + token auth + access log + run/regression read endpoints
- LLM adapter:
  - echo default + Google AI Studio support
  - regress-live + baseline quality gate
- Corpus work (recent):
  - `ingest` command added (`packs -> corpus/*.jsonl`)
  - runtime corpus merge (`simulate/regress/regress-live`)
  - KB index now ingests corpus passages (`kind=corpus`)

## 3) Confirmed Non-goals (Do NOT implement)

Based on `리서치/dev_spec.docx` section 1.2:

- 외부 커뮤니티 크롤링/복제 기능
- 완전 자동 집필(원고 전체 자동 작성)
- 초기 범위에서 대규모 상용화 인프라

## 4) Gap Register (Spec vs Current)

Priority 기준:
- `P0`: MVP 품질/정확도에 직접 영향
- `P1`: 확장성/품질 고도화
- `P2`: 운영/인프라 고도화

### P0

1. `env_engine` 상태/권한 모델 미완
- Spec ref: dev_spec 4.x, 6.5
- Current: 단순 점수 + 상태 전이만 구현
- Missing:
  - 계정 유형(public/alias/mask), 제재 레벨(L1~L5), 인증/항소 상세 정책
  - 정렬 탭(최신/주간화제/증거우선/보존우선) 분리 로직
  - 액션 타입 전부를 상태 전이에 반영

2. 생성 엔진 Stage1/Stage2 분리 미구현
- Spec ref: dev_spec 6.7
- Current: 단일 `generate_comment()` 호출
- Missing:
  - Stage1(내용 구조화: claim/evidence/intent)
  - Stage2(표현 렌더: voice/style)
  - U/E/M/S/H 다이얼의 실질 제어 반영

3. Gate pipeline 고도화 미구현
- Spec ref: dev_spec 6.8
- Current: regex + RapidFuzz + keyword lore
- Missing:
  - 정합성 위반에 대한 룰 ID 기반 정밀 리포트
  - (선택 기술 제외하더라도) 룰/엔티티 참조형 consistency checker

4. Template/Flow 상세 스키마 활용 미완
- Spec ref: dev_spec 5.3
- Current: 템플릿 최소 필드만 사용
- Missing:
  - `title_patterns`, `body_sections`, `trigger_tags`, `taboos`, `escalation_rules` 등 실행 반영

### P1

5. Pack 스키마를 Pydantic으로 엄격 검증하는 계층 부재
- Spec ref: dev_spec 6.3
- Current: 수동 딕셔너리 검증 중심

6. KB retrieval이 진짜 hybrid(BM25+vector) 아님
- Spec ref: dev_spec 6.2
- Current: token overlap scoring

7. Report 생성 결과에 대한 별도 gate 없음
- Spec ref: dev_spec 6.9 DoD
- Current: 리포트는 생성 후 바로 저장

8. 평가 스택 외부 연동(promptfoo/ragas/tracing) 미구현
- Spec ref: dev_spec 6.10
- Current: 내부 pytest + custom eval only

### P2

9. 저장소가 파일 기반이며 DB/벡터DB/그래프 저장소는 미도입
- Spec ref: dev_spec 3.5
- Current: `FileRunRepository`

10. LangGraph 오케스트레이션 미도입
- Spec ref: dev_spec 6.6
- Current: 단일 함수 기반 턴 루프

## 5) Immediate Start Plan (Next Session)

### First task to start immediately: `P0-1 env_engine 확장`

Reason:
- 플랫폼 규칙이 프로젝트 핵심 도메인이고,
- 현재 구현이 가장 단순화되어 있어 효과 대비 개선폭이 큼.

Execution checklist:

1. 테스트 먼저 추가 (RED)
- new: `tests/test_env_engine_policy_matrix.py`
- cases:
  - account_type별 비용/노출 가중치 차이
  - 신고 누적 + severity + appeal 조합 전이
  - 제재 레벨(L1~L5) 단계 검증
  - 정렬 탭별 상위 노출 결과 차이

2. 최소 구현 (GREEN)
- update: `src/project_dream/env_engine.py`
- update: `src/project_dream/sim_orchestrator.py`
- 필요 시 모델 보강: `src/project_dream/models.py`

3. 회귀 확인
- `./.venv/bin/python -m pytest tests/test_env_engine_policy_matrix.py -q`
- `./.venv/bin/python -m pytest -q`

## 6) Resume Commands (copy/paste)

```bash
cd /home/ljhljh/project_dream
git pull --ff-only
./.venv/bin/python -m pytest -q

# 시작 지점: env_engine 확장 작업 브랜치
git checkout -b feat/env-engine-policy-matrix
```

## 7) File Index For Fast Resume

- Spec source: `/home/ljhljh/project_dream/리서치/dev_spec.docx`
- This handoff: `/home/ljhljh/project_dream/docs/plans/2026-02-28-context-compression-handoff.md`
- Core modules:
  - `src/project_dream/env_engine.py`
  - `src/project_dream/sim_orchestrator.py`
  - `src/project_dream/gate_pipeline.py`
  - `src/project_dream/gen_engine.py`
  - `src/project_dream/kb_index.py`
  - `src/project_dream/report_generator.py`
