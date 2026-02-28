import re

from rapidfuzz.fuzz import ratio
from project_dream.prompt_templates import render_prompt


PHONE_PATTERN = re.compile(r"01[0-9]-\d{3,4}-\d{4}")
TABOO_WORDS = ["실명", "서명 단서", "사망 조롱"]
EVIDENCE_KEYWORDS = ["정본", "증거", "로그", "출처", "근거"]
CONTEXT_KEYWORDS = ["주장", "판단", "사실", "정황", "의혹"]
CONTRADICTION_TERM_GROUPS = [
    (("확정", "단정"), ("추정", "의혹", "가능성")),
    (("사실",), ("루머", "소문")),
]


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


def _entity_refs_from_text(text: str) -> list[str]:
    refs: set[str] = set()
    if PHONE_PATTERN.search(text):
        refs.add("ENT-CONTACT")
    if any(keyword in text for keyword in EVIDENCE_KEYWORDS):
        refs.add("ENT-EVIDENCE")
    if any(keyword in text for keyword in CONTEXT_KEYWORDS) or any(
        marker in text for marker in ("확정", "추정", "의혹", "단정")
    ):
        refs.add("ENT-CLAIM")
    if any(word in text for word in TABOO_WORDS):
        refs.add("ENT-SAFETY-LANGUAGE")
    if any(word in text for word in ("운영", "관리자", "모더레이터")):
        refs.add("ENT-MODERATION")
    return sorted(refs)


def _run_consistency_checker(text: str) -> dict:
    issues: list[dict] = []
    refs = _entity_refs_from_text(text)
    for positives, negatives in CONTRADICTION_TERM_GROUPS:
        found_positive = next((term for term in positives if term in text), "")
        found_negative = next((term for term in negatives if term in text), "")
        if not found_positive or not found_negative:
            continue
        issues.append(
            _build_violation(
                gate_name="lore",
                rule_id="RULE-PLZ-LORE-02",
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
) -> dict:
    gates = []
    aggregate_violations: list[dict] = []
    current = text

    # Gate 1: Safety
    warnings: list[str] = []
    safety_violations: list[dict] = []
    if PHONE_PATTERN.search(current):
        warnings.append("PII_PHONE")
        current = PHONE_PATTERN.sub("[REDACTED-PHONE]", current)
        safety_violations.append(
            _build_violation(
                gate_name="safety",
                rule_id="RULE-PLZ-SAFE-01",
                code="PII_PHONE",
                message="전화번호 패턴 감지",
                severity="high",
                entity_refs=["ENT-CONTACT"],
            )
        )
    for taboo in TABOO_WORDS:
        if taboo in current:
            warnings.append(f"TABOO_TERM:{taboo}")
            current = current.replace(taboo, "부적절 표현")
            safety_violations.append(
                _build_violation(
                    gate_name="safety",
                    rule_id="RULE-PLZ-SAFE-02",
                    code="TABOO_TERM",
                    message=f"금칙어 감지: {taboo}",
                    severity="medium",
                    entity_refs=["ENT-SAFETY-LANGUAGE"],
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
    evidence_found = any(keyword in current for keyword in EVIDENCE_KEYWORDS)
    context_found = any(keyword in current for keyword in CONTEXT_KEYWORDS)
    consistency = _run_consistency_checker(current)
    lore_violations: list[dict] = []
    checklist = {
        "evidence_keyword_found": evidence_found,
        "context_keyword_found": context_found,
    }
    if not evidence_found:
        lore_violations.append(
            _build_violation(
                gate_name="lore",
                rule_id="RULE-PLZ-LORE-01",
                code="EVIDENCE_MISSING",
                message="증거/정본/로그 기준 부재",
                severity="medium",
                entity_refs=sorted(set(["ENT-EVIDENCE"] + _entity_refs_from_text(current))),
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
