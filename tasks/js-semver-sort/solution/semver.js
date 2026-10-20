'use strict';

const NUM = '(0|[1-9]\\d*)';
const PRE_ID = '(?:0|[1-9]\\d*|\\d*[A-Za-z-][0-9A-Za-z-]*)';
const RE = new RegExp(`^v?${NUM}\\.${NUM}\\.${NUM}(?:-(${PRE_ID}(?:\\.${PRE_ID})*))?(?:\\+([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?$`);

function parse(v) {
  if (typeof v !== 'string') return null;
  const m = RE.exec(v.trim());
  if (!m) return null;
  return {
    major: +m[1], minor: +m[2], patch: +m[3],
    prerelease: m[4] ? m[4].split('.').map((p) => (/^\d+$/.test(p) ? +p : p)) : [],
    build: m[5] ? m[5].split('.') : [],
  };
}

function cmpParsed(x, y) {
  for (const k of ['major', 'minor', 'patch']) if (x[k] !== y[k]) return x[k] < y[k] ? -1 : 1;
  const a = x.prerelease, b = y.prerelease;
  if (!a.length && !b.length) return 0;
  if (!a.length) return 1;
  if (!b.length) return -1;
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if (a[i] === undefined) return -1;
    if (b[i] === undefined) return 1;
    if (a[i] === b[i]) continue;
    const an = typeof a[i] === 'number', bn = typeof b[i] === 'number';
    if (an && bn) return a[i] < b[i] ? -1 : 1;
    if (an) return -1;
    if (bn) return 1;
    return a[i] < b[i] ? -1 : 1;
  }
  return 0;
}

function compare(a, b) {
  const x = parse(a), y = parse(b);
  if (!x || !y) throw new TypeError('invalid version');
  return cmpParsed(x, y);
}

function sort(list) {
  return list.filter((v) => parse(v)).sort(compare);
}

function expand(token) {
  if (token === '*' || token === '') return [];
  const m = /^(\^|~|>=|<=|>|<|=)?(.*)$/.exec(token);
  const op = m[1] || '=';
  const v = parse(m[2]);
  if (!v) throw new TypeError(`bad comparator ${token}`);
  const s = (a, b, c) => ({ major: a, minor: b, patch: c, prerelease: [], build: [] });
  if (op === '^') {
    let upper;
    if (v.major > 0) upper = s(v.major + 1, 0, 0);
    else if (v.minor > 0) upper = s(0, v.minor + 1, 0);
    else upper = s(0, 0, v.patch + 1);
    return [{ op: '>=', v }, { op: '<', v: { ...upper, prerelease: [0] }, synthetic: true }];
  }
  if (op === '~') return [{ op: '>=', v }, { op: '<', v: { ...s(v.major, v.minor + 1, 0), prerelease: [0] }, synthetic: true }];
  return [{ op, v }];
}

function test(c, v) {
  const r = cmpParsed(v, c.v);
  switch (c.op) {
    case '=': return r === 0;
    case '>': return r > 0;
    case '>=': return r >= 0;
    case '<': return r < 0;
    case '<=': return r <= 0;
  }
  return false;
}

function satisfies(version, range) {
  const v = parse(version);
  if (!v) return false;
  return range.split('||').some((set) => {
    const comps = set.trim().split(/\s+/).flatMap(expand);
    if (!comps.every((c) => test(c, v))) return false;
    if (!v.prerelease.length) return true;
    return comps.some((c) => !c.synthetic && c.v.prerelease.length &&
      c.v.major === v.major && c.v.minor === v.minor && c.v.patch === v.patch);
  });
}

module.exports = { parse, compare, sort, satisfies };
