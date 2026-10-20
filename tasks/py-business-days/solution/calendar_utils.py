from datetime import date, timedelta


def business_days(start: date, end: date, holidays=None) -> int:
    """Count weekdays in [start, end] that are not holidays."""
    if start > end:
        return 0
    skip = set(holidays or [])
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in skip:
            count += 1
        d += timedelta(days=1)
    return count
