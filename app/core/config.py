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
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_client_id: str = "gezi_backend_service"
    
    # Auth
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
