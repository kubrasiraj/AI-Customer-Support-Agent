import pytest

from app.rag.query_transformer import transform_query


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_empty_questions_are_rejected(question):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        transform_query(question)


def test_lowercases_and_strips_question():
    assert transform_query("  REFUND POLICY  ") == "refund policy"


def test_removes_common_conversational_phrases():
    result = transform_query("Can I please get a refund?")
    assert result == "get a refund"


def test_normalizes_punctuation_and_whitespace():
    result = transform_query("Refunds!!!   for, damaged items?")
    assert result == "refunds for damaged items"


def test_returns_string():
    assert isinstance(transform_query("Where is my order?"), str)