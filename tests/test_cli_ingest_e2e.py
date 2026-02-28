import json
from pathlib import Path

from project_dream.cli import main


def test_cli_ingest_writes_corpus_files(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"
    rc = main(
        [
            "ingest",
            "--packs-dir",
            "packs",
            "--corpus-dir",
            str(corpus_dir),
        ]
    )

    assert rc == 0
    assert (corpus_dir / "reference.jsonl").exists()
    assert (corpus_dir / "refined.jsonl").exists()
    assert (corpus_dir / "generated.jsonl").exists()

    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "corpus.manifest.v1"
    assert manifest["reference_count"] >= 22
