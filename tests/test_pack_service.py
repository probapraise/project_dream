from pathlib import Path
from project_dream.pack_service import load_packs


def test_pack_service_validates_board_reference():
    packs = load_packs(Path("tests/fixtures/packs"))
    assert "B01" in packs.boards
    assert packs.communities["COM-PLZ-001"]["board_id"] == "B01"
