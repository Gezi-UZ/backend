"""drop_trigger_low_balance_pg_net

O trigger trigger_low_balance() usa net.http_post (extensão pg_net do Supabase)
que não existe no PostgreSQL do Railway. Este trigger causava falha em cada
UPDATE da tabela contador (telemetria do ESP32).

A notificação de saldo baixo é agora tratada inteiramente pela aplicação
(ProcessTelemetryUseCase._criar_alerta_saldo_baixo).

Revision ID: e7f8a9b0c1d2
Revises: f32dd6091188
Create Date: 2026-09-10 09:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'f32dd6091188'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove o trigger e a função que dependem de pg_net (net.http_post).
    Esta extensão existe apenas no Supabase; no Railway causa:
      ERROR: schema "net" does not exist
    A lógica de alerta é gerida pela aplicação (ProcessTelemetryUseCase).
    """
    # Drop trigger first (both possible names), then the function
    op.execute("DROP TRIGGER IF EXISTS trg_low_balance ON contador;")
    op.execute("DROP TRIGGER IF EXISTS trigger_low_balance ON contador;")
    op.execute("DROP FUNCTION IF EXISTS trigger_low_balance() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS notify_low_balance() CASCADE;")


def downgrade() -> None:
    """
    Recria o trigger (apenas funciona em ambientes com pg_net do Supabase).
    No Railway este downgrade falhará intencionalmente.
    """
    op.execute("""
        CREATE OR REPLACE FUNCTION trigger_low_balance()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.kwh_saldo < 5.0 THEN
                PERFORM net.http_post(
                    url:='https://gezi.up.railway.app/v1/webhooks/low-balance',
                    headers:='{\"Content-Type\": \"application/json\"}'::jsonb,
                    body:=jsonb_build_object('record', row_to_json(NEW))
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_low_balance
        AFTER UPDATE OF kwh_saldo ON contador
        FOR EACH ROW EXECUTE FUNCTION trigger_low_balance();
    """)
