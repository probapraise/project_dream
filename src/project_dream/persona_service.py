import hashlib
from typing import Any

from project_dream.models import SeedInput


_FALLBACK_BASE = ["AG-01", "AG-02", "AG-03", "AG-04", "AG-05"]

_VOICE_BY_ARCHETYPE: dict[str, dict[str, Any]] = {
    "AG-01": {
        "sentence_length": "short",
        "endings": ["요", "임", "정리함"],
        "frequent_words": ["요약", "핵심", "정리"],
    },
    "AG-02": {
        "sentence_length": "medium",
        "endings": ["입니다", "조항상", "근거로"],
        "frequent_words": ["규정", "조항", "절차"],
    },
    "AG-03": {
        "sentence_length": "short",
        "endings": ["아님?", "각", "임"],
        "frequent_words": ["폭주", "과열", "분노"],
    },
    "AG-04": {
        "sentence_length": "medium",
        "endings": ["확인됨", "검증 필요", "재현 바람"],
        "frequent_words": ["근거", "로그", "반례"],
    },
    "AG-05": {
        "sentence_length": "short",
        "endings": ["계산해보면", "손해임", "계약상"],
        "frequent_words": ["비용", "거래", "계약"],
    },
    "AG-06": {
        "sentence_length": "short",
        "endings": ["밈임", "짤각", "사료행"],
        "frequent_words": ["패러디", "밈", "풍자"],
    },
    "AG-07": {
        "sentence_length": "medium",
        "endings": ["도와줘요", "경험상", "억울함"],
        "frequent_words": ["피해", "사건", "경험"],
    },
    "AG-08": {
        "sentence_length": "medium",
        "endings": ["질서상", "필수입니다", "운영상"],
        "frequent_words": ["질서", "운영", "안정"],
    },
    "AG-09": {
        "sentence_length": "long",
        "endings": ["의혹입니다", "연결됩니다", "수상함"],
        "frequent_words": ["의혹", "정황", "연결"],
    },
    "AG-10": {
        "sentence_length": "medium",
        "endings": ["중재합시다", "절충안", "합의"],
        "frequent_words": ["중재", "합의", "절충"],
    },
}

_ZONE_TABOO_WORDS = {
    "A": ["realname_dox", "signature_dox"],
    "B": ["injury_dox", "doping_claim_no_proof"],
    "C": ["family_secret", "leak_to_public"],
    "D": ["illegal_trade", "fake_review"],
}


def _shift(seed_id: str, round_idx: int, salt: str, size: int) -> int:
    if size <= 1:
        return 0
    key = f"{seed_id}:{round_idx}:{salt}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:8], 16) % size


def _rotate(values: list[str], *, seed_id: str, round_idx: int, salt: str) -> list[str]:
    if not values:
        return []
    shift = _shift(seed_id, round_idx, salt, len(values))
    return values[shift:] + values[:shift]


def _fallback_participants(seed: SeedInput, round_idx: int, limit: int) -> list[str]:
    ordered = _rotate(_FALLBACK_BASE, seed_id=seed.seed_id, round_idx=round_idx, salt="fallback")
    return ordered[: max(limit, 1)]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def select_participants(
    seed: SeedInput,
    round_idx: int,
    *,
    packs=None,
    limit: int = 5,
) -> list[str]:
    if packs is None or not getattr(packs, "personas", None):
        return _fallback_participants(seed, round_idx, limit)

    communities = packs.communities
    preferred: list[str] = []
    board_match: list[str] = []
    others: list[str] = []

    for persona in sorted(packs.personas.values(), key=lambda row: row["id"]):
        persona_id = persona["id"]
        community_id = persona.get("main_com")
        community = communities.get(community_id, {})
        board_id = community.get("board_id")
        zone_id = community.get("zone_id")

        if board_id == seed.board_id and zone_id == seed.zone_id:
            preferred.append(persona_id)
        elif board_id == seed.board_id:
            board_match.append(persona_id)
        else:
            others.append(persona_id)

    ordered = _unique(
        _rotate(preferred, seed_id=seed.seed_id, round_idx=round_idx, salt="preferred")
        + _rotate(board_match, seed_id=seed.seed_id, round_idx=round_idx, salt="board")
        + _rotate(others, seed_id=seed.seed_id, round_idx=round_idx, salt="others")
    )
    if not ordered:
        return _fallback_participants(seed, round_idx, limit)
    return ordered[: max(limit, 1)]


def render_voice(
    persona_id: str,
    zone_id: str,
    *,
    packs=None,
) -> dict[str, Any]:
    archetype_id = None
    if packs is not None:
        persona = packs.personas.get(persona_id) if getattr(packs, "personas", None) else None
        if persona:
            archetype_id = persona.get("archetype_id")

    base = _VOICE_BY_ARCHETYPE.get(archetype_id or "", _VOICE_BY_ARCHETYPE["AG-04"])
    taboo_words = list(_ZONE_TABOO_WORDS.get(zone_id, []))

    return {
        "persona_id": persona_id,
        "zone_id": zone_id,
        "sentence_length": base["sentence_length"],
        "endings": list(base["endings"]),
        "frequent_words": list(base["frequent_words"]),
        "taboo_words": taboo_words,
    }
