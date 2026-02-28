from pathlib import Path

import pytest

from project_dream.kb_index import build_index, retrieve_context, search
from project_dream.pack_service import load_packs


def test_search_filters_board_and_kind():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    index = build_index(packs)

    results = search(
        index,
        query="illegal_trade",
        filters={"board_id": "B07", "kind": "board"},
        top_k=3,
    )

    assert results
    assert results[0]["item_id"] == "B07"
    assert all(row["board_id"] == "B07" for row in results)
    assert all(row["kind"] == "board" for row in results)
    assert "score_sparse" in results[0]
    assert "score_dense" in results[0]
    assert "score_hybrid" in results[0]


def test_search_filters_zone_and_persona():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    index = build_index(packs)

    results = search(
        index,
        query="거래",
        filters={"zone_id": "D", "kind": "persona"},
        top_k=10,
    )

    assert results
    assert all(row["zone_id"] == "D" for row in results)
    assert all(row["kind"] == "persona" for row in results)
    assert any(row["item_id"] == "P07" for row in results)


def test_retrieve_context_returns_bundle_and_corpus():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    index = build_index(packs)

    result = retrieve_context(
        index,
        task="거래 사기 의혹 증거 확인",
        seed="중계망 먹통 사건",
        board_id="B07",
        zone_id="D",
        persona_ids=["P07", "P08"],
        top_k=2,
    )

    bundle = result["bundle"]
    corpus = result["corpus"]

    assert bundle["board_id"] == "B07"
    assert bundle["zone_id"] == "D"
    assert set(bundle["persona_ids"]) == {"P07", "P08"}
    assert set(bundle["sections"]) == {"evidence", "policy", "organization", "hierarchy"}
    assert bundle["sections"]["policy"]
    assert any(row["kind"] == "rule" for row in bundle["sections"]["policy"])
    assert corpus
    assert any("장터기둥" in text or "B07" in text for text in corpus)


def test_build_index_includes_ingested_corpus_passages(tmp_path: Path):
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "reference.jsonl").write_text(
        '{"board_id":"B07","zone_id":"D","doc_id":"DOC-REF-001","source_type":"reference","text":"INGEST-CTX-B07"}\n',
        encoding="utf-8",
    )
    (corpus_dir / "refined.jsonl").write_text("", encoding="utf-8")
    (corpus_dir / "generated.jsonl").write_text("", encoding="utf-8")

    index = build_index(packs, corpus_dir=corpus_dir)
    results = search(
        index,
        query="INGEST-CTX-B07",
        filters={"kind": "corpus", "board_id": "B07"},
        top_k=3,
    )

    assert results
    assert results[0]["kind"] == "corpus"
    assert results[0]["source_type"] == "reference"


def test_retrieve_context_includes_ingested_corpus_when_available(tmp_path: Path):
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "reference.jsonl").write_text(
        '{"board_id":"B07","zone_id":"D","doc_id":"DOC-REF-002","source_type":"reference","text":"INGEST-EVIDENCE-B07"}\n',
        encoding="utf-8",
    )
    (corpus_dir / "refined.jsonl").write_text("", encoding="utf-8")
    (corpus_dir / "generated.jsonl").write_text("", encoding="utf-8")

    index = build_index(packs, corpus_dir=corpus_dir)
    result = retrieve_context(
        index,
        task="거래 사기 의혹 증거 확인",
        seed="중계망 먹통 사건",
        board_id="B07",
        zone_id="D",
        persona_ids=["P07"],
        top_k=3,
    )

    assert any("INGEST-EVIDENCE-B07" in text for text in result["corpus"])


def test_search_hybrid_recovers_spacing_variant_with_dense_signal():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    index = build_index(packs)

    # board B17 meme contains "정렬이진실". query uses spacing variant.
    results = search(
        index,
        query="정렬이 진실",
        filters={"kind": "board"},
        top_k=3,
    )

    assert results
    assert results[0]["item_id"] == "B17"
    assert float(results[0]["score_dense"]) > 0.0
    assert float(results[0]["score_hybrid"]) >= float(results[0]["score_sparse"])


def test_build_index_supports_sqlite_vector_backend(tmp_path: Path):
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    vector_db_path = tmp_path / "kb-vectors.sqlite3"
    index = build_index(
        packs,
        vector_backend="sqlite",
        vector_db_path=vector_db_path,
    )

    results = search(
        index,
        query="정렬이 진실",
        filters={"kind": "board"},
        top_k=3,
    )

    assert vector_db_path.exists()
    assert results
    assert results[0]["item_id"] == "B17"
    assert float(results[0]["score_dense"]) > 0.0


def test_search_top_result_is_consistent_between_memory_and_sqlite_backend(tmp_path: Path):
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)
    index_memory = build_index(packs, vector_backend="memory")
    index_sqlite = build_index(
        packs,
        vector_backend="sqlite",
        vector_db_path=tmp_path / "kb-vectors.sqlite3",
    )

    memory_results = search(
        index_memory,
        query="정렬이 진실",
        filters={"kind": "board"},
        top_k=1,
    )
    sqlite_results = search(
        index_sqlite,
        query="정렬이 진실",
        filters={"kind": "board"},
        top_k=1,
    )

    assert memory_results
    assert sqlite_results
    assert memory_results[0]["item_id"] == sqlite_results[0]["item_id"]


def test_build_index_rejects_unknown_vector_backend():
    packs = load_packs(Path("packs"), enforce_phase1_minimums=True)

    with pytest.raises(ValueError):
        build_index(packs, vector_backend="unknown")
