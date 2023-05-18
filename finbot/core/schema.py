import enum
from typing import Any, TypeAlias

from pydantic import BaseModel as _BaseModel
from pydantic import Extra


class BaseModel(_BaseModel):
    class Config:
        extra = Extra.forbid


class ValuationFrequency(str, enum.Enum):
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    Yearly = "Yearly"


class ValuationChange(BaseModel):
    change_1hour: float | None
    change_1day: float | None
    change_1week: float | None
    change_1month: float | None
    change_6months: float | None
    change_1year: float | None
    change_2years: float | None


CredentialsPayloadType: TypeAlias = dict[str, Any]


class HealthRequest(BaseModel):
    pass


class HealthResponse(BaseModel):
    healthy: bool
