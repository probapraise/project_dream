from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from project_dream.pack_schemas import WorldPackPayload, validate_pack_payload
from project_dream.pack_service import write_pack_manifest
from project_dream.world_master_schema import project_world_master_to_world_pack

_WORLD_MONOLITHIC_FILE = "world_pack.json"
_WORLD_MASTER_FILE = "world_master.json"
_WORLD_META_FILE = "world_meta.json"
_WORLD_SPLIT_FILES = {
    "entities": "world_entities.json",
    "relations": "world_relations.json",
    "timeline_events": "world_timeline_events.json",
    "world_rules": "world_rules.json",
    "glossary": "world_glossary.json",
}
_WORLD_OPTIONAL_SPLIT_FILES = {
    "forbidden_terms": "world_forbidden_terms.json",
    "relation_conflict_rules": "world_relation_conflict_rules.json",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_dict_or_empty(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def _read_list_or_empty(path: Path) -> list:
    if not path.exists():
        return []
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON: {path}")
    return payload


def _load_monolithic(authoring_dir: Path) -> tuple[str, dict] | None:
    source_path = authoring_dir / _WORLD_MONOLITHIC_FILE
    if not source_path.exists():
        return None
    payload = _read_json(source_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {source_path}")
    return "monolithic", payload


def _load_world_master(authoring_dir: Path) -> tuple[str, dict] | None:
    source_path = authoring_dir / _WORLD_MASTER_FILE
    if not source_path.exists():
        return None
    payload = _read_json(source_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {source_path}")
    return "master", project_world_master_to_world_pack(payload)


def _load_split(authoring_dir: Path) -> tuple[str, dict] | None:
    meta = _read_dict_or_empty(authoring_dir / _WORLD_META_FILE)
    payload = {
        "schema_version": str(meta.get("schema_version", "world_schema.v1")),
        "version": str(meta.get("version", "1.0.0")),
        "forbidden_terms": list(meta.get("forbidden_terms", [])),
        "relation_conflict_rules": list(meta.get("relation_conflict_rules", [])),
        "entities": [],
        "relations": [],
        "timeline_events": [],
        "world_rules": [],
        "glossary": [],
    }

    has_any_source = False
    for key, filename in _WORLD_SPLIT_FILES.items():
        section_path = authoring_dir / filename
        if section_path.exists():
            has_any_source = True
        payload[key] = _read_list_or_empty(section_path)

    for key, filename in _WORLD_OPTIONAL_SPLIT_FILES.items():
        section_path = authoring_dir / filename
        if section_path.exists():
            has_any_source = True
            payload[key] = _read_list_or_empty(section_path)

    if (authoring_dir / _WORLD_META_FILE).exists():
        has_any_source = True

    if not has_any_source:
        return None
    return "split", payload


def _load_world_authoring(authoring_dir: Path) -> tuple[str, dict]:
    master = _load_world_master(authoring_dir)
    if master is not None:
        return master
    monolithic = _load_monolithic(authoring_dir)
    if monolithic is not None:
        return monolithic
    split = _load_split(authoring_dir)
    if split is not None:
        return split
    raise ValueError(
        "No world authoring source found. Provide authoring/world_pack.json "
        "or authoring/world_master.json or split files (world_meta.json + world_*.json)."
    )


def compile_world_pack(*, authoring_dir: Path, packs_dir: Path) -> dict:
    source_mode, world_payload = _load_world_authoring(authoring_dir)
    compiled_world = validate_pack_payload(world_payload, WorldPackPayload, "authoring world pack")

    packs_dir.mkdir(parents=True, exist_ok=True)
    world_pack_path = packs_dir / "world_pack.json"
    world_pack_path.write_text(
        json.dumps(compiled_world, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest = write_pack_manifest(packs_dir)

    return {
        "schema_version": "world_compile.v1",
        "source_mode": source_mode,
        "authoring_dir": str(authoring_dir),
        "packs_dir": str(packs_dir),
        "world_pack_path": str(world_pack_path),
        "pack_manifest_path": str(packs_dir / "pack_manifest.json"),
        "pack_manifest": manifest,
        "entities": len(compiled_world.get("entities", [])),
        "relations": len(compiled_world.get("relations", [])),
        "timeline_events": len(compiled_world.get("timeline_events", [])),
        "world_rules": len(compiled_world.get("world_rules", [])),
        "glossary": len(compiled_world.get("glossary", [])),
    }
