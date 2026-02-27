# Project Dream Validation Hardening Design

## Goal

Validation 3중 체크(Safety/Similarity/Lore)를 MVP 수준으로 강화해, 위험 출력과 정합성 붕괴를 더 일찍 차단한다.

## Scope

- `run_gates` 로직 고도화
  - Safety: 경고 코드 기반 탐지 + 마스킹/치환
  - Similarity: top-k 유사도 추적 + 임계치 기반 재작성
  - Lore: 체크리스트 기반 위반 탐지 + 재작성
- 게이트 결과에 진단용 부가정보를 포함

## Approaches

### 1) Existing `run_gates` 확장 (Recommended)

- 설명: 기존 인터페이스를 유지하면서 gate dict 필드를 확장
- 장점: 하위호환, 변경 범위 작음, 빠른 적용 가능
- 단점: 한 파일에 로직이 다소 집중

### 2) Validation 엔진 모듈 분리

- 설명: safety/similarity/lore를 각각 독립 함수/모듈로 분리
- 장점: 장기 유지보수 유리
- 단점: 현재 규모 대비 과설계

### 3) 외부 벡터DB 기반 Similarity

- 설명: 임베딩+ANN top-k 구조 즉시 도입
- 장점: 정확도 향상 가능
- 단점: 의존성/운영 복잡도 급증

선택: 1번.

## Gate Hardening Plan

### Safety Gate

- 탐지 항목:
  - 전화번호 패턴
  - taboo word
- 출력 필드:
  - `warnings`: 경고 코드 배열 (`PII_PHONE`, `TABOO_TERM:<term>`)
- 실패 조건: `warnings` 비어있지 않음
- 재작성: 마스킹/치환 수행

### Similarity Gate

- 계산:
  - corpus 전체 ratio 계산 후 점수 내림차순 정렬
  - 상위 `top_k=3` 유지
- 출력 필드:
  - `top_k`: `[{index, score}]`
- 실패 조건: `max_similarity >= threshold`
- 재작성: 유사도 재작성 접미사 추가

### Lore Gate

- 체크리스트:
  - `evidence_keyword_found` (`정본/증거/로그/출처/근거`)
  - `context_keyword_found` (`주장/판단/사실/정황/의혹`)
- 출력 필드:
  - `checklist` dict
- 실패 조건:
  - evidence 키워드 부재
- 재작성:
  - 증거 기준 안내 문구 추가

## Compatibility

- 기존 필수 키(`gate_name`, `passed`, `reason`) 유지
- 추가 키는 선택적 진단 정보로만 사용
- 기존 orchestrator/eval/report 흐름 영향 최소화

## Testing Strategy

- 기존 게이트 테스트 회귀 유지
- 신규 테스트 추가:
  - similarity top-k 구조 검증
  - lore checklist 및 evidence 미존재 실패 검증
