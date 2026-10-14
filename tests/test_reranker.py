from unittest.mock import MagicMock

import pytest

import app.rag.reranker as module


@pytest.mark.parametrize("query", ["", "  "])
def test_reranker_rejects_empty_query(query):
    with pytest.raises(ValueError):
        module.rerank_results(query, [{"chunk_id": 1, "content": "Refund policy"}])


def test_reranker_returns_empty_list_for_no_results():
    assert module.rerank_results("refund policy", []) == []


def test_reranker_sorts_results_by_model_score(monkeypatch):
    fake_model = MagicMock()
    fake_model.predict.return_value = [0.2, 0.9]

    monkeypatch.setattr(module, "_reranker", fake_model, raising=False)

    results = [
        {"chunk_id": 1, "content": "Shipping policy"},
        {"chunk_id": 2, "content": "Refund policy"},
    ]

    ranked = module.rerank_results("refund", results, top_k=2)

    assert ranked[0]["chunk_id"] == 2
    assert ranked[1]["chunk_id"] == 1
    assert ranked[0]["rerank_score"] == pytest.approx(0.9)
    assert ranked[1]["rerank_score"] == pytest.approx(0.2)


def test_reranker_respects_top_k(monkeypatch):
    fake_model = MagicMock()
    fake_model.predict.return_value = [0.1, 0.9, 0.5]

    monkeypatch.setattr(module, "_reranker", fake_model, raising=False)

    results = [
        {"chunk_id": 1, "content": "First"},
        {"chunk_id": 2, "content": "Second"},
        {"chunk_id": 3, "content": "Third"},
    ]

    ranked = module.rerank_results("query", results, top_k=1)

    assert len(ranked) == 1
    assert ranked[0]["chunk_id"] == 2


def test_reranker_does_not_mutate_original_results(monkeypatch):
    fake_model = MagicMock()
    fake_model.predict.return_value = [0.8]

    monkeypatch.setattr(module, "_reranker", fake_model, raising=False)

    original = {"chunk_id": 1, "content": "Refund policy"}
    module.rerank_results("refund", [original])

    assert "rerank_score" not in original