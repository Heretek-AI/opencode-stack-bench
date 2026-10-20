Implement `parse_duration(s: str) -> int` in `durations.py`. It converts a human duration string into
whole seconds. Rules:

- Units: `w` (weeks), `d` (days), `h` (hours), `m` (minutes), `s` (seconds), `ms` (milliseconds).
- Components may be combined in strictly descending unit order, e.g. `1h30m`, `2d4h5s`, `1m500ms`.
  Whitespace between components is allowed (`1h 30m`). Each unit may appear at most once.
- Decimal values are allowed (`1.5h` = 5400). The total is rounded down to whole seconds.
- A bare integer with no unit means seconds (`90` = 90).
- An optional leading `-` negates the whole duration.
- Anything else (empty string, unknown unit, wrong order, repeated unit, trailing garbage) raises `ValueError`.

Also implement `format_duration(seconds: int) -> str`, the inverse for whole seconds using `d`, `h`, `m`, `s`
with zero components omitted (`5400` -> `1h30m`, `0` -> `0s`, `-61` -> `-1m1s`).
