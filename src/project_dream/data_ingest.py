from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from project_dream.pack_service import LoadedPacks, load_packs


DEFAULT_DIAL = {"U": 30, "E": 25, "M": 15, "S": 15, "H": 15}


def _template_for_board(packs: LoadedPacks, board_id: str) -> tuple[str, str]:
    for template in sorted(packs.thread_templates.values(), key=lambda row: row["id"]):
        if board_id in template.get("intended_boards", []):
            return template["id"], template.get("default_comment_flow", "P1")
    return "T1", "P1"


def _community_by_board(packs: LoadedPacks) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for community in sorted(packs.communities.values(), key=lambda row: row["id"]):
        board_id = str(community.get("board_id", ""))
        if not board_id:
            continue
        out.setdefault(board_id, community)
    return out


def _base_row(
    *,
    board_id: str,
    zone_id: str,
    source_type: str,
    doc_id: str,
    thread_id: str,
    parent_id: str,
    thread_template_id: str,
    comment_flow_id: str,
    persona_archetype_id: str,
    topic_tags: list[str],
    style_tags: list[str],
    text: str,
    notes: str,
) -> dict:
    return {
        "zone_id": zone_id,
        "board_id": board_id,
        "source_type": source_type,
        "doc_type": "post",
        "doc_id": doc_id,
        "thread_id": thread_id,
        "parent_id": parent_id,
        "thread_template_id": thread_template_id,
        "comment_flow_id": comment_flow_id,
        "dial": dict(DEFAULT_DIAL),
        "persona_archetype_id": persona_archetype_id,
        "author_role": "regular",
        "stance": "neutral",
        "intent": "info",
        "emotion": "calm",
        "topic_tags": topic_tags,
        "style_tags": style_tags,
        "toxicity_flag": False,
        "pii_flag": False,
        "text": text,
        "notes": notes,
    }


def _build_rows(packs: LoadedPacks) -> tuple[list[dict], list[dict]]:
    communities_by_board = _community_by_board(packs)
    reference_rows: list[dict] = []
    refined_rows: list[dict] = []

    for board in sorted(packs.boards.values(), key=lambda row: row["id"]):
        board_id = board["id"]
        community = communities_by_board.get(board_id)
        zone_id = str(community.get("zone_id", "A")) if community else "A"
        template_id, flow_id = _template_for_board(packs, board_id)
        thread_id = f"{board_id}-reference-thread"
        taboos = ", ".join(str(row) for row in board.get("taboos", []))
        memes = ", ".join(str(row) for row in board.get("memes", []))
        topic = str(board.get("topic", ""))
        emotion = str(board.get("emotion", ""))
        community_id = str(community.get("id", "")) if community else ""

        reference_text = (
            f"[{board_id}/{zone_id}] board={board.get('name','')} "
            f"topic={topic} emotion={emotion} "
            f"taboos={taboos} memes={memes} community={community_id}"
        )
        refined_text = (
            f"{board.get('name','')} 보드 기준: {topic}. "
            f"기본 정서는 {emotion}이며 금기 키워드는 {taboos}."
        )

        reference_rows.append(
            _base_row(
                board_id=board_id,
                zone_id=zone_id,
                source_type="reference",
                doc_id=f"{board_id}-ref-0001",
                thread_id=thread_id,
                parent_id=f"{thread_id}-p00",
                thread_template_id=template_id,
                comment_flow_id=flow_id,
                persona_archetype_id="AG-04",
                topic_tags=[board_id, "board_card"],
                style_tags=["reference", "pack"],
                text=reference_text,
                notes=f"pack=board_pack.json board_id={board_id}",
            )
        )
        refined_rows.append(
            _base_row(
                board_id=board_id,
                zone_id=zone_id,
                source_type="refined",
                doc_id=f"{board_id}-rfd-0001",
                thread_id=f"{board_id}-refined-thread",
                parent_id=f"{board_id}-refined-thread-p00",
                thread_template_id=template_id,
                comment_flow_id=flow_id,
                persona_archetype_id="AG-01",
                topic_tags=[board_id, "board_refined"],
                style_tags=["refined", "pack"],
                text=refined_text,
                notes=f"pack=board_pack.json board_id={board_id}",
            )
        )

    for community in sorted(packs.communities.values(), key=lambda row: row["id"]):
        board_id = str(community.get("board_id", "B01"))
        zone_id = str(community.get("zone_id", "A"))
        template_id, flow_id = _template_for_board(packs, board_id)
        community_id = community["id"]
        thread_id = f"{community_id}-reference-thread"
        identity = ", ".join(str(row) for row in community.get("identity", []))
        biases = ", ".join(str(row) for row in community.get("biases", []))
        taboos = ", ".join(str(row) for row in community.get("taboos", []))
        evidence = ", ".join(str(row) for row in community.get("preferred_evidence", []))
        reference_text = (
            f"[{community_id}] board={board_id} zone={zone_id} identity={identity} "
            f"biases={biases} preferred_evidence={evidence} taboos={taboos}"
        )
        refined_text = (
            f"{community.get('name','')} 렌즈는 {identity} 성향을 가지며 "
            f"주요 편향은 {biases}이다."
        )

        reference_rows.append(
            _base_row(
                board_id=board_id,
                zone_id=zone_id,
                source_type="reference",
                doc_id=f"{community_id}-ref-0001",
                thread_id=thread_id,
                parent_id=f"{thread_id}-p00",
                thread_template_id=template_id,
                comment_flow_id=flow_id,
                persona_archetype_id="AG-08",
                topic_tags=[community_id, "community_card"],
                style_tags=["reference", "pack"],
                text=reference_text,
                notes=f"pack=community_pack.json community_id={community_id}",
            )
        )
        refined_rows.append(
            _base_row(
                board_id=board_id,
                zone_id=zone_id,
                source_type="refined",
                doc_id=f"{community_id}-rfd-0001",
                thread_id=f"{community_id}-refined-thread",
                parent_id=f"{community_id}-refined-thread-p00",
                thread_template_id=template_id,
                comment_flow_id=flow_id,
                persona_archetype_id="AG-10",
                topic_tags=[community_id, "community_refined"],
                style_tags=["refined", "pack"],
                text=refined_text,
                notes=f"pack=community_pack.json community_id={community_id}",
            )
        )

    for rule in sorted(packs.rules.values(), key=lambda row: row["id"]):
        rule_id = rule["id"]
        summary = str(rule.get("summary", ""))
        category = str(rule.get("category", ""))
        reference_rows.append(
            _base_row(
                board_id="B11",
                zone_id="A",
                source_type="reference",
                doc_id=f"{rule_id}-ref-0001",
                thread_id=f"{rule_id}-reference-thread",
                parent_id=f"{rule_id}-reference-thread-p00",
                thread_template_id="T4",
                comment_flow_id="P4",
                persona_archetype_id="AG-02",
                topic_tags=[category or "rule", rule_id],
                style_tags=["reference", "rule"],
                text=f"{rule_id} {rule.get('name','')} category={category} summary={summary}",
                notes=f"pack=rule_pack.json rule_id={rule_id}",
            )
        )

    return reference_rows, refined_rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_corpus_from_packs(*, packs_dir: Path, corpus_dir: Path) -> dict:
    packs = load_packs(packs_dir, enforce_phase1_minimums=True)
    reference_rows, refined_rows = _build_rows(packs)
    generated_rows: list[dict] = []

    reference_path = corpus_dir / "reference.jsonl"
    refined_path = corpus_dir / "refined.jsonl"
    generated_path = corpus_dir / "generated.jsonl"
    manifest_path = corpus_dir / "manifest.json"

    _write_jsonl(reference_path, reference_rows)
    _write_jsonl(refined_path, refined_rows)
    _write_jsonl(generated_path, generated_rows)

    manifest = {
        "schema_version": "corpus.manifest.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "packs_dir": str(packs_dir),
        "corpus_dir": str(corpus_dir),
        "reference_count": len(reference_rows),
        "refined_count": len(refined_rows),
        "generated_count": len(generated_rows),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_corpus_rows(
    corpus_dir: Path,
    source_types: tuple[str, ...] = ("reference", "refined", "generated"),
) -> list[dict]:
    if not corpus_dir.exists():
        return []

    source_to_path = {
        "reference": corpus_dir / "reference.jsonl",
        "refined": corpus_dir / "refined.jsonl",
        "generated": corpus_dir / "generated.jsonl",
    }

    rows: list[dict] = []
    for source_type in source_types:
        path = source_to_path.get(source_type)
        if path is None:
            continue
        for row in _read_jsonl(path):
            copied = dict(row)
            copied.setdefault("source_type", source_type)
            rows.append(copied)
    return rows


def load_corpus_texts(corpus_dir: Path, source_types: tuple[str, ...] = ("reference", "refined")) -> list[str]:
    if not corpus_dir.exists():
        return []

    source_to_path = {
        "reference": corpus_dir / "reference.jsonl",
        "refined": corpus_dir / "refined.jsonl",
        "generated": corpus_dir / "generated.jsonl",
    }
    allowed = set(source_types)
    texts: list[str] = []
    seen: set[str] = set()

    for source_type, path in source_to_path.items():
        if source_type not in allowed:
            continue
        for row in _read_jsonl(path):
            text = str(row.get("text", "")).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            texts.append(text)
    return texts
