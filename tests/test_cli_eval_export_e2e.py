import json
from pathlib import Path

from project_dream.cli import main


def test_cli_eval_export_writes_external_eval_bundle(tmp_path: Path):
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(
        json.dumps(
            {
                "seed_id": "SEED-CLI-EXPORT-001",
                "title": "평가 export",
                "summary": "외부 평가 파일 생성",
                "board_id": "B07",
                "zone_id": "D",
            }
        ),
        encoding="utf-8",
    )

    runs_dir = tmp_path / "runs"
    rc = main(
        [
            "simulate",
            "--seed",
            str(seed_file),
            "--output-dir",
            str(runs_dir),
            "--rounds",
            "3",
        ]
    )
    assert rc == 0

    output_dir = tmp_path / "external-eval"
    rc = main(
        [
            "eval-export",
            "--runs-dir",
            str(runs_dir),
            "--output-dir",
            str(output_dir),
            "--max-contexts",
            "4",
        ]
    )
    assert rc == 0

    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "external_eval_export.v1"
    assert (output_dir / "promptfoo_cases.jsonl").exists()
    assert (output_dir / "ragas_samples.jsonl").exists()
    assert (output_dir / "trace_events.jsonl").exists()
