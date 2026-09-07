from app.core.database import Base

# Import all models here so Alembic can discover them
from app.modules.users.domain.entities.user import Utilizador
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.alerta import Alerta
from app.modules.iot.domain.entities.iot import DispositivoIoT
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.recharges.domain.entities.recharge_breakdown import DesdobramentoRecarga
from app.modules.payments.domain.entities.payment import Pagamento
from app.modules.audit.domain.entities.audit import LogAuditoria
from sqlalchemy import Table, Column, String
from sqlalchemy.dialects.postgresql import UUID

# Define the external Supabase auth.users table so SQLAlchemy can resolve the ForeignKey
Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)
