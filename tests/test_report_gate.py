from project_dream.report_gate import run_report_gate


def _valid_report() -> dict:
    return {
        "schema_version": "report.v1",
        "seed_id": "SEED-001",
        "title": "테스트",
        "summary": "요약",
        "lens_summaries": [
            {"community_id": "COM-PLZ-001", "summary": "a"},
            {"community_id": "COM-PLZ-002", "summary": "b"},
            {"community_id": "COM-PLZ-003", "summary": "c"},
            {"community_id": "COM-PLZ-004", "summary": "d"},
        ],
        "highlights_top10": [{"round": 1, "persona_id": "P1", "text": "x"}],
        "conflict_map": {
            "claim_a": "a",
            "claim_b": "b",
            "third_interest": "c",
            "mediation_points": ["m1"],
        },
        "dialogue_candidates": [
            {"speaker": "P1", "line": "l1"},
            {"speaker": "P2", "line": "l2"},
            {"speaker": "P3", "line": "l3"},
        ],
        "foreshadowing": ["f1"],
        "risk_checks": [{"category": "rule", "severity": "low", "details": "ok"}],
        "story_checklist": {
            "countdown_risk": {"label": "카운트다운", "status": "ok", "details": "expires_in_hours=48"},
            "evidence_grade": {"label": "증거 등급", "status": "ok", "details": "grade=B"},
            "board_migration_clue": {"label": "보드 이동", "status": "missing", "details": "board_ids=['B07']"},
            "meme": {"label": "밈", "status": "ok", "details": "meme_seed_id=MM-001"},
            "event_card": {"label": "이벤트", "status": "ok", "details": "event_card_id=EV-001"},
        },
    }


def test_run_report_gate_passes_for_valid_report():
    gate = run_report_gate(_valid_report())

    assert gate["schema_version"] == "report_gate.v1"
    assert gate["pass_fail"] is True
    assert gate["checks"]
    assert gate["failed_checks"] == []


def test_run_report_gate_fails_for_invalid_dialogue_and_risk_severity():
    report = _valid_report()
    report["dialogue_candidates"] = [{"speaker": "", "line": ""}]
    report["risk_checks"] = [{"category": "rule", "severity": "critical", "details": "bad"}]

    gate = run_report_gate(report)

    assert gate["pass_fail"] is False
    failed = {item["name"] for item in gate["failed_checks"]}
    assert "report.dialogue_count" in failed
    assert "report.dialogue_candidate_fields" in failed
    assert "report.risk_checks.severity_values" in failed


def test_run_report_gate_fails_when_story_checklist_missing():
    report = _valid_report()
    report.pop("story_checklist")

    gate = run_report_gate(report)

    assert gate["pass_fail"] is False
    failed = {item["name"] for item in gate["failed_checks"]}
    assert "report.story_checklist.required_items" in failed
