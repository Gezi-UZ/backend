from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
from app.core.database import SessionLocal
from app.core.firebase import send_push_notification
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/low-balance")
async def low_balance_webhook(request: Request):
    """Webhook called by Supabase Database Trigger when a meter balance drops below 5 kWh."""
    try:
        payload = await request.json()
        record = payload.get("record", {})
        
        meter_serial = record.get("numero_serie")
        kwh_saldo = record.get("kwh_saldo")
        user_id = record.get("utilizador_id")

        if not user_id or kwh_saldo is None:
            raise HTTPException(status_code=400, detail="Invalid payload")

        if kwh_saldo >= 5.0:
            return {"status": "ignored", "reason": "balance not low"}

        # Fetch FCM tokens from user_devices table
        db = SessionLocal()
        try:
            query = text("SELECT fcm_token FROM user_devices WHERE user_id = :user_id")
            result = db.execute(query, {"user_id": user_id}).fetchall()
            tokens = [row[0] for row in result]
        finally:
            db.close()

        if not tokens:
            return {"status": "ignored", "reason": "no devices found for user"}

        title = "Saldo Baixo!"
        body = f"O saldo do contador {meter_serial} baixou de 5 kWh. Considere recarregar em breve."

        sent_count = 0
        for token in tokens:
            success = send_push_notification(token, title, body)
            if success:
                sent_count += 1

        return {"status": "success", "sent_count": sent_count}

    except Exception as e:
        logger.error(f"Error processing low balance webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
