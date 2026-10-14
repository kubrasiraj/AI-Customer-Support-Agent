from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import app.services.agent_service as service
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message


class FakeQuery:
    """Small database-query mock for agent service tests."""

    def __init__(self, db, model):
        self.db = db
        self.model = model

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        if self.model is Customer:
            return self.db.customer

        if self.model is Conversation:
            return self.db.existing_conversation

        return None

    def all(self):
        if self.model is Message:
            return self.db.previous_messages

        return []


class FakeDB:
    """In-memory database behavior; no real database connection."""

    def __init__(
        self,
        customer=None,
        conversation=None,
        previous_messages=None,
    ):
        self.customer = customer
        self.existing_conversation = conversation
        self.previous_messages = previous_messages or []

        self.added = []
        self.committed = False
        self.rolled_back = False
        self.flush_count = 0

    def query(self, model):
        return FakeQuery(self, model)

    def add(self, obj):
        self.added.append(obj)

        if isinstance(obj, Conversation) and obj.id is None:
            obj.id = 501

    def flush(self):
        self.flush_count += 1

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def make_customer():
    return SimpleNamespace(id=20, user_id=10)


def make_conversation(
    conversation_id=55,
    customer_id=20,
    status="active",
):
    return Conversation(
        id=conversation_id,
        customer_id=customer_id,
        status=status,
    )


def make_message(role, content, message_id=1):
    return SimpleNamespace(
        id=message_id,
        role=role,
        content=content,
        created_at=None,
    )


def fake_agent_result(answer="Your order is being processed."):
    return {
        "messages": [
            SimpleNamespace(
                content=answer,
                tool_calls=[
                    {"name": "order_lookup"},
                    {"name": "customer_lookup"},
                    {"name": "order_lookup"},
                ],
            ),
            SimpleNamespace(
                content=answer,
                tool_calls=[],
            ),
        ]
    }


def install_fake_agent(monkeypatch, result=None, error=None):
    agent = MagicMock()

    if error is not None:
        agent.invoke.side_effect = error
    else:
        agent.invoke.return_value = (
            result if result is not None else fake_agent_result()
        )

    create_agent = MagicMock(return_value=agent)
    monkeypatch.setattr(service, "create_support_agent", create_agent)

    return create_agent, agent


def test_blank_question_returns_422_without_database_queries():
    db = FakeDB()

    with pytest.raises(HTTPException) as exc:
        service.run_support_agent(
            db=db,
            user_id=10,
            question="   ",
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "Question cannot be empty."
    assert db.flush_count == 0


def test_missing_customer_profile_returns_404():
    db = FakeDB(customer=None)

    with pytest.raises(HTTPException) as exc:
        service.run_support_agent(
            db=db,
            user_id=999,
            question="Where is my order?",
        )

    assert exc.value.status_code == 404
    assert "No customer profile" in exc.value.detail


def test_missing_or_foreign_conversation_returns_404():
    db = FakeDB(
        customer=make_customer(),
        conversation=None,
    )

    with pytest.raises(HTTPException) as exc:
        service.run_support_agent(
            db=db,
            user_id=10,
            question="Check my order",
            conversation_id=999,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Conversation not found."


def test_inactive_conversation_returns_409():
    conversation = make_conversation(status="closed")
    db = FakeDB(
        customer=make_customer(),
        conversation=conversation,
    )

    with pytest.raises(HTTPException) as exc:
        service.run_support_agent(
            db=db,
            user_id=10,
            question="I need help",
            conversation_id=55,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "This conversation is not active."


def test_successful_response_saves_messages_and_commits(monkeypatch):
    customer = make_customer()
    conversation = make_conversation()
    previous_messages = [
        make_message("user", "Where is my order?", 1),
        make_message("assistant", "Please share your order number.", 2),
        make_message("system", "Internal note", 3),
    ]

    db = FakeDB(
        customer=customer,
        conversation=conversation,
        previous_messages=previous_messages,
    )

    create_agent, agent = install_fake_agent(monkeypatch)

    result = service.run_support_agent(
        db=db,
        user_id=10,
        question="  ORD-123 status?  ",
        conversation_id=55,
    )

    assert result["answer"] == "Your order is being processed."
    assert result["conversation_id"] == 55
    assert result["tools_used"] == ["order_lookup", "customer_lookup"]

    invocation = agent.invoke.call_args.args[0]
    assert invocation["messages"] == [
        {"role": "user", "content": "Where is my order?"},
        {
            "role": "assistant",
            "content": "Please share your order number.",
        },
        {"role": "user", "content": "ORD-123 status?"},
    ]

    saved_user_messages = [
        obj for obj in db.added
        if isinstance(obj, Message) and obj.role == "user"
    ]
    saved_assistant_messages = [
        obj for obj in db.added
        if isinstance(obj, Message) and obj.role == "assistant"
    ]

    assert len(saved_user_messages) == 1
    assert saved_user_messages[0].content == "ORD-123 status?"
    assert len(saved_assistant_messages) == 1
    assert saved_assistant_messages[0].content == (
        "Your order is being processed."
    )

    assert db.committed is True
    assert db.rolled_back is False
    create_agent.assert_called_once()


def test_new_conversation_is_created_for_customer(monkeypatch):
    db = FakeDB(customer=make_customer())
    install_fake_agent(monkeypatch)

    result = service.run_support_agent(
        db=db,
        user_id=10,
        question="Hello",
    )

    assert result["conversation_id"] == 501

    conversations = [
        obj for obj in db.added
        if isinstance(obj, Conversation)
    ]

    assert len(conversations) == 1
    assert conversations[0].customer_id == 20
    assert conversations[0].status == "active"
    assert db.committed is True


def test_list_content_extracts_text_blocks(monkeypatch):
    db = FakeDB(
        customer=make_customer(),
        conversation=make_conversation(),
    )

    result_data = {
        "messages": [
            SimpleNamespace(
                content=[
                    {"type": "text", "text": "Your refund "},
                    {"type": "image", "url": "ignored"},
                    {"type": "text", "text": "is under review."},
                ],
                tool_calls=[],
            )
        ]
    }

    install_fake_agent(monkeypatch, result=result_data)

    result = service.run_support_agent(
        db=db,
        user_id=10,
        question="Refund status?",
        conversation_id=55,
    )

    assert result["answer"] == "Your refund is under review."
    assert db.committed is True


def test_empty_agent_messages_roll_back(monkeypatch):
    db = FakeDB(
        customer=make_customer(),
        conversation=make_conversation(),
    )
    install_fake_agent(monkeypatch, result={"messages": []})

    with pytest.raises(RuntimeError, match="no messages"):
        service.run_support_agent(
            db=db,
            user_id=10,
            question="Help me",
            conversation_id=55,
        )

    assert db.rolled_back is True
    assert db.committed is False


def test_empty_agent_answer_rolls_back(monkeypatch):
    db = FakeDB(
        customer=make_customer(),
        conversation=make_conversation(),
    )
    install_fake_agent(
        monkeypatch,
        result={
            "messages": [
                SimpleNamespace(content="   ", tool_calls=[])
            ]
        },
    )

    with pytest.raises(RuntimeError, match="empty answer"):
        service.run_support_agent(
            db=db,
            user_id=10,
            question="Help me",
            conversation_id=55,
        )

    assert db.rolled_back is True
    assert db.committed is False


def test_agent_exception_rolls_back_and_propagates(monkeypatch):
    db = FakeDB(
        customer=make_customer(),
        conversation=make_conversation(),
    )

    install_fake_agent(
        monkeypatch,
        error=RuntimeError("Simulated agent failure"),
    )

    with pytest.raises(RuntimeError, match="Simulated agent failure"):
        service.run_support_agent(
            db=db,
            user_id=10,
            question="Check my order",
            conversation_id=55,
        )

    assert db.rolled_back is True
    assert db.committed is False