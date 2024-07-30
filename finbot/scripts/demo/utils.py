import calendar
from datetime import date, timedelta


def is_last_business_day_of_month(d: date) -> bool:
    return d.day == max(calendar.monthcalendar(d.year, d.month)[-1][:5])


def is_last_day_of_month(d: date) -> bool:
    next_day = d + timedelta(days=1)
    return next_day.month != d.month


def is_last_day_of_week(d: date) -> bool:
    return d.weekday() == 6


def is_last_day_of_year(d: date) -> bool:
    return d.month == 12 and d.day == 31
