import enum

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

    @staticmethod
    def deserialize(_: str) -> "ValuationFrequency":  # TODO: TEMPORARY REMOVE THIS
        return ValuationFrequency.Daily
