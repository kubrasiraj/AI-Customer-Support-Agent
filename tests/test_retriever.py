from unittest.mock import MagicMock

import app.services.retriever as module


def test_retriever_keeps_results_above_minimum_score(monkeypatch):
    monkeypatch.setattr(
        module,
        "semantic_search",
        lambda *args, **kwargs: [
            {"chunk_id": 1, "score": 0.9},
            {"chunk_id": 2, "score": 0.3},
            {"chunk_id": 3, "score": 0.7},
        ],
    )

    results = module.retrieve_relevant_chunks(
        MagicMock(),
        "refund policy",
        min_score=0.5,
    )

    assert [item["chunk_id"] for item in results] == [1, 3]


def test_retriever_returns_empty_list_when_nothing_matches(monkeypatch):
    monkeypatch.setattr(
        module,
        "semantic_search",
        lambda *args, **kwargs: [
            {"chunk_id": 1, "score": 0.2}
        ],
    )

    results = module.retrieve_relevant_chunks(
        MagicMock(),
        "refund policy",
        min_score=0.5,
    )

    assert results == []