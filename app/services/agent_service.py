
from fastapi import HTTPException
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.agent.agent import create_support_agent
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.services.rag_service import retrieve_customer_knowledge
from app.tools.customer_tools import get_customer
from app.tools.order_tools import get_order, get_order_status
from app.tools.ticket_tools import get_ticket
from app.tools.refund_tools import check_refund_eligibility



def create_database_tools(
    db: Session,
    authenticated_customer_id: int,
):
    @tool
    def customer_lookup() -> dict | None:
        """Look up the authenticated customer's own profile."""
        return get_customer(
            db=db,
            customer_id=authenticated_customer_id,
        )

    @tool
    def order_lookup(order_number: str) -> dict | None:
        """Look up an order belonging to the authenticated customer."""
        return get_order(
            db=db,
            order_number=order_number,
            customer_id=authenticated_customer_id,
        )

    @tool
    def order_status_lookup(order_number: str) -> str | None:
        """Get the status of the authenticated customer's own order."""
        return get_order_status(
            db=db,
            order_number=order_number,
            customer_id=authenticated_customer_id,
        )

    @tool
    def ticket_lookup(ticket_id: int) -> dict | None:
        """Look up a ticket belonging to the authenticated customer."""
        return get_ticket(
            db=db,
            ticket_id=ticket_id,
            customer_id=authenticated_customer_id,
        )

    @tool
    def refund_eligibility_check(
        order_number: str,
        reason: str,
    ) -> dict:
        """Check refund eligibility for the authenticated customer's order."""
        return check_refund_eligibility(
            db=db,
            order_number=order_number,
            reason=reason,
            customer_id=authenticated_customer_id,
        )

    @tool
    def support_knowledge_search(question: str) -> dict:
        """Search approved company policies and FAQs."""
        return retrieve_customer_knowledge(
            db=db,
            question=question,
        )

    return [
        customer_lookup,
        order_lookup,
        order_status_lookup,
        ticket_lookup,
        refund_eligibility_check,
        support_knowledge_search,
    ]


def run_support_agent(
    db: Session,
    user_id: int,
    question: str,
    conversation_id: int | None = None,
) -> dict:
    if not question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty.",
        )

    # 1. Resolve the authenticated user to their customer record.
    customer = (
        db.query(Customer)
        .filter(Customer.user_id == user_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="No customer profile is linked to this account.",
        )

    # 2. Load the requested conversation or create a new one.
    if conversation_id is None:
        conversation = Conversation(
            customer_id=customer.id,
            status="active",
        )
        db.add(conversation)
        db.flush()

    else:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.customer_id == customer.id,
            )
            .first()
        )

        if conversation is None:
            # Do not reveal whether another customer's conversation exists.
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        if conversation.status != "active":
            raise HTTPException(
                status_code=409,
                detail="This conversation is not active.",
            )

    # 3. Load previous messages in chronological order.
    previous_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    # 4. Save the new user message.
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=question.strip(),
    )
    db.add(user_message)
    db.flush()

    # 5. Convert stored messages to LangChain's message format.
    history = []

    for message in previous_messages:
        if message.role == "user":
            history.append({
                "role": "user",
                "content": message.content,
            })
        elif message.role in ("assistant", "ai"):
            history.append({
                "role": "assistant",
                "content": message.content,
            })

    # Add the current question after the earlier history.
    history.append({
        "role": "user",
        "content": question.strip(),
    })

    try:
        tools = create_database_tools(
            db=db,
            authenticated_customer_id=customer.id,

        )
        agent = create_support_agent(tools)

        # 6. Invoke the agent with the complete conversation history.
        result = agent.invoke({
            "messages": history,
        })

        messages = result.get("messages", [])

        if not messages:
            raise RuntimeError(
                "The agent returned no messages."
            )

        final_message = messages[-1]
        content = final_message.content

        if isinstance(content, str):
            answer = content.strip()
        else:
            answer = "".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
            ).strip()

        if not answer:
            raise RuntimeError(
                "The agent returned an empty answer."
            )

        # 7. Collect tool names for API transparency and testing.
        tools_used = []

        for message in messages:
            for tool_call in getattr(message, "tool_calls", []):
                tool_name = tool_call.get("name")

                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)

        # 8. Save the assistant's final response.
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )
        db.add(assistant_message)

        conversation.updated_at = __import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        )

        # Persist the conversation and both messages.
        db.commit()

        return {
            "answer": answer,
            "conversation_id": conversation.id,
            "tools_used": tools_used,
        }

    except Exception:
        db.rollback()
        raise

