from enum import Enum


class JobSource(str, Enum):
    app = "app"
    schedule = "schedule"


class JobPriority(str, Enum):
    highest = "highest"
    high = "high"
    medium = "medium"
    low = "low"
    lowest = "lowest"
