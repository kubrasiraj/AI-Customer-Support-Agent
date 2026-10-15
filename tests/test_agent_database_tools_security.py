from unittest.mock import patch

from app.services.agent_service import create_database_tools


def test_database_tools_use_authenticated_customer_id():
    authenticated_customer_id = 42
    fake_db = object()

    with (
        patch("app.services.agent_service.get_customer") as get_customer,
        patch("app.services.agent_service.get_order") as get_order,
        patch("app.services.agent_service.get_order_status") as get_order_status,
        patch("app.services.agent_service.get_ticket") as get_ticket,
        patch(
            "app.services.agent_service.check_refund_eligibility"
        ) as check_refund,
        patch(
            "app.services.agent_service.retrieve_customer_knowledge"
        ) as search_knowledge,
    ):
        tools = create_database_tools(
            db=fake_db,
            authenticated_customer_id=authenticated_customer_id,
        )

        tools_by_name = {item.name: item for item in tools}

        tools_by_name["customer_lookup"].invoke({})
        tools_by_name["order_lookup"].invoke(
            {"order_number": "ORD-123"}
        )
        tools_by_name["order_status_lookup"].invoke(
            {"order_number": "ORD-123"}
        )
        tools_by_name["ticket_lookup"].invoke({"ticket_id": 7})
        tools_by_name["refund_eligibility_check"].invoke(
            {"order_number": "ORD-123", "reason": "damaged item"}
        )
        tools_by_name["support_knowledge_search"].invoke(
            {"question": "What is the refund policy?"}
        )

        get_customer.assert_called_once_with(
            db=fake_db, customer_id=authenticated_customer_id
        )
        get_order.assert_called_once_with(
            db=fake_db,
            order_number="ORD-123",
            customer_id=authenticated_customer_id,
        )
        get_order_status.assert_called_once_with(
            db=fake_db,
            order_number="ORD-123",
            customer_id=authenticated_customer_id,
        )
        get_ticket.assert_called_once_with(
            db=fake_db,
            ticket_id=7,
            customer_id=authenticated_customer_id,
        )
        check_refund.assert_called_once_with(
            db=fake_db,
            order_number="ORD-123",
            reason="damaged item",
            customer_id=authenticated_customer_id,
        )
        search_knowledge.assert_called_once_with(
            db=fake_db,
            question="What is the refund policy?",
        )
