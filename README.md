# Project Dream MVP

Latest resume handoff: `docs/plans/2026-02-28-context-compression-handoff.md`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
python -m project_dream.cli ingest --packs-dir packs --corpus-dir corpus
python -m project_dream.cli compile --authoring-dir authoring --packs-dir packs
python -m project_dream.cli simulate --seed examples/seeds/seed_001.json --output-dir runs --rounds 3
python -m project_dream.cli evaluate --runs-dir runs --metric-set v2
python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10
python -m project_dream.cli regress-live
python -m project_dream.cli serve --api-token local-dev-token
# or: export PROJECT_DREAM_API_TOKEN=local-dev-token && python -m project_dream.cli serve
```

`evaluate`는 스키마 체크와 함께 report 내용 품질 체크(중재포인트/떡밥/대사필드/severity 표준값)를 함께 검증합니다.
`serve`는 `GET /health`를 제외한 모든 API 호출에 `Authorization: Bearer <token>` 헤더가 필요합니다.
`serve` 실행 중에는 요청 로그가 stderr에 JSON 라인으로 출력되며, `method/path/status/latency_ms/auth_ok/event` 필드를 포함합니다.

## Local Ops (3-Min Setup)

```bash
cp .env.example .env
# .env에서 PROJECT_DREAM_API_TOKEN 값을 원하는 값으로 변경

./scripts/dev_serve.sh
# 다른 터미널에서:
./scripts/smoke_api.sh
```

`.env`에서 `PROJECT_DREAM_HOST/PORT/RUNS_DIR/PACKS_DIR`를 조정하면 환경이 바뀌어도 같은 명령으로 서버 실행/검증이 가능합니다.
벡터 인덱스 기본값도 `.env`로 고정할 수 있습니다:

- `PROJECT_DREAM_VECTOR_BACKEND=memory|sqlite`
- `PROJECT_DREAM_VECTOR_DB_PATH=<path>` (sqlite 선택 시 권장)

CLI(`simulate/regress/regress-live/serve`)에서 벡터 옵션을 명시하지 않으면 위 환경변수 기본값을 사용합니다.
추가로 운영 스크립트도 같은 설정을 사용합니다.

- `scripts/dev_serve.sh`: `PROJECT_DREAM_VECTOR_BACKEND`, `PROJECT_DREAM_VECTOR_DB_PATH`
- `scripts/regress_live.sh`: `PROJECT_DREAM_LIVE_VECTOR_BACKEND`, `PROJECT_DREAM_LIVE_VECTOR_DB_PATH`
- `scripts/smoke_api.sh`: `PROJECT_DREAM_SMOKE_VECTOR_SQLITE_CHECK=1`일 때 sqlite 벡터 모드 추가 점검

### Corpus Build (Ingest)

`ingest` 명령은 pack 데이터를 기준으로 유사도/레퍼런스 코퍼스를 생성합니다.

```bash
python -m project_dream.cli ingest --packs-dir packs --corpus-dir corpus
```

생성 파일:

- `corpus/reference.jsonl`
- `corpus/refined.jsonl`
- `corpus/generated.jsonl`
- `corpus/manifest.json`

`simulate`, `regress`, `regress-live`는 기본적으로 `corpus/`를 자동 로드해 context corpus에 병합합니다.
다른 경로를 쓰려면 각 명령에 `--corpus-dir <path>`를 지정하면 됩니다.
또한 KB 조회(`search_knowledge`, `retrieve_context_bundle`)도 동일 `corpus/`를 인덱싱해 `kind=corpus` 검색이 가능합니다.

### World Authoring Compile

`compile` 명령은 작성용 세계관 JSON을 런타임 pack으로 반영하고 manifest checksum을 갱신합니다.

```bash
python -m project_dream.cli compile --authoring-dir authoring --packs-dir packs
```

입력 우선순위:

- `authoring/world_master/` split 디렉터리 (`meta.json`, `nodes.json` 등)
- `authoring/world_master.json` (`world_master.v1`, 대량 세계관 작성용)
- `authoring/world_pack.json` (`world_schema.v1`, 단일 파일)
- split files (`world_meta.json`, `world_entities.json` 등)

`world_master.v1` 템플릿은 `examples/world_master_template.json`를 참고하면 됩니다.
`world_master` 입력을 사용하면 compile 시 단일 파일과 split 디렉터리를 자동 동기화합니다.
필요하면 export 경로를 직접 지정할 수 있습니다:

```bash
python -m project_dream.cli compile \
  --authoring-dir authoring \
  --packs-dir packs \
  --world-master-export-file authoring/world_master.json \
  --world-master-export-dir authoring/world_master
```

### Run Tests With Gemini 3.1 Flash

`.env`에서 아래를 설정하면 기본 LLM client가 Google AI Studio를 사용합니다.

```bash
PROJECT_DREAM_LLM_PROVIDER=google
PROJECT_DREAM_LLM_MODEL=gemini-3.1-flash
GOOGLE_API_KEY=<your-key>
GEMINI_API_KEY=$GOOGLE_API_KEY
PROJECT_DREAM_LLM_RESPONSE_MODE=prompt_passthrough
```

`prompt_passthrough`는 프로세스당 1회 Gemini 연결을 확인하고, 이후에는 응답 대신 prompt를 사용해 테스트를 빠르고 결정적으로 유지합니다.
실제 모델 출력을 그대로 쓰려면 `PROJECT_DREAM_LLM_RESPONSE_MODE=model_output`로 바꾸면 됩니다.
`gemini-3.1-flash`가 계정에서 아직 미노출인 경우 자동으로 `gemini-3-flash-preview` 등으로 폴백합니다.

### Live LLM Regression Smoke

실제 모델 출력 품질을 빠르게 확인하려면 아래 명령을 사용합니다.

```bash
python -m project_dream.cli regress-live
# 또는
./scripts/regress_live.sh
```

`regress-live`는 실행 중에만 LLM 설정을 아래처럼 강제합니다.

- `PROJECT_DREAM_LLM_PROVIDER=google`
- `PROJECT_DREAM_LLM_RESPONSE_MODE=model_output`
- `PROJECT_DREAM_LLM_MODEL=gemini-3.1-flash` (기본값, `--llm-model`로 변경 가능)

기본은 `max-seeds=2`, `metric-set=v2`의 소규모 스모크 실행이며, 인자는 `regress`와 동일하게 대부분 커스터마이즈할 수 있습니다.
또한 baseline 품질 게이트를 기본으로 수행합니다.

```bash
# 1) 기준선 생성/갱신
python -m project_dream.cli regress-live --update-baseline

# 2) 이후 실행은 baseline과 자동 비교(기본)
python -m project_dream.cli regress-live
```

기본 baseline 경로는 `runs/regressions/regress-live-baseline.json`이며,
비교 허용치는 `--allowed-rate-drop`(기본 0.05), `--allowed-community-drop`(기본 1)입니다.

### Server Control

```bash
./scripts/server_ctl.sh start
./scripts/server_ctl.sh status
./scripts/server_ctl.sh check
./scripts/server_ctl.sh logs
./scripts/server_ctl.sh logs -f
./scripts/server_ctl.sh restart
./scripts/server_ctl.sh stop
```

`check`는 서버가 꺼져 있으면 먼저 기동한 뒤 `smoke_api.sh`를 실행합니다.

## CI Regression Gate

GitHub Actions(`Regression Gate`)가 PR 및 `main` push에서 `pytest`와 `regress(metric-set v2)`를 자동 실행합니다.
