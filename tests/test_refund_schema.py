
import pytest
from pydantic import ValidationError

from app.schemas.refund import RefundCreate, RefundApproval


def test_valid_refund_request():
    data = RefundCreate(
        order_id=1,
        amount="100.00",
        reason="Product arrived damaged",
    )

    assert data.order_id == 1
    assert data.amount == 100
    assert data.reason == "Product arrived damaged"


@pytest.mark.parametrize(
    "payload",
    [
        {"order_id": 0, "amount": "100.00", "reason": "Damaged product"},
        {"order_id": 1, "amount": "0", "reason": "Damaged product"},
        {"order_id": 1, "amount": "-10", "reason": "Damaged product"},
        {"order_id": 1, "amount": "100.00", "reason": "bad"},
    ],
)
def test_invalid_refund_request_is_rejected(payload):
    with pytest.raises(ValidationError):
        RefundCreate(**payload)


def test_refund_approval_accepts_optional_note():
    approval = RefundApproval(
        approved=True,
        note="Reviewed by support",
    )

    assert approval.approved is True
    assert approval.note == "Reviewed by support"


def test_refund_approval_rejects_overlong_note():
    with pytest.raises(ValidationError):
        RefundApproval(
            approved=False,
            note="x" * 1001,
        )
