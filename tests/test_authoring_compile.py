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
