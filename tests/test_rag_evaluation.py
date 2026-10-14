
import pytest
from pydantic import ValidationError

from app.schemas.rag import RAGQuestion


def test_rag_question_accepts_valid_question():
    data = RAGQuestion(
        question="What is the refund policy?"
    )

    assert data.question == "What is the refund policy?"


@pytest.mark.parametrize(
    "question",
    ["", "   "],
)
def test_rag_question_rejects_empty_question(question):
    with pytest.raises(ValidationError):
        RAGQuestion(question="")


def test_rag_question_rejects_question_over_max_length():
    with pytest.raises(ValidationError):
        RAGQuestion(question="x" * 2001)
