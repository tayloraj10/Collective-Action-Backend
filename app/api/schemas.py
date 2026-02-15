"""
Expose Pydantic schemas in OpenAPI so frontend codegen can use them.
These endpoints return example instances; their main purpose is to register
the models in OpenAPI components/schemas.
"""

from fastapi import APIRouter

from app.schemas.event_data import (
    CleanupEventData,
    CleanupRouteEventData,
    EventDataBase,
    TrashReportEventData,
    ZipCodeSubmissionEventData,
)

router = APIRouter(
    prefix="/schemas",
    tags=["schemas"],
    include_in_schema=True,
)


@router.get(
    "/event-data/cleanup",
    response_model=CleanupEventData,
    summary="CleanupEventData schema",
    description="Schema for event_data when action_type is 'cleanup'. Exposed for OpenAPI/codegen.",
)
def get_cleanup_event_data_schema() -> CleanupEventData:
    return CleanupEventData()


@router.get(
    "/event-data/trash_report",
    response_model=TrashReportEventData,
    summary="TrashReportEventData schema",
    description=(
        "Schema for event_data when action_type is 'trash_report'. Exposed for OpenAPI/codegen."
    ),
)
def get_trash_report_event_data_schema() -> TrashReportEventData:
    return TrashReportEventData()


@router.get(
    "/event-data/cleanup_route",
    response_model=CleanupRouteEventData,
    summary="CleanupRouteEventData schema",
    description=(
        "Schema for event_data when action_type is 'cleanup_route'. Exposed for OpenAPI/codegen."
    ),
)
def get_cleanup_route_event_data_schema() -> CleanupRouteEventData:
    return CleanupRouteEventData()


@router.get(
    "/event-data/zip_code_submission",
    response_model=ZipCodeSubmissionEventData,
    summary="ZipCodeSubmissionEventData schema",
    description=(
        "Schema for event_data when action_type is 'zip_code_submission'. "
        "Exposed for OpenAPI/codegen."
    ),
)
def get_zip_code_submission_event_data_schema() -> ZipCodeSubmissionEventData:
    return ZipCodeSubmissionEventData()


@router.get(
    "/event-data/base",
    response_model=EventDataBase,
    summary="EventDataBase schema",
    description="Shared base fields for all event_data types. Exposed for OpenAPI/codegen.",
)
def get_event_data_base_schema() -> EventDataBase:
    return EventDataBase()
