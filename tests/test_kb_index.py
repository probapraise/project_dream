from pathlib import Path

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
