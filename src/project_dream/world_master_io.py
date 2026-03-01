from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from project_dream.world_master_schema import validate_world_master_payload

WORLD_MASTER_SPLIT_DIR_NAME = "world_master"

_META_FILE = "meta.json"
_KIND_REGISTRY_FILE = "kind_registry.json"
_LIST_FILES = {
    "nodes": "nodes.json",
    "edges": "edges.json",
    "events": "events.json",
    "rules": "rules.json",
    "glossary": "glossary.json",
    "source_documents": "source_documents.json",
    "claims": "claims.json",
    "taxonomy_terms": "taxonomy_terms.json",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_dict(path: Path) -> dict:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def _read_list(path: Path) -> list:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON: {path}")
    return payload


def load_world_master_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = _read_dict(path)
    return validate_world_master_payload(payload)


def load_world_master_split_dir(split_dir: Path) -> dict | None:
    if not split_dir.exists() or not split_dir.is_dir():
        return None

    payload = {
        "schema_version": "world_master.v1",
        "version": "1.0.0",
        "forbidden_terms": [],
        "relation_conflict_rules": [],
        "kind_registry": {},
        "nodes": [],
        "edges": [],
        "events": [],
        "rules": [],
        "glossary": [],
        "source_documents": [],
        "claims": [],
        "taxonomy_terms": [],
    }
    has_any_source = False

    meta_path = split_dir / _META_FILE
    if meta_path.exists():
        has_any_source = True
        meta = _read_dict(meta_path)
        payload["schema_version"] = str(meta.get("schema_version", "world_master.v1"))
        payload["version"] = str(meta.get("version", "1.0.0"))
        payload["forbidden_terms"] = list(meta.get("forbidden_terms", []))
        payload["relation_conflict_rules"] = list(meta.get("relation_conflict_rules", []))

    kind_registry_path = split_dir / _KIND_REGISTRY_FILE
    if kind_registry_path.exists():
        has_any_source = True
        payload["kind_registry"] = _read_dict(kind_registry_path)

    for key, filename in _LIST_FILES.items():
        section_path = split_dir / filename
        if section_path.exists():
            has_any_source = True
            payload[key] = _read_list(section_path)

    if not has_any_source:
        return None
    return validate_world_master_payload(payload)


def write_world_master_file(payload: dict, path: Path) -> dict:
    canonical = validate_world_master_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")
    return canonical


def write_world_master_split_dir(payload: dict, split_dir: Path) -> dict:
    canonical = validate_world_master_payload(payload)
    split_dir.mkdir(parents=True, exist_ok=True)

    meta_payload = {
        "schema_version": str(canonical.get("schema_version", "world_master.v1")),
        "version": str(canonical.get("version", "1.0.0")),
        "forbidden_terms": list(canonical.get("forbidden_terms", [])),
        "relation_conflict_rules": list(canonical.get("relation_conflict_rules", [])),
    }
    (split_dir / _META_FILE).write_text(
        json.dumps(meta_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (split_dir / _KIND_REGISTRY_FILE).write_text(
        json.dumps(canonical.get("kind_registry", {}), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for key, filename in _LIST_FILES.items():
        section_payload = canonical.get(key, [])
        if not isinstance(section_payload, list):
            section_payload = []
        (split_dir / filename).write_text(
            json.dumps(section_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return canonical
