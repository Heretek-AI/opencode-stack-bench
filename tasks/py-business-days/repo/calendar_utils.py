from datetime import date, timedelta


def business_days(start: date, end: date, holidays=None) -> int:
    """Count weekdays in [start, end] that are not holidays."""
    holidays = holidays or []
    days = (end - start).days
    count = 0
    for i in range(days):
        d = start + timedelta(days=i)
        if d.weekday() < 6:
            count += 1
    return count - len(holidays)
