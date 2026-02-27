from project_dream.gate_pipeline import run_gates


def test_gate_pipeline_masks_pii_and_reports_rewrite():
    corpus = ["안전한 문장"]
    result = run_gates("내 연락처는 010-1234-5678", corpus=corpus)
    assert result["final_text"] != "내 연락처는 010-1234-5678"
    safety_gate = next(g for g in result["gates"] if g["gate_name"] == "safety")
    assert safety_gate["passed"] is False
    assert "warnings" in safety_gate
    assert any(code == "PII_PHONE" for code in safety_gate["warnings"])
