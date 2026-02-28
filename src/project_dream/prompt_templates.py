from collections.abc import Mapping


PROMPT_TEMPLATE_REGISTRY: dict[str, dict[str, str]] = {
    "v1": {
        "thread_generation": (
            "[THREAD] board={board_id} zone={zone_id} title={title} summary={summary}"
        ),
        "comment_generation": (
            "[{board_id}/{zone_id}] R{round_idx} {persona_id}: {title}에 대한 반응 - {summary}"
        ),
        "comment_stage1_plan": (
            "[STAGE1] board={board_id} zone={zone_id} round={round_idx} persona={persona_id} "
            "title={title} summary={summary} memory={memory_hint} dial={dial_hint}"
        ),
        "comment_stage2_render": (
            "[{board_id}/{zone_id}] R{round_idx} {persona_id}: "
            "claim={claim} | evidence={evidence} | intent={intent} | dial={dial_hint}"
            " | memory={memory_hint} | {voice_hint}"
        ),
        "report_summary": "{title} / 라운드 {round_count}",
        "report_dialogue_candidate": "{text}",
        "validation_lore": "requires evidence context",
    }
}


def render_prompt(
    template_key: str,
    variables: Mapping[str, object] | None = None,
    template_set: str = "v1",
) -> str:
    templates = PROMPT_TEMPLATE_REGISTRY.get(template_set)
    if templates is None:
        raise ValueError(f"Unknown template_set: {template_set}")

    template = templates.get(template_key)
    if template is None:
        raise ValueError(f"Unknown template key: {template_key}")

    params = dict(variables or {})
    try:
        return template.format(**params)
    except KeyError as exc:
        raise ValueError(f"Missing template variable: {exc.args[0]}") from exc
