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
