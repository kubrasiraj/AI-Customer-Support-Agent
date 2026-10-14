
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.refund_service import approve_or_reject_refund


def make_pending_refund():
    return SimpleNamespace(
        id=1,
        order_id=10,
        customer_id=5,
        amount=Decimal("100.00"),
        reason="Product arrived damaged",
        status="pending",
    )


def setup_refund_query(db, refund):
    query = MagicMock()
    query.filter.return_value = query
    query.with_for_update.return_value = query
    query.first.return_value = refund
    db.query.return_value = query


def test_admin_can_approve_pending_refund():
    db = MagicMock()
    refund = make_pending_refund()
    setup_refund_query(db, refund)

    result = approve_or_reject_refund(
        db=db,
        refund_id=1,
        reviewer_id=202,
        reviewer_role="admin",
        approved=True,
        note="Verified",
    )

    assert result.status == "approved"
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(refund)


def test_support_can_reject_pending_refund():
    db = MagicMock()
    refund = make_pending_refund()
    setup_refund_query(db, refund)

    result = approve_or_reject_refund(
        db=db,
        refund_id=1,
        reviewer_id=303,
        reviewer_role="support",
        approved=False,
        note="Policy requirements not met",
    )

    assert result.status == "rejected"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_customer_cannot_review_refund():
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        approve_or_reject_refund(
            db=db,
            refund_id=1,
            reviewer_id=101,
            reviewer_role="customer",
            approved=True,
            note=None,
        )

    assert exc.value.status_code == 403
    db.query.assert_not_called()


def test_missing_refund_raises_value_error():
    db = MagicMock()
    setup_refund_query(db, None)

    with pytest.raises(ValueError, match="Refund not found"):
        approve_or_reject_refund(
            db=db,
            refund_id=999,
            reviewer_id=202,
            reviewer_role="admin",
            approved=True,
            note=None,
        )

    db.rollback.assert_called_once()


def test_already_reviewed_refund_cannot_be_reviewed_again():
    db = MagicMock()
    refund = make_pending_refund()
    refund.status = "approved"
    setup_refund_query(db, refund)

    with pytest.raises(
        ValueError,
        match="Only pending refunds can be reviewed",
    ):
        approve_or_reject_refund(
            db=db,
            refund_id=1,
            reviewer_id=202,
            reviewer_role="admin",
            approved=False,
            note=None,
        )

    db.rollback.assert_called_once()
