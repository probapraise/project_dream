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
