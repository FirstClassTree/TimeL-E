# db_service/app/config.py
import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://timele_user:timele_password@postgres:5432/timele_db")
    RESET_DATABASE_ON_STARTUP: bool = os.getenv("RESET_DATABASE_ON_STARTUP", "false").lower() == "true"

settings = Settings()

