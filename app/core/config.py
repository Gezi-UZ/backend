from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    environment: str = "development"
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    
    # DB
    database_url: str = ""
    
    # MQTT
    mqtt_broker: str = "broker.hivemq.com"
    mqtt_port: int = 8883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_client_id: str = "gezi_backend_service"
    mqtt_use_tls: bool = True
    mqtt_transport: str = "tcp"  # 'tcp' ou 'websockets'
    
    
    # E2Payments (M-Pesa Gateway)
    e2payments_base_url: str = "https://e2payments.explicador.co.mz"
    e2payments_client_id: str = ""
    e2payments_client_secret: str = ""
    e2payments_wallet_id: str = ""

    # Firebase
    firebase_service_account: str = ""

    # Auth
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    supabase_jwks_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
