import json
import shutil
from pathlib import Path

import pytest

from project_dream.pack_service import load_packs


def _copy_packs(tmp_path: Path) -> Path:
    dst = tmp_path / "packs"
    shutil.copytree(Path("packs"), dst)
    manifest_path = dst / "pack_manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()
    return dst


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_packs_rejects_non_list_trigger_tags(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    template_path = packs_dir / "template_pack.json"
    payload = _read_json(template_path)
    payload["thread_templates"][0]["trigger_tags"] = "not-a-list"
    _write_json(template_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "trigger_tags" in str(exc.value)


def test_load_packs_rejects_invalid_escalation_condition_type(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    template_path = packs_dir / "template_pack.json"
    payload = _read_json(template_path)
    payload["comment_flows"][0]["escalation_rules"] = [
        {
            "condition": "reports>=10",
            "action_type": "FLOW_ESCALATE_REVIEW",
            "reason_rule_id": "RULE-PLZ-MOD-01",
        }
    ]
    _write_json(template_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "condition" in str(exc.value)


def test_load_packs_rejects_unknown_extra_fields(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    board_path = packs_dir / "board_pack.json"
    payload = _read_json(board_path)
    payload["boards"][0]["unexpected_extra"] = "x"
    _write_json(board_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "unexpected_extra" in str(exc.value)


def test_load_packs_rejects_non_string_board_id(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    community_path = packs_dir / "community_pack.json"
    payload = _read_json(community_path)
    payload["communities"][0]["board_id"] = 101
    _write_json(community_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "board_id" in str(exc.value)


def test_load_packs_rejects_invalid_gate_policy_keyword_type(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    rule_path = packs_dir / "rule_pack.json"
    payload = _read_json(rule_path)
    payload["gate_policy"] = {
        "safety": {
            "taboo_words": ["실명"],
            "phone_pattern": r"01[0-9]-\d{3,4}-\d{4}",
            "rule_ids": {
                "pii_phone": "RULE-PLZ-SAFE-01",
                "taboo_term": "RULE-PLZ-SAFE-02",
                "seed_forbidden": "RULE-PLZ-SAFE-03",
            },
        },
        "lore": {
            "evidence_keywords": "not-a-list",
            "context_keywords": ["주장"],
            "contradiction_term_groups": [],
            "rule_ids": {
                "evidence_missing": "RULE-PLZ-LORE-01",
                "consistency_conflict": "RULE-PLZ-LORE-02",
            },
        },
    }
    _write_json(rule_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "evidence_keywords" in str(exc.value)


def test_load_packs_rejects_invalid_gate_policy_similarity_rule_id_type(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    rule_path = packs_dir / "rule_pack.json"
    payload = _read_json(rule_path)
    payload["gate_policy"]["similarity"] = {
        "rule_ids": {
            "over_threshold": 101,
        }
    }
    _write_json(rule_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "over_threshold" in str(exc.value)


def test_load_packs_rejects_manifest_checksum_mismatch(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    manifest_path = packs_dir / "pack_manifest.json"
    manifest_payload = {
        "schema_version": "pack_manifest.v1",
        "pack_version": "1.0.0",
        "checksum_algorithm": "sha256",
        "files": {
            "board_pack.json": "deadbeef",
            "community_pack.json": "deadbeef",
            "rule_pack.json": "deadbeef",
            "entity_pack.json": "deadbeef",
            "persona_pack.json": "deadbeef",
            "template_pack.json": "deadbeef",
        },
    }
    _write_json(manifest_path, manifest_payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "checksum mismatch" in str(exc.value)


def test_load_packs_rejects_unknown_register_profile_reference(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    persona_path = packs_dir / "persona_pack.json"
    payload = _read_json(persona_path)
    payload["register_profiles"] = [
        {
            "id": "REG-BASE",
            "sentence_length": "medium",
            "endings": ["입니다"],
            "frequent_words": ["정리"],
        }
    ]
    for archetype in payload.get("archetypes", []):
        if isinstance(archetype, dict):
            archetype["default_register_profile_id"] = "REG-BASE"
    payload["register_switch_rules"] = [
        {
            "id": "RR-UNKNOWN",
            "priority": 10,
            "apply_profile_id": "REG-NOT-FOUND",
            "conditions": {"dial_axis_in": ["H"]},
        }
    ]
    _write_json(persona_path, payload)

    with pytest.raises(ValueError) as exc:
        load_packs(packs_dir)

    assert "Unknown register_profile_id" in str(exc.value)
