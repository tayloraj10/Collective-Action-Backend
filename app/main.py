from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.users import router as users_router
from app.database import Base, engine
from app.models import user as _user_model  # noqa: F401 - ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Collective Action Backend", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users_router)
