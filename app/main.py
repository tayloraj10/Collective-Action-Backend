from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.actions import router as actions_router
from app.api.initiatives import router as initiatives_router
from app.api.users import router as users_router
from app.database import Base, engine
from app.models import action as _action_model  # noqa: F401
from app.models import action_types as _action_types_model  # noqa: F401
from app.models import category as _category_model  # noqa: F401
from app.models import initiative as _initiative_model  # noqa: F401
from app.models import status as _status_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401 - ensure models are registered
from app.api.config import categories_router, statuses_router, action_types_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Collective Action Backend", lifespan=lifespan)


class SimpleValidationError(BaseModel):
    detail: str
    field: str | None = None


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    simplified = [
        SimpleValidationError(
            detail=err["msg"], field=".".join(str(loc) for loc in err["loc"])
        ).model_dump()
        for err in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"errors": simplified},
    )


# Override OpenAPI schema to exclude ValidationError AND remove 422 responses
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="Collective Action Backend",
        version="1.0.0",
        routes=app.routes,
    )

    # Remove ValidationError schemas
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        openapi_schema["components"]["schemas"].pop("ValidationError", None)
        openapi_schema["components"]["schemas"].pop(
            "HTTPValidationError", None)

    # Remove all 422 responses from all endpoints
    if "paths" in openapi_schema:
        for path_data in openapi_schema["paths"].values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "responses" in operation:
                    operation["responses"].pop("422", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

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
app.include_router(categories_router)
app.include_router(statuses_router)
app.include_router(action_types_router)
app.include_router(users_router)
