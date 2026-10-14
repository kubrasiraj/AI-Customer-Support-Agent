from app.tools.customer_tools import get_customer
from app.tools.order_tools import (
    get_order,
    get_order_status,
)
from app.tools.ticket_tools import get_ticket
from app.tools.refund_tools import check_refund_eligibility


def get_available_tools() -> list:
    """
    Return the tools available to the support agent.
    """

    return [
        get_customer,
        get_order,
        get_order_status,
        get_ticket,
        check_refund_eligibility,
    ]