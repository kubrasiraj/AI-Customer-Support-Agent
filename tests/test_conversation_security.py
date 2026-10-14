
from app.routers import agent as agent_router


def test_agent_receives_authenticated_user_id(
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
        captured["user_id"] = user_id
        captured["question"] = question
        captured["conversation_id"] = conversation_id

        return {
            "answer": "Your order is being processed.",
            "conversation_id": 7,
            "tools_used": [],
        }

    monkeypatch.setattr(
        agent_router,
        "run_support_agent",
        mock_run_support_agent,
    )

    response = client.post(
        "/agent/ask",
        json={
            "question": "Where is my order?",
            "conversation_id": 7,
        },
    )

    assert response.status_code == 200
    assert captured["user_id"] == 101
    assert captured["question"] == "Where is my order?"
    assert captured["conversation_id"] == 7
