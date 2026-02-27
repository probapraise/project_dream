# Project Dream MVP Design (Balanced Minimal Set)

## 1. Goal

`dev_spec` 기반으로 다음을 한 번에 성립시키는 Python MVP를 구축한다.

- Pack 스키마/로딩 검증
- 1회 시뮬레이션(3라운드 이상) 턴 루프
- 3중 게이트(안전/유사도/정합성)
- 작가용 리포트 출력

## 2. Scope

### In Scope

- Python 단일 저장소의 모듈러 모놀리스 구조
- CLI 진입점 기반 실행(`simulate`, `validate`, `report`)
- 결정적 템플릿 생성기(LLM 어댑터 인터페이스만 확보)
- 파일 기반 저장(`runs/<run_id>/runlog.jsonl`, `report.md`, `report.json`)

### Out of Scope (MVP)

- 실서비스 UI
- 외부 커뮤니티 크롤링
- 완전 자동 집필
- 복잡한 분산/병렬 인프라

## 3. Architecture

모듈 경계를 명시한 모놀리스로 시작한다. 핵심 원칙은 "교체 가능한 경계 + 고정된 입출력 모델"이다.

- `pack_service`: Pack 로딩, Pydantic 검증, 참조 무결성 검사
- `kb_index`(MVP): 파일 기반 필터 조회/문맥 번들링
- `persona_service`: 라운드별 참가자 선택, 기본 보이스 제약
- `gen_engine`: Stage1(내용 구조) -> Stage2(표현), 초기 템플릿 기반
- `gate_pipeline`: 안전/유사도/정합성 검증 + 재작성 트리거
- `env_engine`: 노출 점수, 신고 누적, 임시가리기/봉문/유령/제재 전이
- `sim_orchestrator`: 턴 루프 전체 제어, 재시도 상한 관리
- `report_generator`: 요약/하이라이트/갈등/대사/리스크 보고서 생성
- `storage`: runlog/report 저장

## 4. Runtime Data Flow

1. `simulate` 명령 입력(seed + 옵션)
2. Pack 로딩/검증
3. 컨텍스트 번들 생성(board/community/persona/rule)
4. 스레드 후보 생성 및 선택
5. 댓글 라운드 반복(최소 3회)
6. 매 생성물마다 3중 게이트 실행
7. 환경 규칙 적용(점수/신고/잠금/유령/제재)
8. 종료 조건 확인 후 리포트 생성/저장

## 5. Contracts for Future Replacement

전면 재수정을 피하기 위해 아래 계약을 고정한다.

- 데이터 계약: Pydantic 모델(`Pack`, `ThreadState`, `ActionLog`, `GateResult`, `RunReport`)
- 엔진 계약: `Generator`, `Gate`, `EnvEngine`, `Reporter`, `Retriever` 프로토콜
- 저장 계약: `runlog.jsonl` 레코드 스키마와 report JSON 필수 필드

이 계약을 유지하면 다음 교체가 부분 수정으로 가능하다.

- 템플릿 생성기 -> 실제 LLM 생성기
- 수동 루프 오케스트레이터 -> LangGraph
- 파일 저장 -> DB/벡터 인덱스

## 6. Testing Strategy

### Unit Tests

- Pack 필수 필드/중복 ID/참조 무결성
- 환경 엔진 점수 계산 및 상태 전이
- 게이트 위반 탐지 및 재작성 트리거
- 리포트 필수 섹션 보장

### Integration Tests

- 고정 seed 2~3개로 전체 `simulate` 실행
- 3라운드 이상 로그 생성
- gate 결과(pass/fail + reason) 기록
- report 필수 항목 존재

### Regression Baseline

- 결정적 템플릿 생성기 기반 스냅샷 검증
- LLM 전환 시 구조/규칙 중심 검증으로 단계적 변경

## 7. MVP Definition of Done

- CLI 단일 명령으로 runlog/report 생성
- 최소 Pack(Board/Community/Rule/Persona) 로드 성공
- 3중 게이트 및 재작성 로그 저장
- 테스트 스위트 통과

## 8. Risks and Mitigations

- 과설계 위험: 모놀리스 유지, 인터페이스만 선제 분리
- 품질 저하 위험: 게이트/리포트 기준을 테스트로 고정
- 확장 리팩터링 위험: 계약 테스트로 교체 안전성 확보
