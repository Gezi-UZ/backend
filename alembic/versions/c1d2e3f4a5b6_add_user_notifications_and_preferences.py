"""add_user_notifications_and_preferences

Revision ID: c1d2e3f4a5b6
Revises: a9ca7be1aae6
Create Date: 2026-09-10 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'a9ca7be1aae6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as tabelas user_notifications e user_notification_preferences."""

    # Tabela de notificações in-app
    op.create_table(
        'user_notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(64), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['auth.users.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_user_notifications_user_id',
        'user_notifications',
        ['user_id'],
    )
    op.create_index(
        'ix_user_notifications_created_at',
        'user_notifications',
        ['created_at'],
    )

    # Tabela de preferências de notificação por utilizador
    op.create_table(
        'user_notification_preferences',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('low_balance_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('recharge_confirmed_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('payment_failed_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['auth.users.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('user_id'),
    )


def downgrade() -> None:
    """Remove as tabelas de notificações."""
    op.drop_table('user_notification_preferences')
    op.drop_index('ix_user_notifications_created_at', table_name='user_notifications')
    op.drop_index('ix_user_notifications_user_id', table_name='user_notifications')
    op.drop_table('user_notifications')
