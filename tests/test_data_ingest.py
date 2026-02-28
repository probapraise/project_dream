import json
from pathlib import Path

from project_dream.data_ingest import build_corpus_from_packs, load_corpus_texts


REQUIRED_ROW_KEYS = {
    "zone_id",
    "board_id",
    "source_type",
    "doc_type",
    "doc_id",
    "thread_id",
    "parent_id",
    "thread_template_id",
    "comment_flow_id",
    "dial",
    "persona_archetype_id",
    "author_role",
    "stance",
    "intent",
    "emotion",
    "topic_tags",
    "style_tags",
    "toxicity_flag",
    "pii_flag",
    "text",
    "notes",
}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def test_build_corpus_from_packs_writes_required_files(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"

    summary = build_corpus_from_packs(
        packs_dir=Path("packs"),
        corpus_dir=corpus_dir,
    )

    assert summary["reference_count"] >= 22
    assert summary["refined_count"] >= 22
    assert summary["generated_count"] == 0

    reference_path = corpus_dir / "reference.jsonl"
    refined_path = corpus_dir / "refined.jsonl"
    generated_path = corpus_dir / "generated.jsonl"
    manifest_path = corpus_dir / "manifest.json"

    assert reference_path.exists()
    assert refined_path.exists()
    assert generated_path.exists()
    assert manifest_path.exists()

    reference_rows = _read_jsonl(reference_path)
    refined_rows = _read_jsonl(refined_path)
    generated_rows = _read_jsonl(generated_path)

    assert len(reference_rows) == summary["reference_count"]
    assert len(refined_rows) == summary["refined_count"]
    assert len(generated_rows) == summary["generated_count"]

    first_reference = reference_rows[0]
    first_refined = refined_rows[0]
    assert REQUIRED_ROW_KEYS.issubset(first_reference.keys())
    assert REQUIRED_ROW_KEYS.issubset(first_refined.keys())
    assert first_reference["source_type"] == "reference"
    assert first_refined["source_type"] == "refined"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "corpus.manifest.v1"
    assert manifest["reference_count"] == len(reference_rows)
    assert manifest["refined_count"] == len(refined_rows)


def test_load_corpus_texts_reads_reference_and_refined(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"
    build_corpus_from_packs(packs_dir=Path("packs"), corpus_dir=corpus_dir)

    texts = load_corpus_texts(corpus_dir)

    assert texts
    assert len(texts) == len(set(texts))
    assert all(isinstance(row, str) and row.strip() for row in texts)


def test_load_corpus_texts_returns_empty_when_missing_dir(tmp_path: Path):
    assert load_corpus_texts(tmp_path / "missing-corpus") == []
