import json
import shutil
from pathlib import Path

import pytest

from project_dream.pack_service import load_packs


def _copy_packs(tmp_path: Path) -> Path:
    dst = tmp_path / "packs"
    shutil.copytree(Path("packs"), dst)
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
