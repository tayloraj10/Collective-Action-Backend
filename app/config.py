import os
import re
from pydantic_settings import BaseSettings


import os
import re
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        # Use env DATABASE_URL if set, else build from POSTGRES_* vars
        url = os.environ.get("DATABASE_URL")
        if url:
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
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
