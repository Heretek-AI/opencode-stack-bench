import re
import sys
from collections import Counter


def main(argv):
    path = argv[1]
    with open(path) as f:
        text = f.read()
    counts = Counter(re.findall(r"[A-Za-z]+", text))
    for word, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"{word}\t{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
