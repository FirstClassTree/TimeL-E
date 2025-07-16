import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://timele_user:timele_password@postgres:5432/timele_db")
