from app.schemas.map_area import MapAreaBoundsSchema


def point_in_bounds(
    latitude: float, longitude: float, bounds: dict | MapAreaBoundsSchema | None
) -> bool:
    """Return True if the point falls within [bounds], or False if bounds is missing."""
    if bounds is None:
        return False
    if isinstance(bounds, MapAreaBoundsSchema):
        b = bounds
    else:
        try:
            b = MapAreaBoundsSchema.model_validate(bounds)
        except Exception:
            return False
    return b.min_lat <= latitude <= b.max_lat and b.min_lng <= longitude <= b.max_lng


def detect_area_for_point(
    latitude: float,
    longitude: float,
    areas: list,
) -> object | None:
    """Return the first active area whose bounds contain the point."""
    for area in areas:
        if not getattr(area, "active", True):
            continue
        if point_in_bounds(latitude, longitude, getattr(area, "bounds", None)):
            return area
    return None
