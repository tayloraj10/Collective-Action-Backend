import os
import re

# Build DATABASE_URL at runtime from environment variables


def get_env(key, default=None):
    return os.environ.get(key, default)


POSTGRES_DB = get_env("POSTGRES_DB", "app_db")
POSTGRES_USER = get_env("POSTGRES_USER", "app_user")
POSTGRES_PASSWORD = get_env("DB_PASSWORD", get_env(
    "POSTGRES_PASSWORD", "app_password"))
POSTGRES_HOST = get_env("POSTGRES_HOST", "db")
POSTGRES_PORT = get_env("POSTGRES_PORT", "5432")

# For Cloud Run/Cloud SQL socket
CLOUDSQL_CONNECTION = get_env("CLOUDSQL_CONNECTION")
if CLOUDSQL_CONNECTION:
    DB_HOST = f"/cloudsql/{CLOUDSQL_CONNECTION}"
else:
    DB_HOST = POSTGRES_HOST

if DB_HOST.startswith("/cloudsql/"):
    DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@/{POSTGRES_DB}?host={DB_HOST}"
else:
    DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Debug print for DATABASE_URL (mask password)


def mask_url_password(url):
    return re.sub(r'(://[^:]+:)([^@]+)(@)', r'\1***\3', url)


print("[DEBUG] DATABASE_URL:", mask_url_password(settings.DATABASE_URL))

# Print DB_PASSWORD (masked) for debugging Secret Manager injection
db_password = os.environ.get("DB_PASSWORD", "<not set>")
masked_pw = db_password[:2] + \
    "***" if db_password and db_password != "<not set>" else db_password
print(f"[DEBUG] DB_PASSWORD: {masked_pw}")
