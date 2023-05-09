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


CredentialsPayloadType: TypeAlias = dict[str, Any]


class HealthResponse(BaseModel):
    healthy: bool
