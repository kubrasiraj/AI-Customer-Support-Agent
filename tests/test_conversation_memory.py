
from app.routers import agent as agent_router


def test_agent_forwards_new_conversation_request(
    client,
    monkeypatch,
):
    captured = {}

    def mock_run_support_agent(
        db,
        user_id,
        question,
        conversation_id,
    ):
        captured.update(
            user_id=user_id,
            question=question,
            conversation_id=conversation_id,
        )

        return {
            "answer": "How can I help?",
            "conversation_id": 42,
            "tools_used": [],
        }

    monkeypatch.setattr(
        agent_router,
        "run_support_agent",
        mock_run_support_agent,
    )

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 200
    assert captured["user_id"] == 101
    assert captured["question"] == "Hello"
    assert captured["conversation_id"] is None
    assert response.json()["conversation_id"] == 42
