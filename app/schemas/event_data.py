"""
Pydantic models for type-specific payloads stored in Action.event_data.
Validate by action_type when creating/updating actions.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class EventDataType(StrEnum):
    """Type discriminator for event_data payloads."""

    cleanup = "Cleanup"
    trash_report = "Trash Report"
    cleanup_route = "Cleanup Route"
    zip_code_submission = "Zip Code Submission"
    tree_planting = "Tree Planting"
    wildflower_planting = "Wildflower Planting"


# ----- Shared fields (every event_data type has these) -----
class EventDataBase(BaseModel):
    type: EventDataType
    name: str = ""
    image_url: str | None = None
    small_bags: int | None = None
    large_bags: int | None = None
    pounds: float | None = None


# ----- Cleanup (single cleanup event) -----
class CleanupEventData(EventDataBase):
    type: EventDataType = EventDataType.cleanup
    location: str = ""


# ----- TrashReport -----
class TrashReportEventData(BaseModel):
    type: EventDataType = EventDataType.trash_report
    location: str = ""
    image_url: str | None = None


# ----- CleanupRoute (route with waypoints) -----
class CleanupWaypoint(BaseModel):
    lat: float = 0.0
    lng: float = 0.0
    number: int = 0


class CleanupRouteEventData(EventDataBase):
    type: EventDataType = EventDataType.cleanup_route
    route_name: str = ""
    waypoints: list[CleanupWaypoint] = Field(default_factory=list)


# ----- ZipCodeSubmission -----
class ZipCodeSubmissionEventData(EventDataBase):
    type: EventDataType = EventDataType.zip_code_submission
    zip_code: str = ""


class PlantingEventData(BaseModel):
    """Tree or wildflower planting map submission."""

    type: EventDataType
    name: str = ""
    location: str = ""
    planting_type: str = ""
    species: str = ""
    quantity: int = 1
    notes: str = ""
    image_url: str | None = None


class TreePlantingEventData(PlantingEventData):
    type: EventDataType = EventDataType.tree_planting
    planting_type: str = "tree"


class WildflowerPlantingEventData(PlantingEventData):
    type: EventDataType = EventDataType.wildflower_planting
    planting_type: str = "wildflower"


# Map action_type to the schema class for validation.
EVENT_SCHEMAS: dict[str, type[BaseModel]] = {
    "cleanup": CleanupEventData,
    EventDataType.cleanup.value: CleanupEventData,
    "trash_report": TrashReportEventData,
    EventDataType.trash_report.value: TrashReportEventData,
    "cleanup_route": CleanupRouteEventData,
    EventDataType.cleanup_route.value: CleanupRouteEventData,
    "zip_code_submission": ZipCodeSubmissionEventData,
    EventDataType.zip_code_submission.value: ZipCodeSubmissionEventData,
    "tree_planting": TreePlantingEventData,
    EventDataType.tree_planting.value: TreePlantingEventData,
    "wildflower_planting": WildflowerPlantingEventData,
    EventDataType.wildflower_planting.value: WildflowerPlantingEventData,
}


def validate_event_data(action_type: str, data: dict) -> dict | None:
    """Validate and return sanitized event_data.

    Uses data['type'] if present, otherwise falls back to action_type.
    Ensures the type field is set in the validated output.
    """
    if not data:
        return None

    # Prefer type from data if present, otherwise use action_type
    event_type = data.get("type", action_type)
    schema_cls = EVENT_SCHEMAS.get(event_type)
    if not schema_cls:
        return data  # unknown type: store as-is

    validated = schema_cls.model_validate(data)
    result = validated.model_dump()
    # Ensure type is set (in case it wasn't in input)
    if "type" not in result:
        result["type"] = event_type
    return result
