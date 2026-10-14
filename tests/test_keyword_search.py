from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.rag.keyword_search import keyword_search


def make_db(chunks):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = chunks
    return db


@pytest.mark.parametrize("query", ["", "  "])
def test_rejects_empty_query(query):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        keyword_search(make_db([]), query)


def test_returns_matching_chunks_ranked_by_keyword_score():
    chunks = [
        SimpleNamespace(
            id=1, document_id=10, chunk_index=0,
            content="refund policy return",
        ),
        SimpleNamespace(
            id=2, document_id=10, chunk_index=1,
            content="refund refund",
        ),
        SimpleNamespace(
            id=3, document_id=11, chunk_index=0,
            content="shipping delay",
        ),
    ]

    results = keyword_search(make_db(chunks), "refund policy")

    assert [item["chunk_id"] for item in results] == [1, 2]
    assert results[0]["keyword_score"] == 1.0
    assert results[1]["keyword_score"] == 0.5


def test_respects_top_k():
    chunks = [
        SimpleNamespace(
            id=i, document_id=1, chunk_index=i,
            content="refund policy",
        )
        for i in range(1, 4)
    ]

    results = keyword_search(make_db(chunks), "refund", top_k=2)

    assert len(results) == 2


def test_no_matching_terms_returns_empty_list():
    chunk = SimpleNamespace(
        id=1, document_id=1, chunk_index=0,
        content="shipping address",
    )

    assert keyword_search(make_db([chunk]), "refund") == []