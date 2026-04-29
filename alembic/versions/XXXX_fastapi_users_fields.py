"""add is_verified column for fastapi-users

Revision ID: XXXX_fastapi_users_fields
Revises: cbc528c85f8f
Create Date: 2026-04-22 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "XXXX_fastapi_users_fields"
down_revision: Union[str, None] = "cbc528c85f8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем колонку is_verified (требование fastapi-users)
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_verified")