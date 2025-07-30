# db_service/app/config.py
import os

class Settings:
    NODE_ENV = os.getenv("NODE_ENV", "development")

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://timele_user:timele_password@postgres:5432/timele_db")
    RESET_DATABASE_ON_STARTUP: bool = os.getenv("RESET_DATABASE_ON_STARTUP", "false").lower() == "true"
    DB_SERVICE_PORT: int = int(os.getenv("DB_SERVICE_PORT", "7000"))

    VERSION: str = "1.0.0"
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    NOTIFICATION_FROM_EMAIL = os.getenv("NOTIFICATION_FROM_EMAIL", "timele.connects@gmail.com")
    APP_NAME = os.getenv("APP_NAME", "TimeL-E")

settings = Settings()
