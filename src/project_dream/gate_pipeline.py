import re

from rapidfuzz.fuzz import ratio
from project_dream.prompt_templates import render_prompt


PHONE_PATTERN = re.compile(r"01[0-9]-\d{3,4}-\d{4}")
TABOO_WORDS = ["실명", "서명 단서", "사망 조롱"]
EVIDENCE_KEYWORDS = ["정본", "증거", "로그", "출처", "근거"]
CONTEXT_KEYWORDS = ["주장", "판단", "사실", "정황", "의혹"]


def run_gates(
    text: str,
    corpus: list[str],
    similarity_threshold: int = 85,
    template_set: str = "v1",
) -> dict:
    gates = []
    current = text

    # Gate 1: Safety
    warnings: list[str] = []
    if PHONE_PATTERN.search(current):
        warnings.append("PII_PHONE")
        current = PHONE_PATTERN.sub("[REDACTED-PHONE]", current)
    for taboo in TABOO_WORDS:
        if taboo in current:
            warnings.append(f"TABOO_TERM:{taboo}")
            current = current.replace(taboo, "부적절 표현")
    safety_pass = len(warnings) == 0
    gates.append(
        {
            "gate_name": "safety",
            "passed": safety_pass,
            "reason": f"warnings={len(warnings)}",
            "warnings": warnings,
        }
    )

    # Gate 2: Similarity
    scored = [{"index": idx, "score": float(ratio(current, c))} for idx, c in enumerate(corpus)]
    scored.sort(key=lambda item: item["score"], reverse=True)
    top_k = scored[:3]
    max_sim = top_k[0]["score"] if top_k else 0.0
    similarity_pass = max_sim < similarity_threshold
    if not similarity_pass:
        current = f"{current} (유사도 재작성)"
    gates.append(
        {
            "gate_name": "similarity",
            "passed": similarity_pass,
            "reason": f"max_similarity={max_sim}",
            "top_k": top_k,
        }
    )

    # Gate 3: Lore consistency (MVP rule)
    evidence_found = any(keyword in current for keyword in EVIDENCE_KEYWORDS)
    context_found = any(keyword in current for keyword in CONTEXT_KEYWORDS)
    checklist = {
        "evidence_keyword_found": evidence_found,
        "context_keyword_found": context_found,
    }
    lore_pass = evidence_found
    if not lore_pass:
        current = f"{current} / 근거(정본/증거/로그) 기준 추가 필요"
    gates.append(
        {
            "gate_name": "lore",
            "passed": lore_pass,
            "reason": render_prompt("validation_lore", template_set=template_set),
            "checklist": checklist,
        }
    )

    return {"final_text": current, "gates": gates}
