from project_dream.gate_pipeline import run_gates


def test_gate_pipeline_masks_pii_and_reports_rewrite():
    corpus = ["안전한 문장"]
    result = run_gates("내 연락처는 010-1234-5678", corpus=corpus)
    assert result["final_text"] != "내 연락처는 010-1234-5678"
    assert any(not g["passed"] for g in result["gates"])
