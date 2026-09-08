"""fix_contador_dispositivo_canal_uq

Revision ID: 8ed656a70d3c
Revises: 32dffb9f9c5f
Create Date: 2026-09-08 00:38:19.337543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ed656a70d3c'
down_revision: Union[str, Sequence[str], None] = '32dffb9f9c5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_contador_dispositivo_canal', 'contador', ['dispositivo_id', 'canal'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_contador_dispositivo_canal', 'contador', type_='unique')
