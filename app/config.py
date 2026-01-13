import os
import re
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()

# Debug print for DATABASE_URL (mask password)


def mask_url_password(url):
    return re.sub(r'(://[^:]+:)([^@]+)(@)', r'\1***\3', url)


print("[DEBUG] DATABASE_URL:", mask_url_password(settings.DATABASE_URL))

# Print DB_PASSWORD (masked) for debugging Secret Manager injection
db_password = os.environ.get("DB_PASSWORD", "<not set>")
masked_pw = db_password[:2] + \
    "***" if db_password and db_password != "<not set>" else db_password
print(f"[DEBUG] DB_PASSWORD: {masked_pw}")
