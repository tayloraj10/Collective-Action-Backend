from contextlib import asynccontextmanager


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.api.actions import router as actions_router
from app.api.initiatives import router as initiatives_router
from app.api.config import router as config_router
from app.database import Base, engine
from app.models import user as _user_model  # noqa: F401 - ensure models are registered
from app.models import initiative as _initiative_model  # noqa: F401
from app.models import action as _action_model  # noqa: F401
from app.models import category as _category_model  # noqa: F401
from app.models import status as _status_model  # noqa: F401
from app.models import action_types as _action_types_model  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Collective Action Backend", lifespan=lifespan)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(initiatives_router)
app.include_router(actions_router)
app.include_router(config_router)
app.include_router(users_router)
