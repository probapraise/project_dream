from project_dream.models import SeedInput
from project_dream.prompt_templates import render_prompt


def generate_comment(seed: SeedInput, persona_id: str, round_idx: int) -> str:
    return render_prompt(
        "comment_generation",
        {
            "board_id": seed.board_id,
            "zone_id": seed.zone_id,
            "round_idx": round_idx,
            "persona_id": persona_id,
            "title": seed.title,
            "summary": seed.summary,
        },
    )
