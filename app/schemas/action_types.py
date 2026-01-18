from pydantic import BaseModel
from uuid import UUID
from enum import Enum


class ActionTypeValuesEnum(str, Enum):
    initative = "Initiative"
    map_submission = "Map Submission"


class ActionTypeSchema(BaseModel):
    id: UUID | None = None
    name: ActionTypeValuesEnum


class ActionTypeCreate(BaseModel):
    name: ActionTypeValuesEnum
