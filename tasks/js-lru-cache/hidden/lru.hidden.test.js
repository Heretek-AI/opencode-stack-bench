'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const { LRUCache } = require(path.join(process.cwd(), 'lru.js'));

test('basic get/set', () => {
  const c = new LRUCache({ max: 2 });
  assert.strictEqual(c.set('a', 1), c);
  assert.strictEqual(c.get('a'), 1);
  assert.strictEqual(c.get('zz'), undefined);
});

test('evicts least recently used', () => {
  const c = new LRUCache({ max: 2 });
  c.set('a', 1); c.set('b', 2); c.get('a'); c.set('c', 3);
  assert.strictEqual(c.has('b'), false);
  assert.deepStrictEqual(c.keys(), ['c', 'a']);
});

test('has does not change recency', () => {
  const c = new LRUCache({ max: 2 });
  c.set('a', 1); c.set('b', 2); c.has('a'); c.set('c', 3);
  assert.strictEqual(c.has('a'), false);
});

test('invalid max throws RangeError', () => {
  assert.throws(() => new LRUCache({ max: 0 }), RangeError);
  assert.throws(() => new LRUCache({ max: 1.5 }), RangeError);
});

test('ttl expiry with injected clock', () => {
  let t = 1000;
  const c = new LRUCache({ max: 5, ttlMs: 100, now: () => t });
  c.set('a', 1); t += 50; c.set('b', 2); t += 60;
  assert.strictEqual(c.get('a'), undefined);
  assert.strictEqual(c.get('b'), 2);
  assert.strictEqual(c.size, 1);
  assert.deepStrictEqual(c.keys(), ['b']);
});

test('update resets ttl', () => {
  let t = 0;
  const c = new LRUCache({ max: 5, ttlMs: 100, now: () => t });
  c.set('a', 1); t = 90; c.set('a', 2); t = 150;
  assert.strictEqual(c.get('a'), 2);
});

test('delete and clear', () => {
  const c = new LRUCache({ max: 3 });
  c.set('a', 1); c.set('b', 2);
  assert.strictEqual(c.delete('a'), true);
  assert.strictEqual(c.delete('a'), false);
  c.clear();
  assert.strictEqual(c.size, 0);
});

test('onEvict only on LRU eviction', () => {
  const evicted = [];
  const c = new LRUCache({ max: 1, onEvict: (k, v) => evicted.push([k, v]) });
  c.set('a', 1); c.set('b', 2); c.delete('b'); c.set('c', 3); c.clear();
  assert.deepStrictEqual(evicted, [['a', 1]]);
});

test('non-string keys', () => {
  const c = new LRUCache({ max: 2 });
  const k = {};
  c.set(k, 'obj'); c.set(1, 'num');
  assert.strictEqual(c.get(k), 'obj');
  assert.strictEqual(c.get('1'), undefined);
});
