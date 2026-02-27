from project_dream.models import SeedInput
from project_dream.persona_service import select_participants
from project_dream.gen_engine import generate_comment


def test_generator_is_deterministic_for_same_seed():
    seed = SeedInput(seed_id="SEED-001", title="사건", summary="요약", board_id="B01", zone_id="A")
    participants = select_participants(seed, round_idx=1)
    c1 = generate_comment(seed, participants[0], round_idx=1)
    c2 = generate_comment(seed, participants[0], round_idx=1)
    assert c1 == c2
