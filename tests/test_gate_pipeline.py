from project_dream.gate_pipeline import run_gates


def test_gate_pipeline_masks_pii_and_reports_rewrite():
    corpus = ["안전한 문장"]
    result = run_gates("내 연락처는 010-1234-5678", corpus=corpus)
    assert result["final_text"] != "내 연락처는 010-1234-5678"
    safety_gate = next(g for g in result["gates"] if g["gate_name"] == "safety")
    assert safety_gate["passed"] is False
    assert "warnings" in safety_gate
    assert any(code == "PII_PHONE" for code in safety_gate["warnings"])


def test_gate_pipeline_blocks_seed_forbidden_term():
    result = run_gates(
        "이 사건은 실명노출이 핵심이다",
        corpus=[],
        forbidden_terms=["실명노출"],
        sensitivity_tags=["privacy"],
    )
    safety_gate = next(g for g in result["gates"] if g["gate_name"] == "safety")
    assert safety_gate["passed"] is False
    assert any("SEED_FORBIDDEN_TERM:실명노출" == code for code in safety_gate["warnings"])
    assert any(item["rule_id"] == "RULE-PLZ-SAFE-03" for item in safety_gate["violations"])


def test_gate_pipeline_uses_pack_policy_for_taboo_words():
    custom_policy = {
        "safety": {
            "phone_pattern": r"01[0-9]-\d{3,4}-\d{4}",
            "taboo_words": ["절대금지어"],
            "rule_ids": {
                "pii_phone": "RULE-PLZ-SAFE-01",
                "taboo_term": "RULE-PLZ-SAFE-02",
                "seed_forbidden": "RULE-PLZ-SAFE-03",
            },
        },
        "lore": {
            "evidence_keywords": ["팩근거"],
            "context_keywords": ["판단"],
            "contradiction_term_groups": [],
            "rule_ids": {
                "evidence_missing": "RULE-PLZ-LORE-01",
                "consistency_conflict": "RULE-PLZ-LORE-02",
            },
        },
    }
    result = run_gates("실명 단어는 여기 있어도 통과", corpus=[], gate_policy=custom_policy)
    safety_gate = next(g for g in result["gates"] if g["gate_name"] == "safety")
    assert safety_gate["passed"] is True
    assert safety_gate["warnings"] == []

    blocked = run_gates("절대금지어 포함", corpus=[], gate_policy=custom_policy)
    blocked_gate = next(g for g in blocked["gates"] if g["gate_name"] == "safety")
    assert blocked_gate["passed"] is False
    assert any(code == "TABOO_TERM:절대금지어" for code in blocked_gate["warnings"])


def test_gate_pipeline_uses_pack_policy_for_similarity_rule_id():
    custom_policy = {
        "similarity": {
            "rule_ids": {
                "over_threshold": "RULE-CUSTOM-SIM-01",
            }
        }
    }

    result = run_gates(
        "같은 문장",
        corpus=["같은 문장"],
        similarity_threshold=85,
        gate_policy=custom_policy,
    )

    similarity_gate = next(g for g in result["gates"] if g["gate_name"] == "similarity")
    assert similarity_gate["passed"] is False
    assert any(item["rule_id"] == "RULE-CUSTOM-SIM-01" for item in similarity_gate["violations"])


def test_gate_pipeline_uses_pack_policy_for_claim_and_moderation_markers():
    custom_policy = {
        "lore": {
            "evidence_keywords": ["팩근거"],
            "context_keywords": [],
            "claim_markers": ["판결문구"],
            "moderation_keywords": ["중재봇"],
            "contradiction_term_groups": [],
            "rule_ids": {
                "evidence_missing": "RULE-PLZ-LORE-01",
                "consistency_conflict": "RULE-PLZ-LORE-02",
            },
        }
    }
    result = run_gates(
        "중재봇이 판결문구를 근거 없이 선언했다",
        corpus=[],
        gate_policy=custom_policy,
    )

    lore_gate = next(g for g in result["gates"] if g["gate_name"] == "lore")
    assert lore_gate["passed"] is False
    first_violation = lore_gate["violations"][0]
    assert "ENT-CLAIM" in first_violation.get("entity_refs", [])
    assert "ENT-MODERATION" in first_violation.get("entity_refs", [])
