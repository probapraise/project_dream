import re

from rapidfuzz.fuzz import ratio


PHONE_PATTERN = re.compile(r"01[0-9]-\d{3,4}-\d{4}")
TABOO_WORDS = ["실명", "서명 단서", "사망 조롱"]


def run_gates(text: str, corpus: list[str], similarity_threshold: int = 85) -> dict:
    gates = []
    current = text

    # Gate 1: Safety
    safety_pass = True
    if PHONE_PATTERN.search(current):
        safety_pass = False
        current = PHONE_PATTERN.sub("[REDACTED-PHONE]", current)
    for taboo in TABOO_WORDS:
        if taboo in current:
            safety_pass = False
            current = current.replace(taboo, "부적절 표현")
    gates.append({"gate_name": "safety", "passed": safety_pass, "reason": "pii/taboo check"})

    # Gate 2: Similarity
    max_sim = max((ratio(current, c) for c in corpus), default=0)
    similarity_pass = max_sim < similarity_threshold
    if not similarity_pass:
        current = f"{current} (재작성)"
    gates.append(
        {
            "gate_name": "similarity",
            "passed": similarity_pass,
            "reason": f"max_similarity={max_sim}",
        }
    )

    # Gate 3: Lore consistency (MVP rule)
    lore_pass = ("정본" in current) or ("증거" in current)
    if not lore_pass:
        current = f"{current} / 증거 기준 미기재"
    gates.append({"gate_name": "lore", "passed": lore_pass, "reason": "requires evidence context"})

    return {"final_text": current, "gates": gates}
