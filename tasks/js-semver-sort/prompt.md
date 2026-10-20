Implement `semver.js` (CommonJS, no dependencies) exporting:

- `parse(v)`: parses a SemVer 2.0.0 string (an optional leading `v` is allowed) into
  `{ major, minor, patch, prerelease: [...], build: [...] }` where numeric prerelease identifiers are
  numbers. Returns `null` for invalid input (including leading zeros in numeric parts).
- `compare(a, b)`: returns -1, 0 or 1 following SemVer 2.0.0 precedence (build metadata ignored).
  Throws `TypeError` if either input is invalid.
- `sort(list)`: returns a new array sorted ascending by precedence; invalid entries are dropped.
- `satisfies(v, range)`: supports ranges made of space-separated comparators that must all match
  (`>=1.2.0 <2.0.0`), `||` alternatives, exact versions, `^` and `~` with the usual npm meaning
  (including `^0.x` behaviour), and `*`. Prerelease versions only satisfy a range if a comparator in
  the same set has a prerelease on the same `major.minor.patch`, as in npm.

There is an existing partial implementation; fix and complete it.
