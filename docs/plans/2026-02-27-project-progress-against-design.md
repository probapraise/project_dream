# Project Dream 전체 설계 대비 진행 현황 (2026-02-27)

기준 시점: `main` @ `19da359`  
기준 설계 문서: `docs/plans/2026-02-27-project-dream-mvp-design.md`

## 1) MVP 핵심 설계 대비

- Pack 스키마/로딩/참조 검증: 완료
- 3라운드 이상 시뮬레이션 턴 루프: 완료
- 3중 게이트(안전/유사도/정합성): 완료
- 환경 엔진(노출 점수/상태 전이): 완료
- 작가용 리포트 생성/저장(`report.json`, `report.md`): 완료
- 파일 저장 계약(`runs/<run_id>/...`): 완료
- CLI 기본 흐름: 완료 (`simulate`, `evaluate`, `regress`, `serve`)

## 2) MVP 이후 확장 설계 대비

- Prompt 템플릿 분리: 완료
- Validation hardening: 완료
- 품질 지표 세트(v1/v2) + 평가 강화: 완료
- 회귀 배치 러너 + summary 산출: 완료
- 회귀 CI 게이트(GitHub Actions): 완료
- LLM 경계 분리(댓글/리포트 어댑터): 완료
- Web API/HTTP 서버 계층: 완료

## 3) Web API 구현 범위 (현재)

### POST
- `/simulate`
- `/evaluate`
- `/regress`

### GET
- `/health`
- `/runs/latest`
- `/runs/{run_id}/report`
- `/runs/{run_id}/eval`
- `/runs/{run_id}/runlog`
- `/regressions` (`?limit=` 지원)
- `/regressions/latest`
- `/regressions/{summary_id}`

## 4) 품질/검증 상태

- 로컬 테스트: `54 passed` (최근 실행 기준)
- CI 워크플로우: `Regression Gate` 구성 완료
  - `pytest`
  - `regress --metric-set v2`
  - 회귀 summary를 Job Summary로 렌더링
  - 회귀 산출물 artifact 업로드

## 5) 아직 미착수/범위 밖 항목

MVP 설계의 Out of Scope로 명시된 항목은 아직 미착수 상태:

- 실서비스 UI
- 외부 커뮤니티 크롤링
- 완전 자동 집필
- 복잡한 분산/병렬 인프라

추가로, 운영 보안 관점의 인증/인가(예: API 토큰)는 아직 미구현.

## 6) 결론

`project-dream-mvp-design` 기준 MVP와 이후 합의된 API/회귀 편의 확장까지는 구현 완료 상태다.  
현재는 "기능 확장"보다 "운영 준비(보안/배포/관측)" 단계로 넘어갈 수 있는 시점이다.
