import unittest
from datetime import date

from calendar_utils import business_days


class TestBusinessDays(unittest.TestCase):
    def test_single_week(self):
        self.assertEqual(business_days(date(2024, 1, 1), date(2024, 1, 5)), 5)


if __name__ == "__main__":
    unittest.main()
