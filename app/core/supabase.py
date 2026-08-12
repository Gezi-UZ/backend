from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_supabase_client() -> Client | None:
    if settings.supabase_url and settings.supabase_key:
        try:
            return create_client(settings.supabase_url, settings.supabase_key)
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Supabase: {e}")
            return None
    else:
        logger.warning("Supabase URL ou Key não fornecidas. Cliente Supabase não inicializado.")
        return None

supabase = init_supabase_client()
