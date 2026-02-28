from project_dream.llm_client import LLMClient, build_default_llm_client
from project_dream.models import SeedInput
from project_dream.prompt_templates import render_prompt


def _render_voice_hint(voice_constraints: dict | None) -> str:
    if not voice_constraints:
        return ""

    style = str(voice_constraints.get("sentence_length", "medium"))
    endings = voice_constraints.get("endings", [])
    endings_hint = "/".join(str(value) for value in endings[:2]) if isinstance(endings, list) else ""
    taboo_words = voice_constraints.get("taboo_words", [])
    taboo_count = len(taboo_words) if isinstance(taboo_words, list) else 0

    return f"voice=style:{style};endings:{endings_hint};taboo_count:{taboo_count}"


def generate_comment(
    seed: SeedInput,
    persona_id: str,
    round_idx: int,
    llm_client: LLMClient | None = None,
    template_set: str = "v1",
    memory_hint: str | None = None,
    voice_constraints: dict | None = None,
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
    if memory_hint:
        prompt = f"{prompt} | memory={memory_hint}"
    voice_hint = _render_voice_hint(voice_constraints)
    if voice_hint:
        prompt = f"{prompt} | {voice_hint}"
    client = llm_client if llm_client is not None else build_default_llm_client()
    return client.generate(prompt, task="comment_generation")
