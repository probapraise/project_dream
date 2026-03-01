# World Master Schema v1 (Authoring) + Runtime Projection

## 1) 목적

- 월드 바이블 문서의 대규모 설정(인물, 가문, 종족, 역사, 규정, 조직, 증거, 용어)을 한 번에 수용할 수 있는 작성용 스키마를 정의한다.
- 엔진 런타임은 기존 `world_schema.v1` 계약을 유지하고, 작성용 스키마(`world_master.v1`)를 컴파일 단계에서 투영(projection)한다.

핵심 전략:
- `Authoring Layer`: 확장 가능한 그래프형 구조(`world_master.v1`)
- `Runtime Layer`: 현재 엔진 호환 구조(`world_schema.v1`)

---

## 2) 월드 바이블에서 확인된 데이터 축

아래 축이 반복적으로 등장하며, 모두 ID 참조가 가능한 구조가 필요하다.

- 인물/가문/종족/조직/기관/장소/유물
- 관계(혈통, 소속, 동맹, 적대, 대표, 규제 등)
- 연표 사건(참여자, 위치, 촉발 요인, 결과)
- 규정/법/운영 규칙
- 용어사전(동의어 포함)
- 증거/출처/주장(공개 레벨, 신뢰도, 근거 문서)
- 분류체계(taxonomy: 종족 계보, 계급 분류, 직능 분류 등)

---

## 3) 스키마 구조

`world_master.v1` 최상위 필드:

- `schema_version`, `version`
- `forbidden_terms`
- `relation_conflict_rules`
- `kind_registry`
- `nodes`
- `edges`
- `events`
- `rules`
- `glossary`
- `source_documents`
- `claims`
- `taxonomy_terms`

### 3.1 `nodes` (엔티티 허브)

- 어떤 타입이든 `kind`로 수용:
  - 예: `character`, `family`, `species`, `organization`, `faction`, `location`, `artifact`, `institution`, `religion`, `custom_*`
- 공통 필드:
  - `id`, `kind`, `name`, `summary`, `tags`, `aliases`
  - `linked_org_id`, `linked_char_id`, `linked_board_id` (엔진 연계용)
  - `attributes` (대량 확장을 위한 가변 속성)
  - `source`, `valid_from`, `valid_to`, `evidence_grade`, `visibility`

### 3.0 `kind_registry` (범주 확장 허브)

- 새 범주를 코드 수정 없이 데이터로 선언하기 위한 레지스트리
- 권장 하위 키:
  - `node_kinds`: 신규 노드 종류 선언
  - `edge_kinds`: 신규 관계 종류 선언
- 필드/규칙을 느슨하게 유지해, 미리 정의되지 않은 도메인도 수용 가능

### 3.2 `edges` (관계 허브)

- 공통 필드:
  - `id`, `relation_type`, `from_id`, `to_id`, `notes`
  - `qualifiers` (가변 관계 속성: 계승순위, 계약조건, 기간 등)
  - `source`, `valid_from`, `valid_to`, `evidence_grade`, `visibility`

### 3.3 `events` (역사/사건 허브)

- 공통 필드:
  - `id`, `title`, `summary`, `era`
  - `participant_ids`, `location_id`, `trigger_ids`, `consequence_ids`
  - `source`, `valid_from`, `valid_to`, `evidence_grade`, `visibility`

### 3.4 `rules` / `glossary`

- `rules`: 세계관 규범/법/학칙/제도
- `glossary`: 용어/정의/별칭
- 두 섹션 모두 `source + validity + evidence_grade + visibility`를 포함해 정합성/추적성을 유지

### 3.5 `source_documents` / `claims` / `taxonomy_terms`

- `source_documents`: 근거 문서 카탈로그
- `claims`: 주장 단위(주체/술어/대상, confidence, 근거 문서)
- `taxonomy_terms`: 분류 체계(부모-자식 참조)

---

## 4) 대량 데이터 확장 원칙

### 4.1 새 도메인 추가 시

- 새 파일/테이블을 추가하지 않고 `nodes.kind` + `attributes` + `taxonomy_terms`로 먼저 수용한다.
- 전용 섹션 분리가 진짜 필요할 때만 확장한다.

### 4.2 스키마 안정성

- 엔진은 `world_schema.v1`만 사용하므로 런타임 안정성 유지.
- 작성용 스키마는 컴파일 단계에서만 진화.
- 즉, 세계관 데이터가 커져도 런타임 코드 변경을 최소화할 수 있다.

### 4.3 신뢰성/검증

- `world_master.v1`은 컴파일 시 참조 무결성 검증:
  - edge `from_id/to_id` 존재성
  - event participant/location 존재성
  - rule scope 존재성
  - claim subject/object/source 존재성
  - taxonomy parent 존재성
- `confidence`는 `0.0~1.0` 범위 강제

---

## 5) 컴파일 경로(현재 반영 상태)

- 입력 우선순위:
  1. `authoring/world_master/` split 디렉터리
  2. `authoring/world_master.json`
  3. `authoring/world_pack.json`
  4. split files (`world_meta.json + world_*.json`)
- 출력:
  - `packs/world_pack.json` (`world_schema.v1`)
  - `packs/pack_manifest.json` (checksum 자동 갱신)
  - `world_master` 입력 사용 시 단일/분할 포맷 자동 동기화
    - `authoring/world_master.json`
    - `authoring/world_master/`

추가 보존:
- `world_master`의 고급 정보(`claims`, `source_documents`, `taxonomy_terms`)는
  `world_pack.extensions.world_master`에 보존된다.

---

## 6) ID 정책(권장)

- Node: `WN-{DOMAIN}-{NNN}` 예) `WN-CHAR-001`, `WN-FAMILY-017`
- Edge: `WE-{DOMAIN}-{NNN}`
- Event: `WV-{DOMAIN}-{NNN}`
- Rule: `WRULE-{DOMAIN}-{NNN}`
- Glossary: `WG-{DOMAIN}-{NNN}`
- Source: `SRC-{DOMAIN}-{NNN}`
- Claim: `CLM-{DOMAIN}-{NNN}`
- Taxonomy: `TAX-{DOMAIN}-{NNN}`

도메인 예시:
- `CHAR`, `FAMILY`, `SPECIES`, `ORG`, `FACTION`, `LOCATION`, `ACADEMY`, `RELIGION`, `ECON`

---

## 7) 운영 권장 플로우

1. 월드 바이블에서 설정 추출 후 `world_master.json` 작성
2. `python -m project_dream.cli compile --authoring-dir authoring --packs-dir packs`
3. `pytest -q` 또는 `simulate/regress`로 동작 검증
4. 필요 시 `canon gate` 룰 추가

---

## 8) 왜 이 구조가 “인물/가문/종족/역사” 대량 입력에 유리한가

- 도메인별 고정 테이블 폭증을 피하고, 그래프형(`nodes/edges/events`)으로 수렴
- 근거/주장/공개레벨을 분리해 스포일러/정본 관리 가능
- 런타임 계약은 보수적으로 유지해 엔진 안정성 확보
- 향후 SQL/그래프DB 도입 시에도 1:1 매핑이 쉬움
