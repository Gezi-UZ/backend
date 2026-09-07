from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.metrics.domain.entities.schemas import MetricsHistoryResponse, RevenueHistoryItem
from datetime import datetime, timedelta

class GetMetricsHistoryUseCase:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, period: str) -> MetricsHistoryResponse:
        now = datetime.utcnow()
        if period == "7d":
            days = 7
        elif period == "30d":
            days = 30
        else:
            days = 7  # default
            
        start_date = now - timedelta(days=days)
        
        # Aggregate revenue by date
        # PostgreSQL syntax: date_trunc('day', criado_em) or just cast to date
        results = self.db.query(
            func.date(Recarga.criado_em).label('date'),
            func.sum(Recarga.montante_pago).label('revenue'),
            func.count(Recarga.id).label('transactions')
        ).filter(
            Recarga.criado_em >= start_date,
            Recarga.estado.in_(["CONFIRMED", "COMPLETED", "MQTT_SENT", "ACK_RECEIVED"])
        ).group_by(
            func.date(Recarga.criado_em)
        ).order_by(
            func.date(Recarga.criado_em)
        ).all()
        
        history = []
        for r in results:
            history.append(RevenueHistoryItem(
                date=str(r.date),
                revenue=float(r.revenue or 0.0),
                transactions=r.transactions
            ))
            
        # Optional: Fill missing dates with 0 if necessary for the chart
        # But NextJS frontend can handle it if needed.
            
        return MetricsHistoryResponse(
            period=period,
            history=history
        )
