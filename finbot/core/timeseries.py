from typing import Iterator, TypeVar, Callable, Tuple, Optional
from datetime import datetime, timedelta
import enum


class ScheduleFrequency(enum.Enum):
    Hourly = enum.auto()
    Daily = enum.auto()
    Weekly = enum.auto()

    @staticmethod
    def deserialize(data: str) -> "ScheduleFrequency":
        return {
            "hourly": ScheduleFrequency.Hourly,
            "daily": ScheduleFrequency.Daily,
            "weekly": ScheduleFrequency.Weekly,
        }[data.lower()]


ItemType = TypeVar("ItemType")


def _frequency_to_time_interval(frequency: ScheduleFrequency) -> timedelta:
    return {
        ScheduleFrequency.Hourly: timedelta(hours=1),
        ScheduleFrequency.Daily: timedelta(days=1),
        ScheduleFrequency.Weekly: timedelta(days=7),
    }[frequency]


def _find_next_close_item(
    items_iterator: Iterator[ItemType],
    cutoff: datetime,
    time_getter: Callable[[ItemType], datetime],
) -> Optional[ItemType]:
    for item in items_iterator:
        if time_getter(item) >= cutoff:
            return item
    return None


def create_schedule(
    from_time: datetime, to_time: datetime, frequency: ScheduleFrequency
) -> list[datetime]:
    schedule = []
    current_time = from_time
    interval = _frequency_to_time_interval(frequency)
    while current_time <= to_time:
        schedule.append(current_time)
        current_time += interval
    return schedule


def schedulify(
    schedule: list[datetime],
    timed_items: list[ItemType],
    time_getter: Callable[[ItemType], datetime],
) -> list[Tuple[datetime, Optional[ItemType]]]:
    last_closest = None
    next_closest = None
    items_iterator = iter(timed_items)
    results: list[Tuple[datetime, Optional[ItemType]]] = []
    for schedule_time in schedule:
        if next_closest is not None and schedule_time >= time_getter(next_closest):
            last_closest = next_closest
        if next_closest is None or schedule_time >= time_getter(next_closest):
            next_closest = _find_next_close_item(
                items_iterator, schedule_time, time_getter
            )
        results.append((schedule_time, last_closest))
    return results
