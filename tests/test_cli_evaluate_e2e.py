import json
from pathlib import Path

from project_dream.cli import main


def test_cli_evaluate_writes_eval_json_for_latest_run(tmp_path: Path):
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
            "--packs-dir",
            "packs",
            "--output-dir",
            str(tmp_path / "runs"),
            "--rounds",
            "3",
        ]
    )
    assert rc == 0

    rc = main(["evaluate", "--runs-dir", str(tmp_path / "runs")])
    assert rc == 0

    eval_files = list((tmp_path / "runs").glob("*/eval.json"))
    assert eval_files
    payload = json.loads(eval_files[0].read_text(encoding="utf-8"))
    assert "checks" in payload
    assert "pass_fail" in payload
    assert payload["metric_set"] == "v1"
