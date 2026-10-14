from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.services.semantic_search as module


def test_cosine_similarity_identical_vectors():
    assert module.cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert module.cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_returns_zero():
    assert module.cosine_similarity([0, 0], [1, 2]) == 0.0


def test_cosine_similarity_dimension_mismatch_raises():
    with pytest.raises(ValueError, match="same dimensions"):
        module.cosine_similarity([1], [1, 2])


@pytest.mark.parametrize("query", ["", " "])
def test_semantic_search_rejects_empty_query(query):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        module.semantic_search(MagicMock(), query)


def test_semantic_search_sorts_results_and_limits_top_k(monkeypatch):
    monkeypatch.setattr(
        module,
        "generate_embedding",
        lambda text: [1.0, 0.0],
    )

    chunks = [
        SimpleNamespace(
            id=1, document_id=2, chunk_index=0,
            content="low", embedding=[0.0, 1.0],
        ),
        SimpleNamespace(
            id=2, document_id=2, chunk_index=1,
            content="high", embedding=[1.0, 0.0],
        ),
    ]

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = chunks

    result = module.semantic_search(db, "query", top_k=1)

    assert len(result) == 1
    assert result[0]["chunk_id"] == 2
    assert result[0]["score"] == pytest.approx(1.0)