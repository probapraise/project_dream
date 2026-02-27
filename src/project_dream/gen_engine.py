from project_dream.models import SeedInput


def generate_comment(seed: SeedInput, persona_id: str, round_idx: int) -> str:
    return (
        f"[{seed.board_id}/{seed.zone_id}] "
        f"R{round_idx} {persona_id}: {seed.title}에 대한 반응 - {seed.summary}"
    )
