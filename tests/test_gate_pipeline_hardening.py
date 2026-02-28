from project_dream.gate_pipeline import run_gates


def test_similarity_gate_reports_top_k_metadata():
    result = run_gates(
        "같은 문장",
        corpus=["같은 문장", "같은 문장 비슷", "완전 다른 문장"],
        similarity_threshold=85,
    )

    similarity_gate = next(g for g in result["gates"] if g["gate_name"] == "similarity")
    assert similarity_gate["passed"] is False
    assert "top_k" in similarity_gate
    assert len(similarity_gate["top_k"]) >= 1
    assert similarity_gate["top_k"][0]["score"] >= 85


def test_lore_gate_adds_checklist_and_fails_without_evidence():
    result = run_gates("그냥 느낌만 말함", corpus=[])

    lore_gate = next(g for g in result["gates"] if g["gate_name"] == "lore")
    assert lore_gate["passed"] is False
    assert "checklist" in lore_gate
    assert lore_gate["checklist"]["evidence_keyword_found"] is False


def test_lore_gate_passes_when_evidence_keyword_present():
    result = run_gates("정본 기준으로 보면 이 주장은 근거가 약함", corpus=[])

    lore_gate = next(g for g in result["gates"] if g["gate_name"] == "lore")
    assert lore_gate["passed"] is True
    assert lore_gate["checklist"]["evidence_keyword_found"] is True


def test_safety_gate_emits_rule_id_violation_details():
    result = run_gates("실명 유출: 010-1234-5678", corpus=[])

    safety_gate = next(g for g in result["gates"] if g["gate_name"] == "safety")
    assert safety_gate["passed"] is False
    assert "violations" in safety_gate
    rule_ids = {item["rule_id"] for item in safety_gate["violations"]}
    assert "RULE-PLZ-SAFE-01" in rule_ids
    assert "RULE-PLZ-SAFE-02" in rule_ids
    assert any("ENT-CONTACT" in item.get("entity_refs", []) for item in safety_gate["violations"])


def test_lore_gate_emits_rule_id_when_evidence_missing():
    result = run_gates("그냥 느낌만 말함", corpus=[])

    lore_gate = next(g for g in result["gates"] if g["gate_name"] == "lore")
    assert lore_gate["passed"] is False
    assert "violations" in lore_gate
    assert any(item["rule_id"] == "RULE-PLZ-LORE-01" for item in lore_gate["violations"])


def test_lore_consistency_checker_detects_contradiction_and_entity_refs():
    text = "정본 근거로 확정이라고 했지만 아직 추정 단계라는 주장도 있다"
    result = run_gates(text, corpus=[])

    lore_gate = next(g for g in result["gates"] if g["gate_name"] == "lore")
    assert lore_gate["passed"] is False
    consistency = lore_gate.get("consistency", {})
    assert consistency.get("passed") is False
    assert "issues" in consistency
    assert any(item["rule_id"] == "RULE-PLZ-LORE-02" for item in consistency["issues"])
    assert any("ENT-CLAIM" in item.get("entity_refs", []) for item in consistency["issues"])


def test_run_gates_emits_aggregate_violations():
    result = run_gates("실명 유출: 010-1234-5678 / 그냥 느낌만 말함", corpus=["실명 유출: 010-1234-5678"])

    assert "violations" in result
    assert len(result["violations"]) >= 3
    all_rule_ids = {item["rule_id"] for item in result["violations"]}
    assert "RULE-PLZ-SAFE-01" in all_rule_ids
    assert "RULE-PLZ-LORE-01" in all_rule_ids
