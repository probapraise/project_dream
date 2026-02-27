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


def test_render_prompt_raises_on_unknown_template_set():
    with pytest.raises(ValueError):
        render_prompt("comment_generation", {}, template_set="v99")


def test_render_prompt_raises_on_unknown_template_key():
    with pytest.raises(ValueError):
        render_prompt("unknown_key", {}, template_set="v1")
