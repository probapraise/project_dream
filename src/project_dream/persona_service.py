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


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_persona_archetype_id(persona_id: str, packs) -> str:
    if packs is None or not getattr(packs, "personas", None):
        return ""
    persona = packs.personas.get(persona_id)
    if not isinstance(persona, dict):
        return ""
    return str(persona.get("archetype_id", "")).strip()


def _apply_register_profile(base_voice: dict[str, Any], profile: dict) -> dict[str, Any]:
    out = dict(base_voice)
    sentence_length = str(profile.get("sentence_length", "")).strip()
    profile_endings = _as_str_list(profile.get("endings"))
    profile_words = _as_str_list(profile.get("frequent_words"))
    profile_taboos = _as_str_list(profile.get("taboo_words"))

    if sentence_length:
        out["sentence_length"] = sentence_length
    if profile_endings:
        out["endings"] = _unique(profile_endings + _as_str_list(out.get("endings")))
    if profile_words:
        out["frequent_words"] = _unique(profile_words + _as_str_list(out.get("frequent_words")))
    if profile_taboos:
        out["taboo_words"] = _unique(_as_str_list(out.get("taboo_words")) + profile_taboos)
    return out


def _register_rule_matches(
    rule: dict,
    *,
    archetype_id: str,
    runtime_context: dict[str, Any],
) -> bool:
    conditions = rule.get("conditions", {})
    if not isinstance(conditions, dict):
        return False

    condition_archetypes = set(_as_str_list(conditions.get("archetype_ids")))
    if condition_archetypes and archetype_id not in condition_archetypes:
        return False

    dial_axis_in = {axis.upper() for axis in _as_str_list(conditions.get("dial_axis_in"))}
    dial_axis = str(runtime_context.get("dial_dominant_axis", "")).strip().upper()
    if dial_axis_in and dial_axis not in dial_axis_in:
        return False

    meme_phase_in = set(_as_str_list(conditions.get("meme_phase_in")))
    meme_phase = str(runtime_context.get("meme_phase", "")).strip()
    if meme_phase_in and meme_phase not in meme_phase_in:
        return False

    status_in = set(_as_str_list(conditions.get("status_in")))
    status = str(runtime_context.get("status", "")).strip()
    if status_in and status not in status_in:
        return False

    if _to_int(runtime_context.get("total_reports"), 0) < _to_int(conditions.get("reports_gte"), 0):
        return False
    if _to_int(runtime_context.get("evidence_hours_left"), 9999) > _to_int(conditions.get("evidence_hours_lte"), 9999):
        return False
    if _to_int(runtime_context.get("round_idx"), 0) < _to_int(conditions.get("round_gte"), 0):
        return False

    return True


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
    archetype_id = _resolve_persona_archetype_id(persona_id, packs)

    base = _VOICE_BY_ARCHETYPE.get(archetype_id or "", _VOICE_BY_ARCHETYPE["AG-04"])
    taboo_words = list(_ZONE_TABOO_WORDS.get(zone_id, []))

    return {
        "persona_id": persona_id,
        "zone_id": zone_id,
        "sentence_length": base["sentence_length"],
        "endings": list(base["endings"]),
        "frequent_words": list(base["frequent_words"]),
        "taboo_words": taboo_words,
        "register_profile_id": "",
        "register_rule_id": "",
        "register_switch_applied": False,
    }


def apply_register_switch(
    voice_constraints: dict[str, Any],
    *,
    persona_id: str,
    packs=None,
    runtime_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(voice_constraints)
    out.setdefault("register_profile_id", "")
    out.setdefault("register_rule_id", "")
    out.setdefault("register_switch_applied", False)

    if packs is None:
        return out
    register_profiles = getattr(packs, "register_profiles", {})
    register_switch_rules = getattr(packs, "register_switch_rules", [])
    archetypes = getattr(packs, "archetypes", {})

    if not isinstance(register_profiles, dict):
        return out
    if not isinstance(register_switch_rules, list):
        register_switch_rules = []

    archetype_id = _resolve_persona_archetype_id(persona_id, packs)
    runtime = dict(runtime_context) if isinstance(runtime_context, dict) else {}

    if archetype_id and isinstance(archetypes, dict):
        archetype = archetypes.get(archetype_id, {})
        if isinstance(archetype, dict):
            out["register_profile_id"] = str(archetype.get("default_register_profile_id", "")).strip()

    for rule in register_switch_rules:
        if not isinstance(rule, dict):
            continue
        if not _register_rule_matches(rule, archetype_id=archetype_id, runtime_context=runtime):
            continue
        profile_id = str(rule.get("apply_profile_id", "")).strip()
        profile = register_profiles.get(profile_id)
        if not isinstance(profile, dict):
            continue
        out = _apply_register_profile(out, profile)
        out["register_profile_id"] = profile_id
        out["register_rule_id"] = str(rule.get("id", "")).strip()
        out["register_switch_applied"] = True
        return out

    return out
