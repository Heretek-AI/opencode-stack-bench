'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const sv = require(path.join(process.cwd(), 'semver.js'));

test('parse basic and v prefix', () => {
  assert.deepStrictEqual(sv.parse('v1.2.3-alpha.1+build.5'), {
    major: 1, minor: 2, patch: 3, prerelease: ['alpha', 1], build: ['build', '5'],
  });
});

test('parse rejects invalid', () => {
  for (const bad of ['1.2', '01.2.3', '1.2.3-01', 'a.b.c', '1.2.3-', '1.2.3+']) {
    assert.strictEqual(sv.parse(bad), null, bad);
  }
});

test('compare precedence chain from spec', () => {
  const chain = ['1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.beta', '1.0.0-beta',
    '1.0.0-beta.2', '1.0.0-beta.11', '1.0.0-rc.1', '1.0.0'];
  for (let i = 0; i < chain.length - 1; i++) {
    assert.strictEqual(sv.compare(chain[i], chain[i + 1]), -1, `${chain[i]} < ${chain[i + 1]}`);
    assert.strictEqual(sv.compare(chain[i + 1], chain[i]), 1);
  }
});

test('compare ignores build and throws on invalid', () => {
  assert.strictEqual(sv.compare('1.0.0+a', '1.0.0+b'), 0);
  assert.throws(() => sv.compare('x', '1.0.0'), TypeError);
});

test('sort is non-mutating and drops invalid', () => {
  const input = ['1.10.0', 'bad', '1.2.0', '1.2.0-rc.1'];
  const out = sv.sort(input);
  assert.deepStrictEqual(out, ['1.2.0-rc.1', '1.2.0', '1.10.0']);
  assert.strictEqual(input[0], '1.10.0');
});

test('satisfies comparators and ||', () => {
  assert.ok(sv.satisfies('1.5.0', '>=1.2.0 <2.0.0'));
  assert.ok(!sv.satisfies('2.0.0', '>=1.2.0 <2.0.0'));
  assert.ok(sv.satisfies('3.0.0', '^1.0.0 || >=3.0.0'));
  assert.ok(sv.satisfies('1.2.3', '1.2.3'));
  assert.ok(sv.satisfies('9.9.9', '*'));
});

test('caret and tilde', () => {
  assert.ok(sv.satisfies('1.9.9', '^1.2.3'));
  assert.ok(!sv.satisfies('2.0.0', '^1.2.3'));
  assert.ok(sv.satisfies('0.2.9', '^0.2.3'));
  assert.ok(!sv.satisfies('0.3.0', '^0.2.3'));
  assert.ok(!sv.satisfies('0.0.4', '^0.0.3'));
  assert.ok(sv.satisfies('1.2.9', '~1.2.3'));
  assert.ok(!sv.satisfies('1.3.0', '~1.2.3'));
});

test('prerelease rules', () => {
  assert.ok(!sv.satisfies('1.3.0-beta', '^1.2.0'));
  assert.ok(sv.satisfies('1.2.3-beta.2', '>=1.2.3-beta.1 <2.0.0'));
  assert.ok(!sv.satisfies('1.2.4-beta.2', '>=1.2.3-beta.1 <2.0.0'));
});
