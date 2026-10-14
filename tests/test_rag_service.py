from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import rag_service


def test_answer_customer_question_rejects_empty_question():
    with pytest.raises(ValueError, match="Question cannot be empty"):
        rag_service.answer_customer_question(
            MagicMock(),
            "   ",
        )


def test_answer_customer_question_when_no_results(monkeypatch):
    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: [],
    )

    result = rag_service.answer_customer_question(
        MagicMock(),
        "Where is my order?",
    )

    assert result["sources"] == []
    assert "could not find enough information" in result["answer"]


def test_answer_customer_question_when_context_is_empty(monkeypatch):
    results = [
        {
            "chunk_id": 1,
            "document_id": 2,
            "semantic_score": 0.9,
            "keyword_score": 0.8,
            "hybrid_score": 0.85,
            "rerank_score": 0.95,
        }
    ]

    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "compress_context",
        lambda **kwargs: "",
    )

    result = rag_service.answer_customer_question(
        MagicMock(),
        "What is the refund policy?",
    )

    assert result["sources"] == []
    assert "could not find enough information" in result["answer"]


def test_answer_customer_question_success(monkeypatch):
    results = [
        {
            "chunk_id": 1,
            "document_id": 2,
            "semantic_score": 0.91234,
            "keyword_score": 0.81234,
            "hybrid_score": 0.85234,
            "rerank_score": 0.95234,
        }
    ]

    chain = MagicMock()
    chain.invoke.return_value = SimpleNamespace(
        content="Refunds are available under the refund policy."
    )

    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: "transformed question",
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "compress_context",
        lambda **kwargs: "Refund policy evidence",
    )
    monkeypatch.setattr(
        rag_service,
        "create_rag_chain",
        lambda: chain,
    )

    result = rag_service.answer_customer_question(
        MagicMock(),
        "Can I get a refund?",
    )

    assert result["answer"] == (
        "Refunds are available under the refund policy."
    )
    assert result["sources"][0]["chunk_id"] == 1
    assert result["sources"][0]["document_id"] == 2
    assert result["sources"][0]["semantic_score"] == 0.9123
    chain.invoke.assert_called_once_with(
        {
            "context": "Refund policy evidence",
            "question": "Can I get a refund?",
        }
    )


def test_answer_customer_question_with_multimodal_content(monkeypatch):
    results = [
        {
            "chunk_id": 1,
            "document_id": 2,
            "semantic_score": 0.9,
            "keyword_score": 0.8,
            "hybrid_score": 0.85,
            "rerank_score": 0.95,
        }
    ]

    chain = MagicMock()
    chain.invoke.return_value = SimpleNamespace(
        content=[
            {"type": "text", "text": "Refund "},
            {"type": "image", "image": "ignored"},
            {"type": "text", "text": "policy explained."},
        ]
    )

    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "compress_context",
        lambda **kwargs: "Refund policy evidence",
    )
    monkeypatch.setattr(
        rag_service,
        "create_rag_chain",
        lambda: chain,
    )

    result = rag_service.answer_customer_question(
        MagicMock(),
        "Explain refunds.",
    )

    assert result["answer"] == "Refund policy explained."


def test_retrieve_customer_knowledge_rejects_empty_question():
    result = rag_service.retrieve_customer_knowledge(
        MagicMock(),
        "   ",
    )

    assert result["found"] is False
    assert result["context"] == ""
    assert result["sources"] == []
    assert result["message"] == "The question cannot be empty."


def test_retrieve_customer_knowledge_when_no_results(monkeypatch):
    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: [],
    )

    result = rag_service.retrieve_customer_knowledge(
        MagicMock(),
        "What is the return policy?",
    )

    assert result["found"] is False
    assert result["context"] == ""
    assert result["sources"] == []


def test_retrieve_customer_knowledge_when_reranking_returns_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: [{"chunk_id": 1}],
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: [],
    )

    result = rag_service.retrieve_customer_knowledge(
        MagicMock(),
        "What is the return policy?",
    )

    assert result["found"] is False
    assert result["sources"] == []
    assert "No sufficiently relevant" in result["message"]


def test_retrieve_customer_knowledge_when_context_is_empty(
    monkeypatch,
):
    results = [{"chunk_id": 1, "document_id": 2}]

    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: question,
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "compress_context",
        lambda **kwargs: "   ",
    )

    result = rag_service.retrieve_customer_knowledge(
        MagicMock(),
        "What is the return policy?",
    )

    assert result["found"] is False
    assert result["context"] == ""
    assert result["sources"] == []


def test_retrieve_customer_knowledge_success(monkeypatch):
    results = [
        {"chunk_id": 10, "document_id": 3},
        {"chunk_id": 11, "document_id": 3},
    ]

    monkeypatch.setattr(
        rag_service,
        "transform_query",
        lambda question: "transformed question",
    )
    monkeypatch.setattr(
        rag_service,
        "hybrid_search",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "rerank_results",
        lambda **kwargs: results,
    )
    monkeypatch.setattr(
        rag_service,
        "compress_context",
        lambda **kwargs: "Relevant refund policy evidence.",
    )

    result = rag_service.retrieve_customer_knowledge(
        MagicMock(),
        "What is the refund policy?",
    )

    assert result["found"] is True
    assert result["context"] == "Relevant refund policy evidence."
    assert result["sources"] == [
        {"chunk_id": 10, "document_id": 3},
        {"chunk_id": 11, "document_id": 3},
    ]
    assert "Answer only claims supported by this evidence." in (
        result["message"]
    )