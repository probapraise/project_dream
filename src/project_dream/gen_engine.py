from __future__ import annotations

import json
from collections.abc import Mapping

from project_dream.llm_client import LLMClient, build_default_llm_client
from project_dream.models import Dial, SeedInput
from project_dream.prompt_templates import render_prompt


_LAST_GENERATION_TRACE: dict | None = None


def _render_voice_hint(voice_constraints: dict | None) -> str:
    if not voice_constraints:
        return ""

    style = str(voice_constraints.get("sentence_length", "medium"))
    endings = voice_constraints.get("endings", [])
    endings_hint = "/".join(str(value) for value in endings[:2]) if isinstance(endings, list) else ""
    taboo_words = voice_constraints.get("taboo_words", [])
    taboo_count = len(taboo_words) if isinstance(taboo_words, list) else 0

    return f"voice=style:{style};endings:{endings_hint};taboo_count:{taboo_count}"


def _render_dial_hint(dial: Dial) -> str:
    return f"U{dial.U}-E{dial.E}-M{dial.M}-S{dial.S}-H{dial.H}"


def _render_csv(values: list[str] | None) -> str:
    if not values:
        return ""
    return ",".join(str(value) for value in values if str(value).strip())


def _default_intent_from_dial(dial: Dial) -> str:
    ranked = sorted(
        (
            ("alert", dial.U),
            ("evidence", dial.E),
            ("mediate", dial.M),
            ("safety", dial.S),
            ("hype", dial.H),
        ),
        key=lambda row: row[1],
        reverse=True,
    )
    return ranked[0][0]


def _coerce_stage1_payload(raw: str, *, seed: SeedInput) -> dict[str, str]:
    default_payload = {
        "claim": f"{seed.title} 관련 입장을 정리한다",
        "evidence": f"{seed.summary} 관련 자료를 확인한다",
        "intent": _default_intent_from_dial(seed.dial),
    }
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return default_payload

    if not isinstance(parsed, Mapping):
        return default_payload
    claim = str(parsed.get("claim", "")).strip()
    evidence = str(parsed.get("evidence", "")).strip()
    intent = str(parsed.get("intent", "")).strip()
    if not claim or not evidence or not intent:
        return default_payload
    return {
        "claim": claim,
        "evidence": evidence,
        "intent": intent,
    }


def reset_last_generation_trace() -> None:
    global _LAST_GENERATION_TRACE
    _LAST_GENERATION_TRACE = None


def pop_last_generation_trace() -> dict | None:
    global _LAST_GENERATION_TRACE
    trace = _LAST_GENERATION_TRACE
    _LAST_GENERATION_TRACE = None
    return trace


def _build_stage1(
    seed: SeedInput,
    persona_id: str,
    round_idx: int,
    *,
    client: LLMClient,
    template_set: str,
    memory_hint: str | None,
    template_context: Mapping[str, object] | None,
    flow_context: Mapping[str, object] | None,
) -> dict:
    selected_title_pattern = str((template_context or {}).get("title_pattern", "")).strip()
    trigger_tags = [str(tag) for tag in list((template_context or {}).get("trigger_tags", [])) if str(tag).strip()]
    template_taboos = [str(tag) for tag in list((template_context or {}).get("taboos", [])) if str(tag).strip()]
    body_sections = [str(tag) for tag in list((flow_context or {}).get("body_sections", [])) if str(tag).strip()]
    stage1_prompt = render_prompt(
        "comment_stage1_plan",
        {
            "board_id": seed.board_id,
            "zone_id": seed.zone_id,
            "round_idx": round_idx,
            "persona_id": persona_id,
            "title": seed.title,
            "summary": seed.summary,
            "memory_hint": memory_hint or "",
            "dial_hint": _render_dial_hint(seed.dial),
        },
        template_set=template_set,
    )
    stage1_prompt = (
        f"{stage1_prompt} | title_pattern={selected_title_pattern}"
        f" | trigger_tags={_render_csv(trigger_tags)}"
        f" | body_sections={_render_csv(body_sections)}"
        f" | template_taboos={_render_csv(template_taboos)}"
    )
    stage1_raw = client.generate(stage1_prompt, task="comment_stage1")
    payload = _coerce_stage1_payload(stage1_raw, seed=seed)
    return {
        **payload,
        "dial": _render_dial_hint(seed.dial),
        "title_pattern": selected_title_pattern,
        "trigger_tags": trigger_tags,
        "body_sections": body_sections,
        "template_taboos": template_taboos,
        "prompt": stage1_prompt,
        "raw": stage1_raw,
    }


def _build_stage2_prompt(
    seed: SeedInput,
    persona_id: str,
    round_idx: int,
    *,
    stage1: Mapping[str, object],
    template_set: str,
    memory_hint: str | None,
    voice_constraints: dict | None,
    template_context: Mapping[str, object] | None,
    flow_context: Mapping[str, object] | None,
) -> tuple[str, str]:
    trigger_tags = [str(tag) for tag in list((template_context or {}).get("trigger_tags", [])) if str(tag).strip()]
    template_taboos = [str(tag) for tag in list((template_context or {}).get("taboos", [])) if str(tag).strip()]
    body_sections = [str(tag) for tag in list((flow_context or {}).get("body_sections", [])) if str(tag).strip()]
    voice_hint = _render_voice_hint(voice_constraints)
    prompt = render_prompt(
        "comment_stage2_render",
        {
            "board_id": seed.board_id,
            "zone_id": seed.zone_id,
            "round_idx": round_idx,
            "persona_id": persona_id,
            "claim": stage1.get("claim", ""),
            "evidence": stage1.get("evidence", ""),
            "intent": stage1.get("intent", ""),
            "dial_hint": stage1.get("dial", _render_dial_hint(seed.dial)),
            "memory_hint": memory_hint or "",
            "voice_hint": voice_hint,
        },
        template_set=template_set,
    )
    prompt = (
        f"{prompt} | sections={_render_csv(body_sections)}"
        f" | triggers={_render_csv(trigger_tags)}"
        f" | taboos={_render_csv(template_taboos)}"
    )
    return prompt, voice_hint


def generate_comment(
    seed: SeedInput,
    persona_id: str,
    round_idx: int,
    llm_client: LLMClient | None = None,
    template_set: str = "v1",
    memory_hint: str | None = None,
    voice_constraints: dict | None = None,
    template_context: Mapping[str, object] | None = None,
    flow_context: Mapping[str, object] | None = None,
) -> str:
    global _LAST_GENERATION_TRACE
    _LAST_GENERATION_TRACE = None

    client = llm_client if llm_client is not None else build_default_llm_client()
    stage1 = _build_stage1(
        seed,
        persona_id,
        round_idx,
        client=client,
        template_set=template_set,
        memory_hint=memory_hint,
        template_context=template_context,
        flow_context=flow_context,
    )
    stage2_prompt, voice_hint = _build_stage2_prompt(
        seed,
        persona_id,
        round_idx,
        stage1=stage1,
        template_set=template_set,
        memory_hint=memory_hint,
        voice_constraints=voice_constraints,
        template_context=template_context,
        flow_context=flow_context,
    )
    final_text = client.generate(stage2_prompt, task="comment_generation")
    _LAST_GENERATION_TRACE = {
        "stage1": {
            "claim": stage1.get("claim", ""),
            "evidence": stage1.get("evidence", ""),
            "intent": stage1.get("intent", ""),
            "dial": stage1.get("dial", _render_dial_hint(seed.dial)),
            "title_pattern": stage1.get("title_pattern", ""),
            "trigger_tags": list(stage1.get("trigger_tags", [])),
            "body_sections": list(stage1.get("body_sections", [])),
            "template_taboos": list(stage1.get("template_taboos", [])),
        },
        "stage2": {
            "voice_hint": voice_hint,
            "prompt": stage2_prompt,
            "sections": list((flow_context or {}).get("body_sections", [])),
            "trigger_tags": list((template_context or {}).get("trigger_tags", [])),
        },
    }
    return final_text
