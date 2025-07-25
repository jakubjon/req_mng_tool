"""Clean baseline - current database state

Revision ID: clean_baseline
Revises: 
Create Date: 2025-07-25 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'clean_baseline'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a baseline migration - no changes needed
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a baseline migration - no changes needed
    pass 