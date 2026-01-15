from pydantic import BaseModel
from uuid import UUID
from enum import Enum


class CategoryValuesEnum(str, Enum):
    environment = "Environment"
    nature = "Nature"
    trash = "Trash"
    animals = "Animals"
    fitness = "Fitness"


class CategorySchema(BaseModel):
    id: UUID | None = None
    name: CategoryValuesEnum


class CategoryCreate(BaseModel):
    name: CategoryValuesEnum
