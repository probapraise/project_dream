# Project Dream Local Ops Automation Design

## Goal

환경이 자주 바뀌어도 같은 절차로 서버 실행/기본 점검을 재현할 수 있도록 로컬 운영 자동화를 제공한다.

## Scope

- `.env` 기반 서버 실행 스크립트 추가
- API 스모크 점검 스크립트 추가
- `.env.example` 제공 및 README 3분 셋업 문서화

## Artifacts

- `.env.example`
- `scripts/dev_serve.sh`
- `scripts/smoke_api.sh`
- `README.md` Local Ops 섹션
- `.gitignore`에 `.env` 추가

## Runtime Behavior

### `dev_serve.sh`

- `.env` (또는 `PROJECT_DREAM_ENV_FILE`) 로드
- `PROJECT_DREAM_API_TOKEN` 필수
- host/port/runs/packs 값을 env에서 읽어 `project_dream.cli serve` 실행
- 워크트리/공용 git 루트 `.venv`를 우선 사용

### `smoke_api.sh`

- `GET /health` -> `200`
- 인증 없는 `GET /runs/latest` -> `401`
- 인증된 `POST /simulate` -> `200` + `run_id`
- 인증된 `GET /runs/latest` -> `200`

## Compatibility

- 기존 CLI/API 계약 변경 없음
- 운영 보안 정책(health 제외 토큰 필수) 유지

## Testing Strategy

- 스크립트 문법 검증(`bash -n`)
- 기존 테스트 스위트(`pytest`) 통과
- 실제 서버 실행 + 스모크 스크립트 통과
