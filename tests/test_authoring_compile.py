import hashlib
import json
import shutil
from pathlib import Path

import pytest

from project_dream.authoring_compile import compile_world_pack
from project_dream.pack_service import load_packs


def _copy_packs(tmp_path: Path) -> Path:
    dst = tmp_path / "packs"
    shutil.copytree(Path("packs"), dst)
    return dst


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minimal_world_master_payload() -> dict:
    return {
        "schema_version": "world_master.v1",
        "version": "1.0.0",
        "forbidden_terms": ["실명 주소"],
        "relation_conflict_rules": [],
        "kind_registry": {
            "node_kinds": [
                {
                    "kind": "character",
                    "required_attributes": [],
                    "description": "개별 인물",
                }
            ],
            "edge_kinds": [],
        },
        "nodes": [
            {
                "id": "WN-CHAR-001",
                "kind": "character",
                "name": "주인공",
                "summary": "테스트 주인공",
                "tags": ["protagonist"],
                "aliases": [],
                "attributes": {"origin": "academy"},
                "source": "worldbible.v4.3",
                "valid_from": "Y100",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
            }
        ],
        "edges": [],
        "events": [],
        "rules": [],
        "glossary": [],
        "source_documents": [],
        "claims": [],
        "taxonomy_terms": [],
    }


def test_compile_world_pack_from_monolithic_source_updates_manifest(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"

    payload = _read_json(packs_dir / "world_pack.json")
    payload["version"] = "1.2.0"
    payload["entities"].append(
        {
            "id": "WE-ARCHIVE-999",
            "entity_type": "facility",
            "name": "아카이브 별관",
            "summary": "테스트용 엔티티",
            "source": "authoring",
            "valid_from": "Y120",
            "valid_to": "",
            "evidence_grade": "B",
        }
    )
    _write_json(authoring_dir / "world_pack.json", payload)

    summary = compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)

    assert summary["source_mode"] == "monolithic"
    assert summary["entities"] >= 1
    compiled_world = _read_json(packs_dir / "world_pack.json")
    assert compiled_world["version"] == "1.2.0"
    assert any(row["id"] == "WE-ARCHIVE-999" for row in compiled_world["entities"])

    manifest = _read_json(packs_dir / "pack_manifest.json")
    assert manifest["files"]["world_pack.json"] == _sha256(packs_dir / "world_pack.json")

    loaded = load_packs(packs_dir)
    assert loaded.world_schema["version"] == "1.2.0"


def test_compile_world_pack_from_split_sources(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"

    _write_json(
        authoring_dir / "world_meta.json",
        {
            "schema_version": "world_schema.v1",
            "version": "2.0.0",
            "forbidden_terms": ["실명 주소"],
            "relation_conflict_rules": [
                {
                    "id": "WRC-TEST-001",
                    "relation_type_a": "allied_with",
                    "relation_type_b": "hostile_to",
                }
            ],
        },
    )
    _write_json(
        authoring_dir / "world_entities.json",
        [
            {
                "id": "WE-A",
                "entity_type": "org",
                "name": "기관 A",
                "summary": "테스트 엔티티 A",
                "source": "authoring",
                "valid_from": "Y001",
                "valid_to": "",
                "evidence_grade": "A",
            },
            {
                "id": "WE-B",
                "entity_type": "org",
                "name": "기관 B",
                "summary": "테스트 엔티티 B",
                "source": "authoring",
                "valid_from": "Y001",
                "valid_to": "",
                "evidence_grade": "A",
            },
        ],
    )
    _write_json(
        authoring_dir / "world_relations.json",
        [
            {
                "id": "WR-001",
                "relation_type": "allied_with",
                "from_entity_id": "WE-A",
                "to_entity_id": "WE-B",
                "source": "authoring",
                "valid_from": "Y010",
                "valid_to": "",
                "evidence_grade": "B",
            }
        ],
    )
    _write_json(
        authoring_dir / "world_timeline_events.json",
        [
            {
                "id": "WT-001",
                "title": "협정 체결",
                "summary": "기관 A/B 동맹",
                "era": "Y010",
                "entity_ids": ["WE-A", "WE-B"],
                "source": "authoring",
                "valid_from": "Y010",
                "valid_to": "",
                "evidence_grade": "B",
            }
        ],
    )
    _write_json(
        authoring_dir / "world_rules.json",
        [
            {
                "id": "WW-001",
                "name": "동맹 유지 조항",
                "category": "regulation",
                "description": "동맹을 깨는 행동 금지",
                "scope_entity_ids": ["WE-A", "WE-B"],
                "source": "authoring",
                "valid_from": "Y011",
                "valid_to": "",
                "evidence_grade": "B",
            }
        ],
    )
    _write_json(
        authoring_dir / "world_glossary.json",
        [
            {
                "id": "WG-001",
                "term": "연합",
                "definition": "기관 A/B 협력 상태",
                "aliases": ["동맹"],
                "source": "authoring",
                "valid_from": "Y010",
                "valid_to": "",
                "evidence_grade": "B",
            }
        ],
    )

    summary = compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)

    assert summary["source_mode"] == "split"
    assert summary["entities"] == 2
    assert summary["relations"] == 1
    assert summary["timeline_events"] == 1
    assert summary["world_rules"] == 1
    assert summary["glossary"] == 1

    compiled_world = _read_json(packs_dir / "world_pack.json")
    assert compiled_world["version"] == "2.0.0"
    assert compiled_world["forbidden_terms"] == ["실명 주소"]
    assert compiled_world["relation_conflict_rules"][0]["id"] == "WRC-TEST-001"

    load_packs(packs_dir)


def test_compile_world_pack_requires_authoring_source(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"
    authoring_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError) as exc:
        compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)

    assert "No world authoring source" in str(exc.value)


def test_compile_world_pack_from_world_master_schema(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"
    authoring_dir.mkdir(parents=True, exist_ok=True)

    world_master = {
        "schema_version": "world_master.v1",
        "version": "4.3.0",
        "forbidden_terms": ["실명 주소"],
        "relation_conflict_rules": [
            {
                "id": "WCR-MASTER-001",
                "relation_type_a": "allied_with",
                "relation_type_b": "hostile_to",
            }
        ],
        "nodes": [
            {
                "id": "WN-CHAR-001",
                "kind": "character",
                "name": "크리스티안",
                "summary": "주인공",
                "tags": ["protagonist", "noble"],
                "aliases": ["차남"],
                "linked_char_id": "",
                "source": "worldbible.v4.3",
                "valid_from": "Y160",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
                "attributes": {"house": "WN-FAMILY-001"},
            },
            {
                "id": "WN-FAMILY-001",
                "kind": "family",
                "name": "OO 백작가",
                "summary": "왕국 귀족 가문",
                "tags": ["noble", "crest_arcana"],
                "aliases": [],
                "source": "worldbible.v4.3",
                "valid_from": "Y0",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
                "attributes": {"rank": "count"},
            },
            {
                "id": "WN-SPECIES-ELF",
                "kind": "species",
                "name": "엘프",
                "summary": "이르민수를 수호하는 종족",
                "tags": ["species", "guardian"],
                "aliases": [],
                "source": "worldbible.v4.3",
                "valid_from": "Y0",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
                "attributes": {"lifespan_tier": "long"},
            },
        ],
        "edges": [
            {
                "id": "WE-HOUSE-001",
                "relation_type": "belongs_to_family",
                "from_id": "WN-CHAR-001",
                "to_id": "WN-FAMILY-001",
                "notes": "혈통 관계",
                "qualifiers": {"line": "secondary"},
                "source": "worldbible.v4.3",
                "valid_from": "Y160",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
            }
        ],
        "events": [
            {
                "id": "WV-AWAKEN-001",
                "title": "각성 사건",
                "summary": "주인공이 외부 기억을 자각",
                "era": "Y160",
                "participant_ids": ["WN-CHAR-001"],
                "location_id": "",
                "trigger_ids": [],
                "consequence_ids": ["WE-HOUSE-001"],
                "source": "worldbible.v4.3",
                "valid_from": "Y160",
                "valid_to": "",
                "evidence_grade": "B",
                "visibility": "META",
            }
        ],
        "rules": [
            {
                "id": "WRULE-001",
                "name": "문장비전 혈통잠금",
                "category": "magic-law",
                "description": "가문 혈통키가 없는 경우 문장비전 시전 불가",
                "scope_ids": ["WN-FAMILY-001"],
                "source": "worldbible.v4.3",
                "valid_from": "Y0",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
            }
        ],
        "glossary": [
            {
                "id": "WG-MASTER-001",
                "term": "문장비전",
                "definition": "혈통 잠금 학파",
                "aliases": ["Crest Arcana"],
                "source": "worldbible.v4.3",
                "valid_from": "Y0",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
            }
        ],
        "source_documents": [
            {
                "id": "SRC-WB-4.3",
                "title": "WorldBible v4.3",
                "source_type": "docx",
                "locator": "월드바이블/WorldBible_Pramisio_ArchivePlaza_v4_3_20260226_renamed.docx",
                "published_at": "2026-02-26",
                "trust_level": "A",
            }
        ],
        "claims": [
            {
                "id": "CLM-001",
                "subject_id": "WN-CHAR-001",
                "predicate": "awakens_with_external_memory",
                "object_id": "",
                "object_literal": "true",
                "evidence_source_ids": ["SRC-WB-4.3"],
                "confidence": 0.95,
                "source": "worldbible.v4.3",
                "valid_from": "Y160",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "META",
            }
        ],
        "taxonomy_terms": [
            {
                "id": "TAX-NODE-KIND-001",
                "taxonomy": "node_kind",
                "label": "character",
                "parent_id": "",
                "description": "개별 인물",
            }
        ],
    }
    _write_json(authoring_dir / "world_master.json", world_master)

    summary = compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)

    assert summary["source_mode"] == "master"
    compiled_world = _read_json(packs_dir / "world_pack.json")
    assert compiled_world["schema_version"] == "world_schema.v1"
    assert compiled_world["version"] == "4.3.0"
    assert any(row["id"] == "WN-SPECIES-ELF" for row in compiled_world["entities"])
    assert any(row["id"] == "WE-HOUSE-001" for row in compiled_world["relations"])
    assert "extensions" in compiled_world
    assert "world_master" in compiled_world["extensions"]
    assert compiled_world["extensions"]["world_master"]["schema_version"] == "world_master.v1"
    assert compiled_world["extensions"]["world_master"]["claims"]

    loaded = load_packs(packs_dir)
    assert loaded.world_schema["extensions"]["world_master"]["claims"]


def test_compile_world_pack_from_world_master_split_directory(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"
    split_dir = authoring_dir / "world_master"
    split_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        split_dir / "meta.json",
        {
            "schema_version": "world_master.v1",
            "version": "2.1.0",
            "forbidden_terms": ["실명 주소"],
            "relation_conflict_rules": [],
        },
    )
    _write_json(
        split_dir / "kind_registry.json",
        {
            "node_kinds": [
                {"kind": "character", "required_attributes": ["origin"]},
            ],
            "edge_kinds": [],
        },
    )
    _write_json(
        split_dir / "nodes.json",
        [
            {
                "id": "WN-CHAR-001",
                "kind": "character",
                "name": "분할 입력 주인공",
                "summary": "split source",
                "tags": [],
                "aliases": [],
                "attributes": {"origin": "split"},
                "source": "worldbible.v4.3",
                "valid_from": "Y150",
                "valid_to": "",
                "evidence_grade": "A",
                "visibility": "PUBLIC",
            }
        ],
    )

    summary = compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)

    assert summary["source_mode"] == "master_split"
    compiled_world = _read_json(packs_dir / "world_pack.json")
    assert compiled_world["version"] == "2.1.0"
    assert compiled_world["extensions"]["world_master"]["kind_registry"]["node_kinds"]

    # 동시 지원: split 입력 시 단일 파일 export도 동기화되어야 한다.
    single_path = authoring_dir / "world_master.json"
    assert single_path.exists()
    single_payload = _read_json(single_path)
    assert single_payload["version"] == "2.1.0"
    assert single_payload["nodes"][0]["name"] == "분할 입력 주인공"


def test_compile_world_pack_syncs_master_file_and_split_outputs(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"
    authoring_dir.mkdir(parents=True, exist_ok=True)

    master_payload = _minimal_world_master_payload()
    master_payload["version"] = "3.0.0"
    _write_json(authoring_dir / "world_master.json", master_payload)

    summary = compile_world_pack(authoring_dir=authoring_dir, packs_dir=packs_dir)
    assert summary["source_mode"] == "master"

    split_dir = authoring_dir / "world_master"
    assert split_dir.exists()
    assert (split_dir / "meta.json").exists()
    assert (split_dir / "nodes.json").exists()
    assert (split_dir / "kind_registry.json").exists()

    split_meta = _read_json(split_dir / "meta.json")
    assert split_meta["version"] == "3.0.0"
    split_nodes = _read_json(split_dir / "nodes.json")
    assert split_nodes[0]["id"] == "WN-CHAR-001"
