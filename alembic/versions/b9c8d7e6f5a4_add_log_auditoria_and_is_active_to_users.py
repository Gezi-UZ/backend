"""Add log_auditoria and is_active to users

Revision ID: b9c8d7e6f5a4
Revises: a1b2c3d4e5f6
Create Date: 2026-09-06 22:57:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b9c8d7e6f5a4'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active to utilizadores
    op.add_column('utilizadores', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    
    # Create log_auditoria table
    op.create_table('log_auditoria',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('accao', sa.String(length=100), nullable=False),
    sa.Column('entidade', sa.String(length=100), nullable=False),
    sa.Column('entidade_id', sa.String(), nullable=True),
    sa.Column('detalhes', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['utilizadores.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('log_auditoria')
    op.drop_column('utilizadores', 'is_active')
