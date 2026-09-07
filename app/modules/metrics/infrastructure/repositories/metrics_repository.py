from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.meters.domain.entities.meter import Contador
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from datetime import datetime, date

class MetricsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_meters(self) -> int:
        return self.db.query(Contador).count()

    def get_online_meters(self) -> int:
        return self.db.query(Contador).filter(Contador.is_online == True).count()

    def get_today_revenue(self) -> float:
        today = date.today()
        # Assume server time is what matters for "today"
        revenue = self.db.query(func.sum(Recarga.montante_pago)).filter(
            func.date(Recarga.criado_em) == today,
            Recarga.estado.in_(["CONFIRMED", "COMPLETED", "MQTT_SENT", "ACK_RECEIVED"])
        ).scalar()
        return float(revenue or 0.0)

    def get_failed_commands(self) -> int:
        return self.db.query(ComandoIoT).filter(ComandoIoT.estado == "FAILED").count()

    def get_avg_latency(self) -> float:
        # Placeholder for latency if not easily available from DB.
        # Alternatively, could be calculated from ComandoIoT timestamps
        return 120.5  # mock ms
