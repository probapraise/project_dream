# Project Dream Infra Store + Web API Scaffold Design

## Goal

`/infra/store`, `/infra/web_api` 경계를 도입하고, CLI와 Web API가 동일한 서비스 레이어를 재사용하도록 구조를 정리한다.

## Scope

- `RunRepository` 인터페이스 정의
- 파일 기반 구현 `FileRunRepository` 추가
- 서비스 레이어(`simulate`, `evaluate`) 추가
- Web API 파사드(`health`, `simulate`, `evaluate`) 추가
- 기존 CLI는 서비스 레이어 + repository를 사용하도록 전환

## Architecture

### Infra Store

- 경로: `project_dream/infra/store.py`
- 구성:
  - `RunRepository` protocol
  - `FileRunRepository` implementation

책임:
- run 저장(`runlog/report`)
- eval 저장
- 최신 run 조회
- run_id 기반 run 조회

### App Service

- 경로: `project_dream/app_service.py`
- 함수:
  - `simulate_and_persist(...)`
  - `evaluate_and_persist(...)`

책임:
- 도메인 실행 오케스트레이션
- repository 경유 저장/조회
- CLI/API 공용 로직 제공

### Web API Facade

- 경로: `project_dream/infra/web_api.py`
- 클래스: `ProjectDreamAPI`
- 메서드:
  - `health()`
  - `simulate(seed_payload, rounds=3, packs_dir=...)`
  - `evaluate(run_id=None, metric_set="v1")`

주의:
- 실제 HTTP 서버(FastAPI/Flask) 도입은 범위 밖
- 현재는 어댑터/핸들러 레이어 스캐폴딩

## Compatibility

- 기존 CLI 인자/출력 계약 유지
- 기존 `storage.py`는 내부 파일 포맷 구현체로 재사용
- regression runner 등 기존 기능 영향 최소화

## Testing Strategy

- `infra/store` 단위 테스트:
  - run 저장/조회
  - eval 저장
- `web_api` 테스트:
  - health 응답
  - simulate/evaluate 흐름
- 기존 CLI e2e 테스트 회귀 통과 확인
