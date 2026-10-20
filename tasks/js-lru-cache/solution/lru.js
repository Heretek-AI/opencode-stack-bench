'use strict';

class LRUCache {
  constructor({ max, ttlMs, now = Date.now, onEvict } = {}) {
    if (!Number.isInteger(max) || max < 1) throw new RangeError('max must be a positive integer');
    this.max = max;
    this.ttlMs = ttlMs;
    this.now = now;
    this.onEvict = onEvict;
    this.map = new Map();
  }

  _expired(entry) {
    return this.ttlMs !== undefined && this.now() - entry.at >= this.ttlMs;
  }

  _prune() {
    for (const [k, e] of this.map) if (this._expired(e)) this.map.delete(k);
  }

  get(key) {
    const e = this.map.get(key);
    if (!e) return undefined;
    if (this._expired(e)) { this.map.delete(key); return undefined; }
    this.map.delete(key);
    this.map.set(key, e);
    return e.value;
  }

  set(key, value) {
    this.map.delete(key);
    this.map.set(key, { value, at: this.now() });
    if (this.map.size > this.max) this._prune();
    while (this.map.size > this.max) {
      const [k, e] = this.map.entries().next().value;
      this.map.delete(k);
      if (this.onEvict) this.onEvict(k, e.value);
    }
    return this;
  }

  has(key) {
    const e = this.map.get(key);
    if (!e) return false;
    if (this._expired(e)) { this.map.delete(key); return false; }
    return true;
  }

  delete(key) { return this.map.delete(key); }

  clear() { this.map.clear(); }

  get size() { this._prune(); return this.map.size; }

  keys() { this._prune(); return [...this.map.keys()].reverse(); }
}

module.exports = { LRUCache };
