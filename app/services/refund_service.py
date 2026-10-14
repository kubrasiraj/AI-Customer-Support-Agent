from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.models.order import Order
from app.models.refund_audit import RefundAudit
from app.models.refund_request import RefundRequest
from app.schemas.refund import RefundCreate


def get_customer_by_user_id(
    db: Session,
    user_id: int,
) -> Customer | None:
    """Find the customer profile linked to a user."""

    return (
        db.query(Customer)
        .filter(Customer.user_id == user_id)
        .first()
    )


def get_customer_refund(
    db: Session,
    refund_id: int,
    user_id: int,
) -> RefundRequest | None:
    """Find a refund only if it belongs to the authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        return None

    return (
        db.query(RefundRequest)
        .filter(
            RefundRequest.id == refund_id,
            RefundRequest.customer_id == customer.id,
        )
        .first()
    )


def create_refund_request(
    db: Session,
    user_id: int,
    data: RefundCreate,
) -> RefundRequest:
    """Create a refund request for an authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        raise ValueError("Customer profile not found")

    # Make sure the order belongs to this customer.
    order = (
        db.query(Order)
        .filter(
            Order.id == data.order_id,
            Order.customer_id == customer.id,
        )
        .first()
    )

    if not order:
        raise ValueError("Order not found")

    # Refund cannot be greater than the order total.
    if data.amount > order.total_amount:
        raise ValueError(
            "Refund amount cannot exceed order total"
        )

    refund = RefundRequest(
        order_id=order.id,
        customer_id=customer.id,
        amount=data.amount,
        reason=data.reason,
        status="pending",
    )

    db.add(refund)
    db.commit()
    db.refresh(refund)

    return refund


def get_customer_refunds(
    db: Session,
    user_id: int,
) -> list[RefundRequest]:
    """Return all refunds belonging to the authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        raise ValueError("Customer profile not found")

    return (
        db.query(RefundRequest)
        .filter(
            RefundRequest.customer_id == customer.id
        )
        .order_by(
            RefundRequest.created_at.desc()
        )
        .all()
    )


def get_refund(
    db: Session,
    refund_id: int,
    user_id: int,
) -> RefundRequest | None:
    """Return one refund owned by the authenticated customer."""

    return get_customer_refund(
        db,
        refund_id,
        user_id,
    )


def approve_or_reject_refund(
    db: Session,
    refund_id: int,
    reviewer_id: int,
    reviewer_role: str,
    approved: bool,
    note: str | None,
) -> RefundRequest:
    """
    Review a pending refund and record the decision
    in the audit table within the same transaction.
    """

    # Defense in depth: only authorized reviewer roles.
    if reviewer_role not in {"admin", "support"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to review refunds.",
        )

    try:
        # Lock this row so concurrent reviewers cannot
        # both approve or reject the same pending request.
        refund = (
            db.query(RefundRequest)
            .filter(RefundRequest.id == refund_id)
            .with_for_update()
            .first()
        )

        if refund is None:
            raise ValueError("Refund not found")

        if refund.status != "pending":
            raise ValueError(
                "Only pending refunds can be reviewed"
            )

        # Record the review decision.
        if approved:
            refund.status = "approved"
            action = "approved"
        else:
            refund.status = "rejected"
            action = "rejected"

        audit = RefundAudit(
            refund_id=refund.id,
            reviewed_by=reviewer_id,
            reviewer_role=reviewer_role,
            action=action,
            note=note,
        )

        db.add(audit)

        # Save refund status and audit record together.
        db.commit()
        db.refresh(refund)

        return refund

    except Exception:
        db.rollback()
        raise

