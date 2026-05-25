from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.actions import router as actions_router
from app.api.config import action_types_router, categories_router, statuses_router
from app.api.connections import router as connections_router
from app.api.directory_of_good import router as directory_of_good_router
from app.api.image_proxy import router as image_proxy_router
from app.api.initiatives import router as initiatives_router
from app.api.links import router as links_router
from app.api.map_campaigns import router as map_campaigns_router
from app.api.map_hotspots import router as map_hotspots_router
from app.api.photos import router as photos_router
from app.api.projects import roles_router as project_roles_router
from app.api.projects import router as projects_router
from app.api.quotes import router as quotes_router
from app.api.schemas import router as schemas_router
from app.api.users import router as users_router
from app.models import action as _action_model  # noqa: F401
from app.models import action_types as _action_types_model  # noqa: F401
from app.models import category as _category_model  # noqa: F401
from app.models import connection as _connection_model  # noqa: F401
from app.models import directory_of_good as _directory_of_good_model  # noqa: F401
from app.models import initiative as _initiative_model  # noqa: F401
from app.models import link as _link_model  # noqa: F401
from app.models import area_captain as _area_captain_model  # noqa: F401
from app.models import map_area as _map_area_model  # noqa: F401
from app.models import map_campaign as _map_campaign_model  # noqa: F401
from app.models import map_hotspot as _map_hotspot_model  # noqa: F401
from app.models import project as _project_model  # noqa: F401
from app.models import status as _status_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401 - ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    # NOTE: Don't create tables in production - use Alembic migrations
    # Uncomment for local development if needed:
    # if settings.environment == "development":
    #     Base.metadata.create_all(bind=engine)
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
        openapi_schema["components"]["schemas"].pop("HTTPValidationError", None)

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


app.include_router(directory_of_good_router)
app.include_router(initiatives_router)
app.include_router(map_campaigns_router)
app.include_router(map_hotspots_router)
app.include_router(projects_router)
app.include_router(project_roles_router)
app.include_router(links_router)
app.include_router(actions_router)
app.include_router(connections_router)
app.include_router(image_proxy_router)
app.include_router(categories_router)
app.include_router(statuses_router)
app.include_router(action_types_router)
app.include_router(quotes_router)
app.include_router(schemas_router)
app.include_router(users_router)
app.include_router(photos_router)
