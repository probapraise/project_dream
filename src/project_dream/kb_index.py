from __future__ import annotations

import re
from typing import Any

from project_dream.pack_service import LoadedPacks


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[0-9A-Za-z가-힣_]+", text.lower()))


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_stringify(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_stringify(v) for v in value.values())
    return str(value)


def _build_text(item: dict, *, fields: list[str]) -> str:
    values = [_stringify(item.get(field)) for field in fields]
    return " ".join(value for value in values if value).strip()


def _matches_filters(row: dict, filters: dict[str, Any]) -> bool:
    for key, expected in filters.items():
        if expected is None:
            continue
        actual = row.get(key)
        if isinstance(expected, (list, tuple, set)):
            expected_set = set(expected)
            if isinstance(actual, list):
                if not expected_set.intersection(actual):
                    return False
            elif actual not in expected_set:
                return False
            continue
        if isinstance(actual, list):
            if expected not in actual:
                return False
            continue
        if actual != expected:
            return False
    return True


def _score(query: str, text: str) -> int:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0
    text_tokens = _tokenize(text)
    overlap = len(query_tokens.intersection(text_tokens))
    phrase_bonus = 2 if query and query.lower() in text.lower() else 0
    return overlap + phrase_bonus


def build_index(packs: LoadedPacks) -> dict[str, Any]:
    passages: list[dict] = []
    communities = packs.communities

    for board in packs.boards.values():
        passages.append(
            {
                "kind": "board",
                "item_id": board["id"],
                "board_id": board["id"],
                "zone_id": None,
                "text": _build_text(
                    board,
                    fields=["id", "name", "topic", "emotion", "taboos", "memes"],
                ),
            }
        )

    for community in communities.values():
        passages.append(
            {
                "kind": "community",
                "item_id": community["id"],
                "board_id": community.get("board_id"),
                "zone_id": community.get("zone_id"),
                "text": _build_text(
                    community,
                    fields=[
                        "id",
                        "name",
                        "identity",
                        "preferred_evidence",
                        "taboos",
                        "biases",
                    ],
                ),
            }
        )

    for rule in packs.rules.values():
        passages.append(
            {
                "kind": "rule",
                "item_id": rule["id"],
                "board_id": None,
                "zone_id": None,
                "type": rule.get("category"),
                "text": _build_text(rule, fields=["id", "name", "category", "summary"]),
            }
        )

    for org in packs.orgs.values():
        passages.append(
            {
                "kind": "organization",
                "item_id": org["id"],
                "board_id": None,
                "zone_id": None,
                "text": _build_text(org, fields=["id", "name", "tags"]),
            }
        )

    for char in packs.chars.values():
        community = communities.get(char.get("main_com", ""))
        passages.append(
            {
                "kind": "character",
                "item_id": char["id"],
                "board_id": community.get("board_id") if community else None,
                "zone_id": community.get("zone_id") if community else None,
                "text": _build_text(
                    char,
                    fields=["id", "name", "affiliations", "main_com"],
                ),
            }
        )

    for persona in packs.personas.values():
        community = communities.get(persona.get("main_com", ""))
        passages.append(
            {
                "kind": "persona",
                "item_id": persona["id"],
                "persona_id": persona["id"],
                "board_id": community.get("board_id") if community else None,
                "zone_id": community.get("zone_id") if community else None,
                "text": _build_text(
                    persona,
                    fields=["id", "char_id", "archetype_id", "main_com"],
                ),
            }
        )

    for template in packs.thread_templates.values():
        passages.append(
            {
                "kind": "thread_template",
                "item_id": template["id"],
                "board_id": template.get("intended_boards", []),
                "zone_id": None,
                "text": _build_text(
                    template,
                    fields=[
                        "id",
                        "name",
                        "intended_boards",
                        "default_comment_flow",
                        "crosspost_routes",
                    ],
                ),
            }
        )

    return {"passages": passages, "packs": packs}


def search(
    index: dict[str, Any],
    query: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
) -> list[dict]:
    if top_k <= 0:
        return []
    filters = filters or {}
    passages = index.get("passages", [])
    matched = [row for row in passages if _matches_filters(row, filters)]

    scored: list[tuple[int, dict]] = [(_score(query, row["text"]), row) for row in matched]
    scored.sort(key=lambda item: (-item[0], item[1]["kind"], item[1]["item_id"]))

    results: list[dict] = []
    for score, row in scored[:top_k]:
        copied = dict(row)
        copied["score"] = score
        results.append(copied)
    return results


def get_pack_item(index: dict[str, Any], pack: str, item_id: str) -> dict | None:
    packs: LoadedPacks = index["packs"]
    registry = {
        "board": packs.boards,
        "community": packs.communities,
        "rule": packs.rules,
        "organization": packs.orgs,
        "character": packs.chars,
        "persona": packs.personas,
        "thread_template": packs.thread_templates,
        "comment_flow": packs.comment_flows,
    }
    source = registry.get(pack)
    if source is None:
        raise ValueError(f"Unknown pack type: {pack}")
    return source.get(item_id)


def _merge_unique_rows(rows: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    merged: list[dict] = []
    for row in rows:
        key = (row.get("kind", ""), row.get("item_id", ""))
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged


def retrieve_context(
    index: dict[str, Any],
    *,
    task: str,
    seed: str,
    board_id: str,
    zone_id: str,
    persona_ids: list[str] | None,
    top_k: int = 3,
) -> dict[str, Any]:
    persona_ids = persona_ids or []

    evidence = search(
        index,
        query=f"{task} {seed} 증거 로그 출처 근거",
        filters={"kind": ["board", "community", "persona"], "board_id": board_id},
        top_k=top_k,
    )
    policy = search(
        index,
        query=f"{task} 규정 제재 신고 룰",
        filters={"kind": "rule"},
        top_k=top_k,
    )
    organization = search(
        index,
        query=f"{task} 조직 세력 운영 감찰",
        filters={"kind": ["organization", "character"]},
        top_k=top_k,
    )
    hierarchy = search(
        index,
        query=f"{task} 페르소나 계층 관계",
        filters={"kind": "persona", "zone_id": zone_id},
        top_k=top_k,
    )

    persona_rows: list[dict] = []
    for persona_id in persona_ids:
        persona_rows.extend(
            search(
                index,
                query=persona_id,
                filters={"kind": "persona", "item_id": persona_id},
                top_k=1,
            )
        )
    if persona_rows:
        hierarchy = _merge_unique_rows(persona_rows + hierarchy)[:top_k]

    sections = {
        "evidence": evidence,
        "policy": policy,
        "organization": organization,
        "hierarchy": hierarchy,
    }

    corpus: list[str] = []
    seen_text: set[str] = set()
    for rows in sections.values():
        for row in rows:
            text = row["text"]
            if text in seen_text:
                continue
            seen_text.add(text)
            corpus.append(text)

    bundle = {
        "task": task,
        "seed": seed,
        "board_id": board_id,
        "zone_id": zone_id,
        "persona_ids": persona_ids,
        "sections": sections,
    }
    return {"bundle": bundle, "corpus": corpus}
