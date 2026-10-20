#!/usr/bin/env python3
"""Run the hidden unittest files in <hidden_dir> against the current directory and print
{"passed": n, "total": n} as the last line of stdout."""
import json
import os
import sys
import unittest


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    hidden = os.path.abspath(sys.argv[1])
    sys.path.insert(0, os.getcwd())
    suite = unittest.defaultTestLoader.discover(hidden, pattern="test*.py", top_level_dir=hidden)
    tests = list(flatten(suite))
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(unittest.TestSuite(tests))
    # A failing subTest is reported as a _SubTest; count it against its parent test.
    bad = {id(getattr(t, "test_case", t)) for t, _ in result.failures + result.errors}
    # Import errors surface as a single failing _FailedTest, which counts as 0 passed.
    passed = sum(1 for t in tests if id(t) not in bad and not isinstance(t, unittest.loader._FailedTest))
    sys.stdout.flush()
    print(json.dumps({"passed": passed, "total": len(tests)}))


if __name__ == "__main__":
    main()
