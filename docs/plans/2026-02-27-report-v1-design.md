# Project Dream Report V1 Design (JSON-First)

## Goal

작가용 리포트를 JSON을 원본(SoT)으로 고정하고, Markdown은 JSON 렌더링 결과로 생성한다.

## Scope

- `models.py`에 `ReportV1` 및 하위 스키마 추가
- `report_generator.py`를 규칙 기반 `ReportV1` 빌더로 교체
- `storage.py`에서 `ReportV1` 기반 JSON/Markdown 저장
- 테스트로 필수 섹션/개수 조건 보장

## ReportV1 Required Sections

- `lens_summaries` (커뮤니티 렌즈별 요약, 4개)
- `highlights_top10` (상위 하이라이트 최대 10개)
- `conflict_map` (claim_a, claim_b, third_interest, mediation_points)
- `dialogue_candidates` (3~5세트)
- `foreshadowing` (떡밥/미스터리 목록)
- `risk_checks` (rule/similarity/safety)

## Evolution Contract

- 생성 인터페이스 고정:
  - `build_report_v1(seed, sim_result, packs) -> ReportV1`
- 구현체 교체 가능:
  - RuleBasedReporter -> ScoredReporter -> LLMReporter
