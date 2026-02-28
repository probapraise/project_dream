import pytest

from project_dream.prompt_templates import render_prompt


def test_render_prompt_comment_generation_v1():
    rendered = render_prompt(
        "comment_generation",
        {
            "board_id": "B01",
            "zone_id": "A",
            "round_idx": 1,
            "persona_id": "P-001",
            "title": "사건",
            "summary": "요약",
        },
        template_set="v1",
    )
    assert rendered == "[B01/A] R1 P-001: 사건에 대한 반응 - 요약"


def test_render_prompt_comment_stage1_plan_v1():
    rendered = render_prompt(
        "comment_stage1_plan",
        {
            "board_id": "B07",
            "zone_id": "D",
            "round_idx": 2,
            "persona_id": "P-777",
            "title": "중계망 먹통 사건",
            "summary": "장터기둥 게시판 접속 장애",
            "memory_hint": "R1: 증거 링크 요구",
            "dial_hint": "U30-E25-M15-S15-H15",
        },
        template_set="v1",
    )
    assert "board=B07 zone=D round=2 persona=P-777" in rendered
    assert "dial=U30-E25-M15-S15-H15" in rendered


def test_render_prompt_comment_stage2_render_v1():
    rendered = render_prompt(
        "comment_stage2_render",
        {
            "board_id": "B07",
            "zone_id": "D",
            "round_idx": 2,
            "persona_id": "P-777",
            "claim": "운영 공지 누락",
            "evidence": "로그 캡처",
            "intent": "mediate",
            "dial_hint": "U30-E25-M15-S15-H15",
            "memory_hint": "R1: 링크 요구",
            "voice_hint": "voice=style:short;endings:임/각;taboo_count:2",
        },
        template_set="v1",
    )
    assert "claim=운영 공지 누락" in rendered
    assert "evidence=로그 캡처" in rendered
    assert "intent=mediate" in rendered


def test_render_prompt_raises_on_unknown_template_set():
    with pytest.raises(ValueError):
        render_prompt("comment_generation", {}, template_set="v99")


def test_render_prompt_raises_on_unknown_template_key():
    with pytest.raises(ValueError):
        render_prompt("unknown_key", {}, template_set="v1")
