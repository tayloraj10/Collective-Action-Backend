from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ActionTypeValuesEnum(StrEnum):
    initative = "Initiative"
    map_submission = "Map Submission"


class ActionTypeSchema(BaseModel):
    id: UUID | None = None
    name: ActionTypeValuesEnum


class ActionTypeCreate(BaseModel):
    name: ActionTypeValuesEnum
