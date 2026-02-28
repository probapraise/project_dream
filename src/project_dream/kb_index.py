from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from project_dream.data_ingest import load_corpus_rows
from project_dream.pack_service import LoadedPacks


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[0-9A-Za-z가-힣_]+", text.lower())


def _term_freq(tokens: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _normalize_dense_text(text: str) -> str:
    return "".join(_tokenize(text))


def _char_ngrams(text: str, n: int = 2) -> dict[str, float]:
    normalized = _normalize_dense_text(text)
    if not normalized:
        return {}
    if len(normalized) <= n:
        return {normalized: 1.0}
    counts: dict[str, float] = {}
    for idx in range(0, len(normalized) - n + 1):
        gram = normalized[idx : idx + n]
        counts[gram] = counts.get(gram, 0.0) + 1.0
    return counts


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a.keys()).intersection(b.keys())
    if not common:
        return 0.0
    dot = sum(a[key] * b[key] for key in common)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


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


def _bm25_score(
    query_tokens: list[str],
    *,
    doc_tf: dict[str, int],
    doc_len: int,
    df: dict[str, int],
    doc_count: int,
    avg_doc_len: float,
    k1: float = 1.2,
    b: float = 0.75,
) -> float:
    if not query_tokens or doc_count <= 0:
        return 0.0
    score = 0.0
    unique_query_tokens = set(query_tokens)
    for term in unique_query_tokens:
        tf = doc_tf.get(term, 0)
        if tf <= 0:
            continue
        term_df = df.get(term, 0)
        idf = math.log(1.0 + ((doc_count - term_df + 0.5) / (term_df + 0.5)))
        denom = tf + (k1 * (1 - b + (b * (doc_len / max(avg_doc_len, 1e-9)))))
        score += idf * ((tf * (k1 + 1.0)) / max(denom, 1e-9))
    return float(score)


def _score_components(
    query: str,
    row: dict,
    *,
    df: dict[str, int],
    doc_count: int,
    avg_doc_len: float,
) -> tuple[float, float, float]:
    query_tokens = _tokenize(query)
    sparse = _bm25_score(
        query_tokens,
        doc_tf=row.get("_token_tf", {}),
        doc_len=int(row.get("_doc_len", 0)),
        df=df,
        doc_count=doc_count,
        avg_doc_len=avg_doc_len,
    )
    dense = _cosine_similarity(_char_ngrams(query, n=2), row.get("_dense_vector", {}))
    phrase_bonus = 0.15 if _normalize_dense_text(query) in str(row.get("_normalized_text", "")) else 0.0
    sparse_norm = 1.0 - math.exp(-max(0.0, sparse))
    hybrid = (0.65 * sparse_norm) + (0.35 * dense) + phrase_bonus
    return sparse, dense, hybrid


def build_index(packs: LoadedPacks, corpus_dir: Path | None = None) -> dict[str, Any]:
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
                        "title_patterns",
                        "trigger_tags",
                        "taboos",
                    ],
                ),
            }
        )

    if corpus_dir is not None:
        corpus_rows = load_corpus_rows(corpus_dir)
        for idx, row in enumerate(corpus_rows):
            text = str(row.get("text", "")).strip()
            if not text:
                continue
            item_id = str(row.get("doc_id", "")).strip() or f"corpus-{idx+1:06d}"
            passages.append(
                {
                    "kind": "corpus",
                    "item_id": item_id,
                    "board_id": row.get("board_id"),
                    "zone_id": row.get("zone_id"),
                    "source_type": row.get("source_type"),
                    "doc_type": row.get("doc_type"),
                    "text": text,
                }
            )

    df: dict[str, int] = {}
    total_doc_len = 0
    for row in passages:
        text = str(row.get("text", ""))
        tokens = _tokenize(text)
        token_tf = _term_freq(tokens)
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] = df.get(token, 0) + 1
        doc_len = len(tokens)
        total_doc_len += doc_len
        row["_tokens"] = tokens
        row["_token_tf"] = token_tf
        row["_doc_len"] = doc_len
        row["_normalized_text"] = _normalize_dense_text(text)
        row["_dense_vector"] = _char_ngrams(text, n=2)

    doc_count = len(passages)
    avg_doc_len = (total_doc_len / doc_count) if doc_count > 0 else 0.0
    return {
        "passages": passages,
        "packs": packs,
        "stats": {
            "df": df,
            "doc_count": doc_count,
            "avg_doc_len": avg_doc_len,
        },
    }


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
    stats = index.get("stats", {})
    df: dict[str, int] = stats.get("df", {})
    doc_count: int = int(stats.get("doc_count", len(passages)))
    avg_doc_len: float = float(stats.get("avg_doc_len", 0.0))
    matched = [row for row in passages if _matches_filters(row, filters)]

    scored: list[tuple[float, float, float, dict]] = []
    for row in matched:
        sparse, dense, hybrid = _score_components(
            query,
            row,
            df=df,
            doc_count=doc_count,
            avg_doc_len=avg_doc_len,
        )
        scored.append((hybrid, sparse, dense, row))
    scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]["kind"], item[3]["item_id"]))

    results: list[dict] = []
    for hybrid, sparse, dense, row in scored[:top_k]:
        copied = {key: value for key, value in row.items() if not str(key).startswith("_")}
        copied["score"] = float(round(hybrid, 6))
        copied["score_hybrid"] = float(round(hybrid, 6))
        copied["score_sparse"] = float(round(sparse, 6))
        copied["score_dense"] = float(round(dense, 6))
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
        filters={"kind": ["board", "community", "persona", "corpus"], "board_id": board_id},
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
