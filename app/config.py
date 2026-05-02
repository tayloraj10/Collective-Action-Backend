import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database Configuration
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "app_db")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "app_user")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "app_password")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT", 5432))

    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # SQLAlchemy pool per process; keep (instances × pool) under Cloud SQL max_connections.
    DB_POOL_SIZE: int = int(os.environ.get("DB_POOL_SIZE", "3"))
    DB_MAX_OVERFLOW: int = int(os.environ.get("DB_MAX_OVERFLOW", "5"))
    DB_POOL_RECYCLE_SECONDS: int = int(os.environ.get("DB_POOL_RECYCLE_SECONDS", "1800"))

    # Environment (production = no path prefix; development/testing = prefix for easy cleanup)
    ENVIRONMENT: str = "production"

    # Google Cloud Storage Configuration
    GCS_USER_IMAGES_BUCKET: str = os.environ.get("GCS_USER_IMAGES_BUCKET", "")
    GCS_SUBMISSIONS_BUCKET: str = os.environ.get("GCS_SUBMISSIONS_BUCKET", "")
    GCS_PROJECT_ID: str = os.environ.get("GCS_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Directory of Good: "Interesting People" Google Sheet (share sheet with service account)
    DIRECTORY_GOOGLE_SHEET_ID: str = os.environ.get(
        "DIRECTORY_GOOGLE_SHEET_ID",
        "1KVYFjM8E_c65hzia2LWgtwvO9UKeqUXJpsfhB2OeOAo",
    )
    DIRECTORY_GOOGLE_SHEET_GID: int = int(
        os.environ.get("DIRECTORY_GOOGLE_SHEET_GID", "1363212709")
    )
    # If set, POST /directory-of-good/sync-from-google-sheet requires header X-Sync-Secret
    DIRECTORY_GOOGLE_SHEET_SYNC_SECRET: str = os.environ.get(
        "DIRECTORY_GOOGLE_SHEET_SYNC_SECRET", ""
    )

    # Google Maps Geocoding API key (server-side; keep separate from the frontend JS key)
    GOOGLE_MAPS_GEOCODING_API_KEY: str = os.environ.get("GOOGLE_MAPS_GEOCODING_API_KEY", "")

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
