"""Initial area definitions for map campaigns (NYC boroughs to start)."""

from app.schemas.map_area import MapAreaBoundsSchema, MapAreaTypeEnum

# NYC borough seed areas — used when a campaign has no areas yet.
NYC_BOROUGH_SEEDS: list[dict] = [
    {
        "name": "Manhattan",
        "area_type": MapAreaTypeEnum.borough,
        "slug": "nyc-manhattan",
        "sort_order": 1,
        "bounds": MapAreaBoundsSchema(
            min_lat=40.7000, max_lat=40.8820, min_lng=-74.0200, max_lng=-73.9070
        ),
    },
    {
        "name": "Brooklyn",
        "area_type": MapAreaTypeEnum.borough,
        "slug": "nyc-brooklyn",
        "sort_order": 2,
        "bounds": MapAreaBoundsSchema(
            min_lat=40.5700, max_lat=40.7390, min_lng=-74.0420, max_lng=-73.8330
        ),
    },
    {
        "name": "Queens",
        "area_type": MapAreaTypeEnum.borough,
        "slug": "nyc-queens",
        "sort_order": 3,
        "bounds": MapAreaBoundsSchema(
            min_lat=40.5410, max_lat=40.8120, min_lng=-73.9620, max_lng=-73.7000
        ),
    },
    {
        "name": "The Bronx",
        "area_type": MapAreaTypeEnum.borough,
        "slug": "nyc-bronx",
        "sort_order": 4,
        "bounds": MapAreaBoundsSchema(
            min_lat=40.7850, max_lat=40.9170, min_lng=-73.9330, max_lng=-73.7650
        ),
    },
    {
        "name": "Staten Island",
        "area_type": MapAreaTypeEnum.borough,
        "slug": "nyc-staten-island",
        "sort_order": 5,
        "bounds": MapAreaBoundsSchema(
            min_lat=40.4960, max_lat=40.6510, min_lng=-74.2550, max_lng=-74.0520
        ),
    },
]

DEFAULT_AREA_SEEDS = NYC_BOROUGH_SEEDS
