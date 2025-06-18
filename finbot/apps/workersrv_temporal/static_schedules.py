from dataclasses import dataclass
from datetime import timedelta

from temporalio.client import Schedule as TemporalSchedule
from temporalio.client import (
    ScheduleActionStartWorkflow,
    ScheduleCalendarSpec,
    SchedulePolicy,
    ScheduleRange,
    ScheduleSpec,
)

from finbot.core.temporal_ import GENERIC_TASK_QUEUE, TRY_ONCE, temporal_workflow_id
from finbot.workflows.user_account_valuation.workflows import RunValuationForAllUsers


@dataclass(frozen=True)
class ValuationScheduleEntry:
    time_str: str
    tz: str = "Europe/Paris"

    @property
    def hour(self) -> int:
        return int(self.time_str.split(":")[0])

    @property
    def minute(self) -> int:
        return int(self.time_str.split(":")[1])


VALUATION_SCHEDULE = [
    ValuationScheduleEntry("08:00"),
    ValuationScheduleEntry("10:00"),
    ValuationScheduleEntry("12:00"),
    ValuationScheduleEntry("14:00"),
    ValuationScheduleEntry("16:00"),
    ValuationScheduleEntry("18:00"),
]


@dataclass(frozen=True)
class Schedule:
    id: str
    temporal_schedule: TemporalSchedule


def get_static_schedules() -> list[Schedule]:
    all_schedules = [
        Schedule(
            id=f"valuation.{entry.time_str.replace(':', '_')}",
            temporal_schedule=TemporalSchedule(
                action=ScheduleActionStartWorkflow(
                    RunValuationForAllUsers,
                    task_queue=GENERIC_TASK_QUEUE,
                    retry_policy=TRY_ONCE,
                    id=temporal_workflow_id(),
                ),
                spec=ScheduleSpec(
                    calendars=[
                        ScheduleCalendarSpec(
                            hour=(ScheduleRange(entry.hour),),
                            minute=(ScheduleRange(entry.minute),),
                        )
                    ],
                    time_zone_name=entry.tz,
                ),
                policy=SchedulePolicy(
                    catchup_window=timedelta(hours=1),
                ),
            ),
        )
        for entry in VALUATION_SCHEDULE
    ]
    return all_schedules
