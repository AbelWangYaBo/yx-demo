"""contract currency for finance settlement

Revision ID: c3e5a8f01b72
Revises: a71c2f90d3e4
Create Date: 2026-11-18 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e5a8f01b72'
down_revision: Union[str, Sequence[str], None] = 'a71c2f90d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('contracts', sa.Column('currency', sa.String(length=8), nullable=False, server_default='CNY'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('contracts', 'currency')
