
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import llm_service


def test_generate_answer_returns_stripped_text(monkeypatch):
    mock_create = MagicMock()
    mock_create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="  Your refund has been approved.  "
                )
            )
        ]
    )

    monkeypatch.setattr(
        llm_service.client.chat.completions,
        "create",
        mock_create,
    )

    result = llm_service.generate_answer(
        system_prompt="You are a customer support assistant.",
        user_prompt="What is the status of my refund?",
    )

    assert result == "Your refund has been approved."

    mock_create.assert_called_once_with(
        model=llm_service.settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a customer support assistant.",
            },
            {
                "role": "user",
                "content": "What is the status of my refund?",
            },
        ],
        temperature=0,
    )


def test_generate_answer_raises_when_response_is_empty(monkeypatch):
    mock_create = MagicMock()
    mock_create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=None)
            )
        ]
    )

    monkeypatch.setattr(
        llm_service.client.chat.completions,
        "create",
        mock_create,
    )

    with pytest.raises(
        ValueError,
        match="Groq returned an empty response",
    ):
        llm_service.generate_answer(
            system_prompt="You are a customer support assistant.",
            user_prompt="Where is my order?",
        )

