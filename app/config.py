import os
import re
from pydantic_settings import BaseSettings


import os
import re
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "app_db")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "app_user")
    POSTGRES_PASSWORD: str = os.environ.get(
        "POSTGRES_PASSWORD", "app_password")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT", 5432))
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")

    @property
    def database_url(self) -> str:
        # Always build DATABASE_URL from individual env vars
        password = self.DB_PASSWORD or self.POSTGRES_PASSWORD
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()


def mask_url_password(url):
    return re.sub(r'(://[^:]+:)([^@]+)(@)', r'\1***\3', url)


print("[DEBUG] DATABASE_URL:", mask_url_password(settings.database_url))

# Print DB_PASSWORD (masked) for debugging Secret Manager injection
db_password = os.environ.get("DB_PASSWORD", "<not set>")
masked_pw = db_password[:2] + \
    "***" if db_password and db_password != "<not set>" else db_password
print(f"[DEBUG] DB_PASSWORD: {masked_pw}")
