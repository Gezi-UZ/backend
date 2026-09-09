import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.modules.recharges.domain.repositories.recharge_repository import IRechargeRepository
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.recharges.domain.entities.recharge_breakdown import DesdobramentoRecarga
from app.modules.recharges.domain.entities.schemas import RechargeInitiateRequest
from app.modules.meters.domain.entities.meter import Contador
from app.modules.users.domain.entities.user import Utilizador


class SQLAlchemyRechargeRepository(IRechargeRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: uuid.UUID, meter_id: uuid.UUID, data: RechargeInitiateRequest) -> Recarga:
        db_recharge = Recarga(
            contador_id=meter_id,
            montante_pago=data.amount_mzn,
            estado="PENDING",
        )
        self.db.add(db_recharge)
        self.db.commit()
        self.db.refresh(db_recharge)
        return db_recharge

    def create_with_breakdown(
        self,
        user_id: uuid.UUID,
        meter_id: uuid.UUID,
        montante: float,
        breakdown_data: dict,
        metodo: str = "M-PESA",
        is_primeira_compra: bool = False,
        token: Optional[str] = None,
    ) -> Recarga:
        """Cria recarga + desdobramento numa única transacção."""
        db_recharge = Recarga(
            contador_id=meter_id,
            utilizador_id=user_id,
            montante_pago=montante,
            kwh_creditado=breakdown_data["kwh_calculado"],
            metodo=metodo,
            estado="PENDING",
            is_primeira_compra_mes=is_primeira_compra,
        )
        self.db.add(db_recharge)
        self.db.flush()  # Obtém o ID sem commit para criar o desdobramento

        db_breakdown = DesdobramentoRecarga(
            recarga_id=db_recharge.id,
            montante_total=breakdown_data["montante_total"],
            val_energia=breakdown_data["val_energia"],
            iva=breakdown_data["iva"],
            divida_paga=breakdown_data.get("divida_paga", 0.0),
            tx_radio=breakdown_data["tx_radio"],
            tx_lixo=breakdown_data["tx_lixo"],
            kwh_calculado=breakdown_data["kwh_calculado"],
        )
        self.db.add(db_breakdown)
        self.db.commit()
        self.db.refresh(db_recharge)
        return db_recharge

    def get_by_id(self, recharge_id: uuid.UUID) -> Optional[Recarga]:
        return self.db.query(Recarga).filter(Recarga.id == recharge_id).first()

    def get_by_meter_and_code(self, recharge_code: str) -> Optional[Recarga]:
        """Verifica duplicação de código manual pelo token guardado (RN10)."""
        return (
            self.db.query(Recarga)
            .filter(Recarga.token_sts == recharge_code)
            .first()
        )

    def get_history(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Recarga], int]:
        from sqlalchemy.orm import contains_eager, selectinload
        from sqlalchemy import or_
        query = (
            self.db.query(Recarga)
            .join(Contador, Recarga.contador_id == Contador.id)
            .options(
                contains_eager(Recarga.contador).selectinload(Contador.utilizador), 
                selectinload(Recarga.pagamentos),
                selectinload(Recarga.utilizador)
            )
            .filter(or_(Contador.utilizador_id == user_id, Recarga.utilizador_id == user_id))
        )
        if meter_id:
            query = query.filter(Recarga.contador_id == meter_id)
        if from_date:
            query = query.filter(Recarga.criado_em >= from_date)
        if to_date:
            query = query.filter(Recarga.criado_em <= to_date)

        total = query.count()
        recharges = query.order_by(Recarga.criado_em.desc()).offset(skip).limit(limit).all()
        return recharges, total

    def get_all_admin(
        self,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        meter_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[dict], int]:
        query = (
            self.db.query(
                Recarga.id,
                Recarga.utilizador_id,
                Utilizador.nome.label("user_name"),
                Recarga.contador_id,
                Contador.numero_serie.label("meter_serial"),
                Recarga.montante_pago,
                Recarga.kwh_creditado,
                Recarga.metodo,
                Recarga.estado,
                Recarga.criado_em
            )
            .join(Contador, Recarga.contador_id == Contador.id)
            .join(Utilizador, Recarga.utilizador_id == Utilizador.id)
        )
        
        if status:
            query = query.filter(Recarga.estado == status)
        if meter_id:
            query = query.filter(Recarga.contador_id == meter_id)
        if from_date:
            query = query.filter(Recarga.criado_em >= from_date)
        if to_date:
            query = query.filter(Recarga.criado_em <= to_date)

        total = query.count()
        results = query.order_by(Recarga.criado_em.desc()).offset(skip).limit(limit).all()
        
        formatted = []
        for r in results:
            formatted.append({
                "recharge_id": r.id,
                "user_id": r.utilizador_id,
                "user_name": r.user_name,
                "meter_id": r.contador_id,
                "meter_serial": r.meter_serial,
                "amount_mzn": r.montante_pago,
                "credit_kwh": r.kwh_creditado,
                "payment_method": r.metodo,
                "status": r.estado,
                "created_at": r.criado_em
            })
            
        return formatted, total

    def update_status(self, recharge_id: uuid.UUID, new_status: str) -> Optional[Recarga]:
        db_recharge = self.get_by_id(recharge_id)
        if db_recharge:
            db_recharge.estado = new_status
            self.db.commit()
            self.db.refresh(db_recharge)
        return db_recharge

    def update_token(self, recharge_id: uuid.UUID, token: str, applied_at: datetime) -> Optional[Recarga]:
        db_recharge = self.get_by_id(recharge_id)
        if db_recharge:
            db_recharge.token_sts = token
            db_recharge.recarregado_em = applied_at
            db_recharge.estado = "CONFIRMED"
            self.db.commit()
            self.db.refresh(db_recharge)
        return db_recharge

    def has_successful_recharge_this_month(self, meter_id: uuid.UUID) -> bool:
        """
        Verifica se o contador já tem uma recarga bem-sucedida no mês corrente.
        Usado para determinar se é a primeira compra do mês (cobra taxas fixas).
        Uma recarga conta se estiver em qualquer estado de sucesso:
        CONFIRMED, MQTT_SENT, ACK_RECEIVED, COMPLETED.
        """
        from sqlalchemy import extract
        now = datetime.utcnow()
        count = (
            self.db.query(Recarga)
            .filter(
                Recarga.contador_id == meter_id,
                Recarga.estado.in_(["CONFIRMED", "MQTT_SENT", "ACK_RECEIVED", "COMPLETED"]),
                extract("year", Recarga.criado_em) == now.year,
                extract("month", Recarga.criado_em) == now.month,
            )
            .count()
        )
        return count > 0

    def mark_token_used(self, recharge_id: uuid.UUID, applied_at: datetime) -> Optional[Recarga]:
        db_recharge = self.get_by_id(recharge_id)
        if db_recharge:
            db_recharge.token_sts_usado = True
            db_recharge.recarregado_em = applied_at
            db_recharge.estado = "MQTT_SENT"
            self.db.commit()
            self.db.refresh(db_recharge)
        return db_recharge

    def get_dashboard_stats(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        from sqlalchemy import or_

        # Recargas bem-sucedidas acessíveis ao utilizador (owner do contador OU iniciador)
        query = (
            self.db.query(Recarga)
            .join(Contador, Recarga.contador_id == Contador.id)
            .filter(or_(Contador.utilizador_id == user_id, Recarga.utilizador_id == user_id))
            .filter(Recarga.estado.in_(["CONFIRMED", "MQTT_SENT", "ACK_RECEIVED", "COMPLETED"]))
        )
        if meter_id:
            query = query.filter(Recarga.contador_id == meter_id)
        if from_date:
            query = query.filter(Recarga.criado_em >= from_date)
        if to_date:
            query = query.filter(Recarga.criado_em <= to_date)

        recharges = query.all()

        # total_spent: montante pago pelo próprio utilizador
        total_spent = sum(
            r.montante_pago for r in recharges if r.utilizador_id == user_id
        )
        # total_kwh: energia creditada em qualquer contador do utilizador (inclui recargas recebidas)
        total_kwh = sum(r.kwh_creditado or 0.0 for r in recharges)
        count = len(recharges)

        # Calcular média diária de consumo
        if from_date and to_date:
            days = max((to_date - from_date).days, 1)
        else:
            days = 30  # Default: último mês

        avg_kwh_day = round(total_kwh / days, 2) if days > 0 else 0.0

        return {
            "total_spent_mzn": round(total_spent, 2),
            "total_kwh_purchased": round(total_kwh, 2),
            "average_consumption_kwh_day": avg_kwh_day,
            "recharge_count": count,
        }

