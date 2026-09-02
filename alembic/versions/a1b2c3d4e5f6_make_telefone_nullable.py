"""make telefone nullable in utilizadores

Revision ID: a1b2c3d4e5f6
Revises: 4b724b2ae0f8
Create Date: 2026-09-02 21:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4b724b2ae0f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tornar telefone nullable para suportar signup por email sem número de telefone."""

    # 1. Remover NOT NULL constraint da coluna telefone
    op.alter_column(
        'utilizadores',
        'telefone',
        existing_type=sa.String(length=9),
        nullable=True,
    )

    # 2. Recriar o índice único como PARTIAL (ignora NULL — permite múltiplos utilizadores sem telefone)
    op.drop_index('ix_utilizadores_telefone', table_name='utilizadores')
    op.execute("""
        CREATE UNIQUE INDEX ix_utilizadores_telefone
          ON public.utilizadores (telefone)
          WHERE telefone IS NOT NULL;
    """)


def downgrade() -> None:
    """Reverter — apenas possível se não existirem linhas com telefone NULL."""

    # Recriar índice único padrão
    op.drop_index('ix_utilizadores_telefone', table_name='utilizadores')
    op.create_index(
        op.f('ix_utilizadores_telefone'),
        'utilizadores',
        ['telefone'],
        unique=True,
    )

    # Restaurar NOT NULL (pode falhar se existirem registos com telefone NULL)
    op.alter_column(
        'utilizadores',
        'telefone',
        existing_type=sa.String(length=9),
        nullable=False,
    )
