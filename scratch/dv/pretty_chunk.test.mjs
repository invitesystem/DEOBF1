import assert from 'node:assert/strict';
import test from 'node:test';
import { parse } from '../../packages/core/src/parser.js';
import { equivalentSyntax, formatLiteral } from './pretty_chunk.ts';

test('compares grouping while preserving multiple-return parentheses', () => {
  const ast = source => parse(source).chunk;
  assert.equal(equivalentSyntax(ast('return (a + b)'), ast('return a + b')), true);
  assert.equal(equivalentSyntax(ast('return (f())'), ast('return f()')), false);
  assert.equal(equivalentSyntax(ast('return (...)'), ast('return ...')), false);
  assert.equal(equivalentSyntax(ast('return 1'), ast('return 2')), false);
  assert.equal(equivalentSyntax(ast('if a then x() else if b then y() end end'),
                                ast('if a then x() elseif b then y() end')), true);
});

test('formats literal syntax without evaluating it', () => {
  const result = formatLiteral('local CHUNK = [=[return function() error("not executed") end]=]', 'CHUNK');
  assert.match(result.formatted, /error\("not executed"\)/);
  assert.equal(result.matchingTables, 0);
  assert.throws(() => formatLiteral('local CHUNK = "return 1"', 'CHUNK'));
  assert.throws(() => formatLiteral('local CHUNK=[=[return 1]=]; local CHUNK=[=[return 2]=]', 'CHUNK'));
});
