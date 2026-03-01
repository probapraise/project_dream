import re
from copy import deepcopy

from rapidfuzz.fuzz import ratio
from project_dream.prompt_templates import render_prompt


DEFAULT_GATE_POLICY = {
    "safety": {
        "phone_pattern": r"01[0-9]-\d{3,4}-\d{4}",
        "taboo_words": ["실명", "서명 단서", "사망 조롱"],
        "rule_ids": {
            "pii_phone": "RULE-PLZ-SAFE-01",
            "taboo_term": "RULE-PLZ-SAFE-02",
            "seed_forbidden": "RULE-PLZ-SAFE-03",
        },
    },
    "lore": {
        "evidence_keywords": ["정본", "증거", "로그", "출처", "근거"],
        "context_keywords": ["주장", "판단", "사실", "정황", "의혹"],
        "contradiction_term_groups": [
            {"positives": ["확정", "단정"], "negatives": ["추정", "의혹", "가능성"]},
            {"positives": ["사실"], "negatives": ["루머", "소문"]},
        ],
        "rule_ids": {
            "evidence_missing": "RULE-PLZ-LORE-01",
            "consistency_conflict": "RULE-PLZ-LORE-02",
        },
    },
}


def _as_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


def _normalize_contradiction_term_groups(values: object) -> list[tuple[tuple[str, ...], tuple[str, ...]]]:
    if not isinstance(values, list):
        return []
    groups: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for raw_group in values:
        if not isinstance(raw_group, dict):
            continue
        positives = tuple(_as_str_list(raw_group.get("positives")))
        negatives = tuple(_as_str_list(raw_group.get("negatives")))
        if not positives or not negatives:
            continue
        groups.append((positives, negatives))
    return groups


def _resolve_gate_policy(gate_policy: dict | None) -> dict:
    resolved = deepcopy(DEFAULT_GATE_POLICY)
    if not isinstance(gate_policy, dict):
        return resolved

    safety = gate_policy.get("safety")
    if isinstance(safety, dict):
        phone_pattern = str(safety.get("phone_pattern", "")).strip()
        if phone_pattern:
            resolved["safety"]["phone_pattern"] = phone_pattern
        taboo_words = _as_str_list(safety.get("taboo_words"))
        if taboo_words:
            resolved["safety"]["taboo_words"] = taboo_words
        rule_ids = safety.get("rule_ids")
        if isinstance(rule_ids, dict):
            for key in ("pii_phone", "taboo_term", "seed_forbidden"):
                value = str(rule_ids.get(key, "")).strip()
                if value:
                    resolved["safety"]["rule_ids"][key] = value

    lore = gate_policy.get("lore")
    if isinstance(lore, dict):
        evidence_keywords = _as_str_list(lore.get("evidence_keywords"))
        if evidence_keywords:
            resolved["lore"]["evidence_keywords"] = evidence_keywords
        context_keywords = _as_str_list(lore.get("context_keywords"))
        if context_keywords:
            resolved["lore"]["context_keywords"] = context_keywords
        contradiction_groups = _normalize_contradiction_term_groups(lore.get("contradiction_term_groups"))
        if contradiction_groups:
            resolved["lore"]["contradiction_term_groups"] = [
                {"positives": list(positives), "negatives": list(negatives)}
                for positives, negatives in contradiction_groups
            ]
        rule_ids = lore.get("rule_ids")
        if isinstance(rule_ids, dict):
            for key in ("evidence_missing", "consistency_conflict"):
                value = str(rule_ids.get(key, "")).strip()
                if value:
                    resolved["lore"]["rule_ids"][key] = value

    return resolved


def _compile_phone_pattern(pattern_text: str) -> re.Pattern[str]:
    raw = pattern_text.strip() or DEFAULT_GATE_POLICY["safety"]["phone_pattern"]
    try:
        return re.compile(raw)
    except re.error:
        return re.compile(DEFAULT_GATE_POLICY["safety"]["phone_pattern"])


def _build_violation(
    *,
    gate_name: str,
    rule_id: str,
    code: str,
    message: str,
    severity: str = "medium",
    entity_refs: list[str] | None = None,
) -> dict:
    return {
        "gate_name": gate_name,
        "rule_id": rule_id,
        "code": code,
        "message": message,
        "severity": severity,
        "entity_refs": list(entity_refs or []),
    }


def _entity_refs_from_text(
    text: str,
    *,
    phone_pattern: re.Pattern[str],
    evidence_keywords: list[str],
    context_keywords: list[str],
    taboo_words: list[str],
) -> list[str]:
    refs: set[str] = set()
    if phone_pattern.search(text):
        refs.add("ENT-CONTACT")
    if any(keyword in text for keyword in evidence_keywords):
        refs.add("ENT-EVIDENCE")
    if any(keyword in text for keyword in context_keywords) or any(
        marker in text for marker in ("확정", "추정", "의혹", "단정")
    ):
        refs.add("ENT-CLAIM")
    if any(word in text for word in taboo_words):
        refs.add("ENT-SAFETY-LANGUAGE")
    if any(word in text for word in ("운영", "관리자", "모더레이터")):
        refs.add("ENT-MODERATION")
    return sorted(refs)


def _run_consistency_checker(
    text: str,
    *,
    contradiction_term_groups: list[tuple[tuple[str, ...], tuple[str, ...]]],
    lore_consistency_rule_id: str,
    phone_pattern: re.Pattern[str],
    evidence_keywords: list[str],
    context_keywords: list[str],
    taboo_words: list[str],
) -> dict:
    issues: list[dict] = []
    refs = _entity_refs_from_text(
        text,
        phone_pattern=phone_pattern,
        evidence_keywords=evidence_keywords,
        context_keywords=context_keywords,
        taboo_words=taboo_words,
    )
    for positives, negatives in contradiction_term_groups:
        found_positive = next((term for term in positives if term in text), "")
        found_negative = next((term for term in negatives if term in text), "")
        if not found_positive or not found_negative:
            continue
        issues.append(
            _build_violation(
                gate_name="lore",
                rule_id=lore_consistency_rule_id,
                code="CONSISTENCY_CONFLICT",
                message=f"상충 표현 감지: {found_positive}/{found_negative}",
                severity="medium",
                entity_refs=sorted(set(refs + ["ENT-CLAIM"])),
            )
        )
        break
    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "entity_refs": refs,
    }


def run_gates(
    text: str,
    corpus: list[str],
    similarity_threshold: int = 85,
    template_set: str = "v1",
    forbidden_terms: list[str] | None = None,
    sensitivity_tags: list[str] | None = None,
    gate_policy: dict | None = None,
) -> dict:
    gates = []
    aggregate_violations: list[dict] = []
    raw_text = text
    current = text
    resolved_policy = _resolve_gate_policy(gate_policy)
    safety_policy = resolved_policy.get("safety", {})
    lore_policy = resolved_policy.get("lore", {})
    phone_pattern = _compile_phone_pattern(str(safety_policy.get("phone_pattern", "")))
    taboo_words = _as_str_list(safety_policy.get("taboo_words")) or _as_str_list(
        DEFAULT_GATE_POLICY["safety"]["taboo_words"]
    )
    evidence_keywords = _as_str_list(lore_policy.get("evidence_keywords")) or _as_str_list(
        DEFAULT_GATE_POLICY["lore"]["evidence_keywords"]
    )
    context_keywords = _as_str_list(lore_policy.get("context_keywords")) or _as_str_list(
        DEFAULT_GATE_POLICY["lore"]["context_keywords"]
    )
    contradiction_term_groups = _normalize_contradiction_term_groups(
        lore_policy.get("contradiction_term_groups")
    ) or _normalize_contradiction_term_groups(DEFAULT_GATE_POLICY["lore"]["contradiction_term_groups"])
    safety_rule_ids = safety_policy.get("rule_ids", {})
    lore_rule_ids = lore_policy.get("rule_ids", {})
    pii_phone_rule_id = str(safety_rule_ids.get("pii_phone", "RULE-PLZ-SAFE-01")).strip() or "RULE-PLZ-SAFE-01"
    taboo_term_rule_id = str(safety_rule_ids.get("taboo_term", "RULE-PLZ-SAFE-02")).strip() or "RULE-PLZ-SAFE-02"
    seed_forbidden_rule_id = (
        str(safety_rule_ids.get("seed_forbidden", "RULE-PLZ-SAFE-03")).strip() or "RULE-PLZ-SAFE-03"
    )
    evidence_missing_rule_id = (
        str(lore_rule_ids.get("evidence_missing", "RULE-PLZ-LORE-01")).strip() or "RULE-PLZ-LORE-01"
    )
    consistency_conflict_rule_id = (
        str(lore_rule_ids.get("consistency_conflict", "RULE-PLZ-LORE-02")).strip() or "RULE-PLZ-LORE-02"
    )

    # Gate 1: Safety
    warnings: list[str] = []
    safety_violations: list[dict] = []
    if phone_pattern.search(current):
        warnings.append("PII_PHONE")
        current = phone_pattern.sub("[REDACTED-PHONE]", current)
        safety_violations.append(
            _build_violation(
                gate_name="safety",
                rule_id=pii_phone_rule_id,
                code="PII_PHONE",
                message="전화번호 패턴 감지",
                severity="high",
                entity_refs=["ENT-CONTACT"],
            )
        )
    for taboo in taboo_words:
        if taboo in current:
            warnings.append(f"TABOO_TERM:{taboo}")
            current = current.replace(taboo, "부적절 표현")
            safety_violations.append(
                _build_violation(
                    gate_name="safety",
                    rule_id=taboo_term_rule_id,
                    code="TABOO_TERM",
                    message=f"금칙어 감지: {taboo}",
                    severity="medium",
                    entity_refs=["ENT-SAFETY-LANGUAGE"],
                )
            )
    for raw_term in forbidden_terms or []:
        term = str(raw_term).strip()
        if not term:
            continue
        found_in_raw = term in raw_text
        found_in_current = term in current
        if not found_in_raw and not found_in_current:
            continue
        warnings.append(f"SEED_FORBIDDEN_TERM:{term}")
        if found_in_current:
            current = current.replace(term, "제약어")
        refs = ["ENT-SEED-CONSTRAINT"]
        refs.extend([f"ENT-SENS:{tag}" for tag in (sensitivity_tags or []) if str(tag).strip()])
        safety_violations.append(
            _build_violation(
                gate_name="safety",
                rule_id=seed_forbidden_rule_id,
                code="SEED_FORBIDDEN_TERM",
                message=f"Seed 금지어 감지: {term}",
                severity="high",
                entity_refs=refs,
            )
        )
    safety_pass = len(warnings) == 0
    aggregate_violations.extend(safety_violations)
    gates.append(
        {
            "gate_name": "safety",
            "passed": safety_pass,
            "reason": f"warnings={len(warnings)}",
            "warnings": warnings,
            "sensitivity_tags": [str(tag) for tag in (sensitivity_tags or []) if str(tag).strip()],
            "violations": safety_violations,
        }
    )

    # Gate 2: Similarity
    scored = [{"index": idx, "score": float(ratio(current, c))} for idx, c in enumerate(corpus)]
    scored.sort(key=lambda item: item["score"], reverse=True)
    top_k = scored[:3]
    max_sim = top_k[0]["score"] if top_k else 0.0
    similarity_pass = max_sim < similarity_threshold
    similarity_violations: list[dict] = []
    if not similarity_pass:
        current = f"{current} (유사도 재작성)"
        similarity_violations.append(
            _build_violation(
                gate_name="similarity",
                rule_id="RULE-PLZ-SIM-01",
                code="SIMILARITY_OVER_THRESHOLD",
                message=f"유사도 임계치 초과: {max_sim} >= {similarity_threshold}",
                severity="low",
                entity_refs=["ENT-CONTENT"],
            )
        )
    aggregate_violations.extend(similarity_violations)
    gates.append(
        {
            "gate_name": "similarity",
            "passed": similarity_pass,
            "reason": f"max_similarity={max_sim}",
            "top_k": top_k,
            "violations": similarity_violations,
        }
    )

    # Gate 3: Lore consistency (MVP rule)
    evidence_found = any(keyword in current for keyword in evidence_keywords)
    context_found = any(keyword in current for keyword in context_keywords)
    consistency = _run_consistency_checker(
        current,
        contradiction_term_groups=contradiction_term_groups,
        lore_consistency_rule_id=consistency_conflict_rule_id,
        phone_pattern=phone_pattern,
        evidence_keywords=evidence_keywords,
        context_keywords=context_keywords,
        taboo_words=taboo_words,
    )
    lore_violations: list[dict] = []
    checklist = {
        "evidence_keyword_found": evidence_found,
        "context_keyword_found": context_found,
    }
    if not evidence_found:
        lore_violations.append(
            _build_violation(
                gate_name="lore",
                rule_id=evidence_missing_rule_id,
                code="EVIDENCE_MISSING",
                message="증거/정본/로그 기준 부재",
                severity="medium",
                entity_refs=sorted(
                    set(
                        ["ENT-EVIDENCE"]
                        + _entity_refs_from_text(
                            current,
                            phone_pattern=phone_pattern,
                            evidence_keywords=evidence_keywords,
                            context_keywords=context_keywords,
                            taboo_words=taboo_words,
                        )
                    )
                ),
            )
        )
        current = f"{current} / 근거(정본/증거/로그) 기준 추가 필요"
    if not consistency["passed"]:
        lore_violations.extend(consistency["issues"])
        current = f"{current} / 정합성 충돌(확정/추정) 정리 필요"
    lore_pass = evidence_found and consistency["passed"]
    aggregate_violations.extend(lore_violations)
    gates.append(
        {
            "gate_name": "lore",
            "passed": lore_pass,
            "reason": render_prompt("validation_lore", template_set=template_set),
            "checklist": checklist,
            "consistency": consistency,
            "violations": lore_violations,
        }
    )

    return {
        "final_text": current,
        "gates": gates,
        "violations": aggregate_violations,
    }
