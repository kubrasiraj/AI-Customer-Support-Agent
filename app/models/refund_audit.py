from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefundAudit(Base):
    __tablename__ = "refund_audits"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    refund_id: Mapped[int] = mapped_column(
        ForeignKey("refund_requests.id"),
        nullable=False,
        index=True,
    )

    reviewed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    reviewer_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    refund = relationship(
        "RefundRequest",
        backref="audit_logs",
    )

    reviewer = relationship(
        "User",
        backref="refund_audit_logs",
    )