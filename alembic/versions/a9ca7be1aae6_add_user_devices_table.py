"""add_user_devices_table

Revision ID: a9ca7be1aae6
Revises: f32dd6091188
Create Date: 2026-09-10 01:44:38.069251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9ca7be1aae6'
down_revision: Union[str, Sequence[str], None] = 'f32dd6091188'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_devices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('fcm_token', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fcm_token')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_devices')
