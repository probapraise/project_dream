import json
from pathlib import Path

from project_dream.cli import main


def test_cli_simulate_writes_run_outputs(tmp_path: Path):
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(
        json.dumps(
            {
                "seed_id": "SEED-001",
                "title": "먹통 사건",
                "summary": "장터기둥 장애",
                "board_id": "B07",
                "zone_id": "D",
            }
        ),
        encoding="utf-8",
    )

    rc = main(
        [
            "simulate",
            "--seed",
            str(seed_file),
            "--output-dir",
            str(tmp_path / "runs"),
            "--rounds",
            "3",
        ]
    )
    assert rc == 0
    assert any((tmp_path / "runs").glob("*/runlog.jsonl"))
    assert any((tmp_path / "runs").glob("*/report.md"))
