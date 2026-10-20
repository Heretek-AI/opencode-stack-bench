import os
import subprocess
import sys
import tempfile
import unittest

import wordfreq

HERE = os.getcwd()
TEXT = "The cat and the hat. The CAT sat; it's 2 cats, don't you see? a a\n"


def run_cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, os.path.join(HERE, "wordfreq.py"), *args],
        input=stdin, capture_output=True, text=True, timeout=30,
    )


class HiddenWordfreq(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(TEXT)

    def tearDown(self):
        os.unlink(self.path)

    def test_count_words_default(self):
        got = wordfreq.count_words(TEXT)
        self.assertEqual(got[0], ("The", 2))
        self.assertIn(("2", 1), got)
        self.assertIn(("it's", 1), got)
        self.assertIn(("don't", 1), got)

    def test_order_ties_alphabetical(self):
        got = wordfreq.count_words("b a c a b")
        self.assertEqual(got, [("a", 2), ("b", 2), ("c", 1)])

    def test_ignore_case(self):
        got = dict(wordfreq.count_words(TEXT, ignore_case=True))
        self.assertEqual(got["the"], 3)
        self.assertEqual(got["cat"], 2)
        self.assertNotIn("The", got)

    def test_min_length(self):
        got = dict(wordfreq.count_words(TEXT, min_length=3))
        self.assertNotIn("a", got)
        self.assertNotIn("it", got)
        self.assertIn("cat", got)

    def test_cli_top(self):
        r = run_cli(self.path, "--top", "2", "--ignore-case")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip().splitlines(), ["the\t3", "a\t2"])

    def test_cli_bad_top(self):
        self.assertEqual(run_cli(self.path, "--top", "0").returncode, 2)
        self.assertEqual(run_cli(self.path, "--top", "x").returncode, 2)

    def test_cli_stdin(self):
        r = run_cli("-", "--top", "1", stdin="z z y")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "z\t2")

    def test_cli_default_still_works(self):
        r = run_cli(self.path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("The\t2\n"))


if __name__ == "__main__":
    unittest.main()
