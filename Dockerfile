FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# System deps (needed for psycopg + general sanity)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies (use lockfile)
RUN uv pip install --system --requirements pyproject.toml

# Copy app code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8080

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080
