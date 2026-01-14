import os
import re

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "app_db")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "app_user")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "app_password")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT", 5432))

    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            if self.DB_PASSWORD:
                if ":" not in self.DATABASE_URL.split("//")[1].split("@")[0]:
                    protocol_and_user, rest = self.DATABASE_URL.split("@", 1)
                    return f"{protocol_and_user}:{self.DB_PASSWORD}@{rest}"
            return self.DATABASE_URL

        password = self.DB_PASSWORD or self.POSTGRES_PASSWORD
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()


# Debug helpers
def mask_url_password(url: str) -> str:
    """Masks password in a URL for logging"""
    return re.sub(r"(://[^:]+:)([^@]+)(@)", r"\1***\3", url)


print("[DEBUG] DATABASE_URL:", mask_url_password(settings.database_url))
masked_pw = settings.DB_PASSWORD[:2] + "***" if settings.DB_PASSWORD else "<not set>"
print(f"[DEBUG] DB_PASSWORD: {masked_pw}")
