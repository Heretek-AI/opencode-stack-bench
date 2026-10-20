import unittest

from durations import format_duration, parse_duration


class HiddenParse(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h5s"), 2 * 86400 + 4 * 3600 + 5)
        self.assertEqual(parse_duration("1w"), 604800)

    def test_whitespace(self):
        self.assertEqual(parse_duration("1h 30m"), 5400)

    def test_decimal(self):
        self.assertEqual(parse_duration("1.5h"), 5400)
        self.assertEqual(parse_duration("1m500ms"), 60)
        self.assertEqual(parse_duration("2500ms"), 2)

    def test_bare_integer(self):
        self.assertEqual(parse_duration("90"), 90)

    def test_negative(self):
        self.assertEqual(parse_duration("-1h"), -3600)

    def test_errors(self):
        for bad in ["", "abc", "1x", "30m1h", "1h1h", "1h30", "h", "1h-30m", "1..5h"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_duration(bad)


class HiddenFormat(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_duration(5400), "1h30m")
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(-61), "-1m1s")
        self.assertEqual(format_duration(90061), "1d1h1m1s")

    def test_roundtrip(self):
        for n in [1, 59, 3600, 86399, 172800, 123456]:
            with self.subTest(n=n):
                self.assertEqual(parse_duration(format_duration(n)), n)


if __name__ == "__main__":
    unittest.main()
