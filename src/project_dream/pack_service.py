import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoadedPacks:
    boards: dict[str, dict]
    communities: dict[str, dict]


def load_packs(base_dir: Path) -> LoadedPacks:
    board_pack = json.loads((base_dir / "board_pack.json").read_text(encoding="utf-8"))
    community_pack = json.loads((base_dir / "community_pack.json").read_text(encoding="utf-8"))

    boards = {b["id"]: b for b in board_pack["boards"]}
    communities = {c["id"]: c for c in community_pack["communities"]}

    for com in communities.values():
        board_id = com["board_id"]
        if board_id not in boards:
            raise ValueError(f"Unknown board_id: {board_id}")

    return LoadedPacks(boards=boards, communities=communities)
