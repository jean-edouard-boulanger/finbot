from typing import List, Iterator, TypeVar, Callable, Tuple, Optional
from datetime import datetime, timedelta
import enum


class ScheduleFrequency(enum.Enum):
    Hourly = enum.auto()
    Daily = enum.auto()
    Weekly = enum.auto()


ItemType = TypeVar("ItemType")


def _frequency_to_time_interval(frequency: ScheduleFrequency) -> timedelta:
    return {
        ScheduleFrequency.Hourly: timedelta(hours=1),
        ScheduleFrequency.Daily: timedelta(days=1),
        ScheduleFrequency.Weekly: timedelta(days=7)
    }[frequency]


def _find_next_close_item(items_iterator: Iterator[ItemType],
                          cutoff: datetime,
                          time_getter: Callable[[ItemType], datetime]) -> Optional[ItemType]:
    for item in items_iterator:
        if time_getter(item) >= cutoff:
            return item
    return None


def sample_time_series(timed_items: List[ItemType],
                       time_getter: Callable[[ItemType], datetime],
                       interval: timedelta):
    if not timed_items:
        return
    next_date = time_getter(timed_items[0])
    yield timed_items[0]
    if len(timed_items) < 2:
        return
    for item in timed_items[1:-1]:
        current_time = time_getter(item)
        if current_time >= next_date:
            next_date = current_time + interval
            yield item
    yield timed_items[-1]


def create_schedule(from_time: datetime,
                    to_time: datetime,
                    frequency: ScheduleFrequency):
    schedule = []
    current_time = from_time
    interval = _frequency_to_time_interval(frequency)
    while current_time <= to_time:
        schedule.append(current_time)
        current_time += interval
    return schedule


def schedulify(schedule: List[datetime],
               timed_items: List[ItemType],
               time_getter: Callable[[ItemType], datetime]) -> List[Tuple[datetime, Optional[ItemType]]]:
    last_closest = None
    next_closest = None
    items_iterator = iter(timed_items)
    results = []
    for schedule_time in schedule:
        if next_closest is not None and schedule_time >= time_getter(next_closest):
            last_closest = next_closest
        if next_closest is None or schedule_time >= time_getter(next_closest):
            next_closest = _find_next_close_item(items_iterator, schedule_time, time_getter)
        results.append((schedule_time, last_closest))
    return results
