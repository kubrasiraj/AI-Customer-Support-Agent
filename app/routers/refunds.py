from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_role,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.refund import (
    RefundApproval,
    RefundCreate,
    RefundListResponse,
    RefundResponse,
)
from app.services.refund_service import (
    approve_or_reject_refund,
    create_refund_request,
    get_customer_refunds,
    get_refund,
)


router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"],
)


@router.post(
    "",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_refund(
    data: RefundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a refund request for the authenticated customer.
    """

    try:
        return create_refund_request(
            db,
            current_user.id,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=RefundListResponse,
)
def get_my_refunds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all refunds belonging to the authenticated customer.
    """

    try:
        refunds = get_customer_refunds(
            db,
            current_user.id,
        )

        return RefundListResponse(
            items=refunds,
            total=len(refunds),
            page=1,
            page_size=len(refunds),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{refund_id}",
    response_model=RefundResponse,
)
def get_my_refund(
    refund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get one refund belonging to the authenticated customer.
    """

    refund = get_refund(
        db,
        refund_id,
        current_user.id,
    )

    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found",
        )

    return refund


@router.post(
    "/{refund_id}/approval",
    response_model=RefundResponse,
)
def review_refund(
    refund_id: int,
    data: RefundApproval,
    current_user: User = Depends(
        require_role("admin", "support")
    ),
    db: Session = Depends(get_db),
):
    """
    Approve or reject a pending refund.

    Only support and admin users can review refunds.
    """

    try:
        return approve_or_reject_refund(
            db=db,
            refund_id=refund_id,
            reviewer_id=current_user.id,
            reviewer_role=current_user.role,
            approved=data.approved,
            note=data.note,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )