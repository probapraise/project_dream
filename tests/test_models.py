from project_dream.models import SeedInput, Dial


def test_seed_input_defaults_and_validation():
    seed = SeedInput(
        seed_id="SEED-001",
        title="중계망 먹통 사건",
        summary="장터기둥이 갑자기 다운됨",
        board_id="B07",
        zone_id="D",
    )
    assert seed.dial == Dial(U=30, E=25, M=15, S=15, H=15)
