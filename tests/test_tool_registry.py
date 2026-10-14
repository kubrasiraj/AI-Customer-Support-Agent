
from app.agent.tool_registry import get_available_tools
from app.tools.customer_tools import get_customer
from app.tools.order_tools import get_order, get_order_status
from app.tools.ticket_tools import get_ticket
from app.tools.refund_tools import check_refund_eligibility


def test_get_available_tools_returns_expected_tools():
    tools = get_available_tools()

    assert tools == [
        get_customer,
        get_order,
        get_order_status,
        get_ticket,
        check_refund_eligibility,
    ]


def test_get_available_tools_returns_fresh_list():
    first = get_available_tools()
    second = get_available_tools()

    assert first == second
    assert first is not second
