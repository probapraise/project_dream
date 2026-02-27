from project_dream.llm_client import EchoLLMClient, LLMClient
from project_dream.models import SeedInput
from project_dream.prompt_templates import render_prompt


def generate_comment(
    seed: SeedInput,
    persona_id: str,
    round_idx: int,
    llm_client: LLMClient | None = None,
    template_set: str = "v1",
) -> str:
    prompt = render_prompt(
        "comment_generation",
        {
            "board_id": seed.board_id,
            "zone_id": seed.zone_id,
            "round_idx": round_idx,
            "persona_id": persona_id,
            "title": seed.title,
            "summary": seed.summary,
        },
        template_set=template_set,
    )
    client = llm_client if llm_client is not None else EchoLLMClient()
    return client.generate(prompt, task="comment_generation")
