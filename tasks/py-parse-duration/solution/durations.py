import re

UNITS = [("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1), ("ms", 0.001)]
COMPONENT = re.compile(r"\s*(\d+(?:\.\d+)?)(ms|w|d|h|m|s)\s*")


def parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise ValueError("not a string")
    body = s.strip()
    sign = 1
    if body.startswith("-"):
        sign, body = -1, body[1:]
    if re.fullmatch(r"\d+", body):
        return sign * int(body)
    if not body:
        raise ValueError("empty duration")
    order = [u for u, _ in UNITS]
    mult = dict(UNITS)
    pos, last, total = 0, -1, 0.0
    while pos < len(body):
        m = COMPONENT.match(body, pos)
        if not m:
            raise ValueError(f"bad duration: {s!r}")
        idx = order.index(m.group(2))
        if idx <= last:
            raise ValueError(f"bad unit order: {s!r}")
        last = idx
        total += float(m.group(1)) * mult[m.group(2)]
        pos = m.end()
    return sign * int(total)


def format_duration(seconds: int) -> str:
    if seconds == 0:
        return "0s"
    sign = "-" if seconds < 0 else ""
    n = abs(seconds)
    out = []
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        q, n = divmod(n, size)
        if q:
            out.append(f"{q}{unit}")
    return sign + "".join(out)
