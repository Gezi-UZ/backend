import uuid
import random
from fastapi import HTTPException
from app.modules.recharges.domain.repositories.recharge_repository import IRechargeRepository
from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.recharges.domain.services.tariff_calculator import calcular_desdobramento

class AdminGenerateTokenUseCase:
    def __init__(self, recharge_repo: IRechargeRepository, meter_repo: IMeterRepository):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo

    def execute(self, meter_id: uuid.UUID, amount: float) -> str:
        meter = self.meter_repo.get_by_id(meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado.")
            
        # Generate 20-digit token format: XXXX-XXXX-XXXX-XXXX
        raw_digits = "".join([str(random.randint(0, 9)) for _ in range(20)])
        token = f"{raw_digits[0:4]}-{raw_digits[4:8]}-{raw_digits[8:12]}-{raw_digits[12:16]}-{raw_digits[16:20]}"
        
        breakdown = calcular_desdobramento(montante_total=amount)
        
        recharge = self.recharge_repo.create_with_breakdown(
            user_id=meter.utilizador_id,
            meter_id=meter_id,
            montante=amount,
            breakdown_data=breakdown,
            metodo="TOPUP",
        )
        
        # We need to save the token and set the state
        # using the existing update_token method from the repository, we can just pass the created recharge_id
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        self.recharge_repo.update_token(recharge.id, token, now)
        
        return token
