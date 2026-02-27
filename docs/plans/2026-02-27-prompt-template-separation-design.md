# Project Dream Prompt Template Separation Design

## Goal

시뮬레이션 생성/요약/검증 문구를 코드 로직에서 분리해, 향후 LLM 연동 시 템플릿 교체만으로 동작을 전환할 수 있게 한다.

## Scope

- 프롬프트 템플릿 레지스트리 모듈 추가
- 템플릿 렌더링 유틸(`render_prompt`) 추가
- 기존 하드코딩 문구를 템플릿 호출로 치환
  - comment 생성
  - report summary 생성
  - lore validation reason 문구
- 템플릿 분리 동작 테스트 추가

## Approaches

### 1) Python Registry 기반 템플릿 분리 (Recommended)

- 설명: `prompt_templates.py`에 `PROMPT_TEMPLATE_REGISTRY`와 렌더러를 두고, 로직 모듈이 템플릿 키로 호출
- 장점: 구현 간결, 테스트 용이, 이후 파일/DB 기반으로 확장하기 쉬움
- 단점: 템플릿이 코드 파일에 존재

### 2) JSON/YAML 파일 기반 템플릿 로더

- 설명: 템플릿을 외부 파일로 저장하고 런타임 로딩
- 장점: 비개발자 수정에 유리
- 단점: 패키지 데이터 관리/배포 복잡도 증가

### 3) Pack(`template_pack`)에 템플릿 통합

- 설명: 기존 pack 로딩 파이프라인으로 템플릿까지 관리
- 장점: 설정 일원화
- 단점: 현재 도메인 pack과 프롬프트 pack 관심사 혼합

선택: 1번.

## Template Set Contract

- `template_set` 키 기반 레지스트리 구조
- 기본값: `v1`
- 필수 키:
  - `thread_generation`
  - `comment_generation`
  - `report_summary`
  - `validation_lore`
- 인터페이스:
  - `render_prompt(template_key, variables, template_set="v1") -> str`

## Integration Points

- `gen_engine.generate_comment(...)`
  - 기존 f-string 제거
  - `comment_generation` 템플릿 사용

- `report_generator.build_report_v1(...)`
  - summary 필드 생성 시 `report_summary` 템플릿 사용

- `gate_pipeline.run_gates(...)`
  - lore gate reason을 `validation_lore` 템플릿 기반 문구로 통일

## Extensibility

- 향후 `v2`, `v3` 템플릿 세트 추가 시 registry에 세트만 확장
- LLM adapter 도입 시 템플릿 문자열을 그대로 prompt input으로 재사용 가능

## Testing Strategy

- 템플릿 렌더링 단위 테스트:
  - 정상 렌더링
  - unknown template_set/key 예외 처리
- 회귀 테스트:
  - 기존 generator/report/gate 관련 테스트가 유지 통과하는지 확인
