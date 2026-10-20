Implement the `LRUCache` class exported from `lru.js` (CommonJS). Requirements:

- `new LRUCache({ max, ttlMs, now })`: `max` is a positive integer (throw `RangeError` otherwise).
  `ttlMs` is optional (no expiry when omitted). `now` is an optional clock function returning
  milliseconds, defaulting to `Date.now`.
- `get(key)` returns the value or `undefined`, and marks the key as most recently used.
  Expired entries are treated as missing and removed.
- `set(key, value)` inserts or updates and marks as most recently used, evicting the least recently
  used entry when over `max`. Returns `this`. Updating an entry resets its TTL.
- `has(key)` (does NOT change recency), `delete(key)` (returns boolean), `clear()`.
- `size` getter (count of non-expired entries).
- `keys()` returns an array of keys from most to least recently used, excluding expired entries.
- Optional `onEvict(key, value)` callback in the constructor options, called on LRU eviction
  (not on delete, clear, or expiry).
