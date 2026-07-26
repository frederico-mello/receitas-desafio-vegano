"""add_restrictions_to_inventory_items

Revision ID: 7812b2cb50fb
Revises: 95a0993676bb
Create Date: 2026-07-26 08:03:33.952388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7812b2cb50fb'
down_revision: Union[str, Sequence[str], None] = '95a0993676bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "inventory_items",
        sa.Column("restrictions", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inventory_items", "restrictions")
