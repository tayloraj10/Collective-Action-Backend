from uuid import UUID

from pydantic import BaseModel

# class CategoryValuesEnum(str, Enum):
#     environment = "Environment"
#     nature = "Nature"
#     trash = "Trash"
#     animals = "Animals"
#     fitness = "Fitness"


class CategorySchema(BaseModel):
    id: UUID | None = None
    name: str


class CategoryCreate(BaseModel):
    name: str
