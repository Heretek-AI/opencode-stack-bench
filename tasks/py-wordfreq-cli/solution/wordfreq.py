import argparse
import re
import sys
from collections import Counter

WORD = re.compile(r"[A-Za-z0-9']+")


def count_words(text, ignore_case=False, min_length=1):
    words = WORD.findall(text)
    if ignore_case:
        words = [w.lower() for w in words]
    counts = Counter(w for w in words if len(w) >= min_length)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def positive_int(s):
    n = int(s)
    if n < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return n


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--top", type=positive_int)
    p.add_argument("--ignore-case", action="store_true")
    p.add_argument("--min-length", type=int, default=1)
    a = p.parse_args(argv[1:])
    text = sys.stdin.read() if a.path == "-" else open(a.path).read()
    rows = count_words(text, a.ignore_case, a.min_length)
    if a.top:
        rows = rows[: a.top]
    for word, n in rows:
        print(f"{word}\t{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
