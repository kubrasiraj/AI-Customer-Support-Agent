from unittest.mock import MagicMock

import pytest

import app.rag.hybrid_search as module


@pytest.mark.parametrize("query", ["", "  "])
def test_rejects_empty_query(query):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        module.hybrid_search(MagicMock(), query)


def test_combines_semantic_and_keyword_scores(monkeypatch):
    monkeypatch.setattr(
        module,
        "semantic_search",
        lambda **kwargs: [
            {
                "chunk_id": 1,
                "document_id": 2,
                "chunk_index": 0,
                "content": "A",
                "score": 0.8,
            }
        ],
    )

    monkeypatch.setattr(
        module,
        "keyword_search",
        lambda **kwargs: [
            {
                "chunk_id": 1,
                "document_id": 2,
                "chunk_index": 0,
                "content": "A",
                "keyword_score": 0.5,
            },
            {
                "chunk_id": 2,
                "document_id": 3,
                "chunk_index": 1,
                "content": "B",
                "keyword_score": 1.0,
            },
        ],
    )

    results = module.hybrid_search(MagicMock(), "question", top_k=5)
    by_id = {item["chunk_id"]: item for item in results}

    assert by_id[1]["hybrid_score"] == pytest.approx(0.71)
    assert by_id[2]["hybrid_score"] == pytest.approx(0.30)
    assert by_id[2]["semantic_score"] == 0.0


def test_sorts_by_hybrid_score_and_limits_results(monkeypatch):
    monkeypatch.setattr(
        module,
        "semantic_search",
        lambda **kwargs: [
            {
                "chunk_id": 1, "document_id": 1,
                "chunk_index": 0, "content": "low", "score": 0.1,
            },
            {
                "chunk_id": 2, "document_id": 1,
                "chunk_index": 1, "content": "high", "score": 0.9,
            },
        ],
    )

    monkeypatch.setattr(module, "keyword_search", lambda **kwargs: [])

    result = module.hybrid_search(MagicMock(), "q", top_k=1)

    assert len(result) == 1
    assert result[0]["chunk_id"] == 2