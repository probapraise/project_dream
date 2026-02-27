import hashlib

from project_dream.models import SeedInput


def select_participants(seed: SeedInput, round_idx: int) -> list[str]:
    base = ["AG-01", "AG-02", "AG-03", "AG-04", "AG-05"]
    key = f"{seed.seed_id}:{round_idx}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    shift = int(digest[:8], 16) % len(base)
    return base[shift:] + base[:shift]
