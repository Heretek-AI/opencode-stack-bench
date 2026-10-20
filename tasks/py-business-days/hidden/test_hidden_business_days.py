import unittest
from datetime import date

from calendar_utils import business_days


class HiddenBusinessDays(unittest.TestCase):
    def test_full_week(self):
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 7)), 5)

    def test_single_day_weekday(self):
        self.assertEqual(business_days(date(2024, 1, 3), date(2024, 1, 3)), 1)

    def test_single_day_weekend(self):
        self.assertEqual(business_days(date(2024, 1, 6), date(2024, 1, 6)), 0)

    def test_reversed_range(self):
        self.assertEqual(business_days(date(2024, 1, 10), date(2024, 1, 1)), 0)

    def test_holiday_on_weekday(self):
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 5), [date(2024, 1, 1)]), 4)

    def test_holiday_on_weekend_ignored(self):
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 7), [date(2024, 1, 6)]), 5)

    def test_holiday_outside_range_ignored(self):
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 5), [date(2024, 2, 1)]), 5)

    def test_duplicate_holidays(self):
        h = [date(2024, 1, 2), date(2024, 1, 2)]
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 5), h), 4)

    def test_month(self):
        self.assertEqual(business_days(date(2024, 2, 1), date(2024, 2, 29)), 21)


if __name__ == "__main__":
    unittest.main()
