'use strict';

function parse(v) {
  const m = /^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$/.exec(v);
  if (!m) return null;
  return {
    major: +m[1], minor: +m[2], patch: +m[3],
    prerelease: m[4] ? m[4].split('.') : [],
    build: [],
  };
}

function compare(a, b) {
  const x = parse(a), y = parse(b);
  for (const k of ['major', 'minor', 'patch']) {
    if (x[k] !== y[k]) return x[k] < y[k] ? -1 : 1;
  }
  return 0;
}

function sort(list) {
  return list.sort(compare);
}

function satisfies(v, range) {
  throw new Error('not implemented');
}

module.exports = { parse, compare, sort, satisfies };
