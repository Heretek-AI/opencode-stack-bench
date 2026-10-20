The `business_days(start, end, holidays=None)` function in `calendar_utils.py` gives wrong answers.
It should return the number of weekdays (Mon-Fri) in the inclusive range [start, end] that are
not in `holidays`. If `start > end` it should return 0. Holidays that fall on weekends must not be
subtracted twice. Fix the function. Keep the public signature unchanged.
