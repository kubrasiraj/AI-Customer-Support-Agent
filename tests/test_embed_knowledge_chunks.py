from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.services.embed_knowledge_chunks as module


def test_embeds_all_document_chunks(monkeypatch):
    chunks = [
        SimpleNamespace(content="Refund policy", embedding=None),
        SimpleNamespace(content="Shipping policy", embedding=None),
    ]

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = chunks

    def fake_embedding(content):
        return [0.1, 0.2, 0.3] if content == "Refund policy" else [0.4, 0.5, 0.6]

    monkeypatch.setattr(module, "generate_embedding", fake_embedding)

    result = module.embed_knowledge_chunks(db, document_id=10)

    assert result == 2
    assert chunks[0].embedding == [0.1, 0.2, 0.3]
    assert chunks[1].embedding == [0.4, 0.5, 0.6]
    db.commit.assert_called_once()


def test_raises_when_document_has_no_chunks():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with pytest.raises(ValueError):
        module.embed_knowledge_chunks(db, document_id=999)

    db.commit.assert_not_called()


def test_embedding_failure_does_not_commit(monkeypatch):
    chunks = [
        SimpleNamespace(content="Refund policy", embedding=None)
    ]

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = chunks

    def fail_embedding(_content):
        raise RuntimeError("Embedding failed")

    monkeypatch.setattr(module, "generate_embedding", fail_embedding)

    with pytest.raises(RuntimeError, match="Embedding failed"):
        module.embed_knowledge_chunks(db, document_id=10)

    db.commit.assert_not_called()