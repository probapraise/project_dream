# Authoring -> World Pack Compile Implementation (2026-03-01)

## Goal

- 작가가 작성한 world authoring JSON을 런타임 `packs/world_pack.json`으로 안전하게 반영하는 컴파일 경로를 추가한다.
- 컴파일 이후 `pack_manifest.json` 체크섬을 자동 갱신해 즉시 실행 가능한 상태를 보장한다.

## Scope

- 신규 모듈: `src/project_dream/authoring_compile.py`
  - 입력 모드:
    - 단일 파일: `authoring/world_pack.json`
    - 분할 파일: `world_meta.json` + `world_{entities,relations,timeline_events,world_rules,glossary}.json`
      - 선택 파일: `world_forbidden_terms.json`, `world_relation_conflict_rules.json`
  - `WorldPackPayload` strict validation 적용
  - 출력: `packs/world_pack.json`, `packs/pack_manifest.json`
- 기존 모듈 확장:
  - `src/project_dream/pack_service.py`
    - `write_pack_manifest(...)` 추가
  - `src/project_dream/cli.py`
    - `compile` 서브커맨드 추가

## TDD

- RED:
  - `tests/test_authoring_compile.py` (new)
  - `tests/test_cli_compile_e2e.py` (new)
  - `tests/test_cli_smoke.py` (`compile` parser 테스트 추가)
  - 초기 실패: `ModuleNotFoundError: project_dream.authoring_compile`
- GREEN:
  - 컴파일 모듈/CLI/manifest writer 구현 후 통과

## Verification

```bash
./.venv/bin/pytest -q tests/test_authoring_compile.py tests/test_cli_compile_e2e.py tests/test_cli_smoke.py
# 18 passed

./.venv/bin/pytest -q
# 240 passed
```
