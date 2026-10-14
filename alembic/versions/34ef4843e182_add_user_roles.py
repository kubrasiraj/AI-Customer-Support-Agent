"""add user roles

Revision ID: 34ef4843e182
Revises: adb4d4e536b2
Create Date: 2026-10-08 15:23:42.202610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34ef4843e182'
down_revision: Union[str, Sequence[str], None] = 'adb4d4e536b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="customer",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")