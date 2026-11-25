// Static formatting of a literal Lua chunk; no Lua or analyzed code is run.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { parse } from '../../packages/core/src/parser.js';
import { print } from '../../packages/core/src/printer.js';
import { walk } from '../../packages/core/src/ast.js';

const hash = (value: Uint8Array) => createHash('sha256').update(value).digest('hex');

// The printer adds grouping parentheses and flattens else-if chains. Preserve
// parentheses around calls and varargs, where Lua multiple returns can change.
export function equivalentSyntax(left: any, right: any): boolean {
  while (left?.type === 'ParenExpr' && !['CallExpr', 'MethodCallExpr', 'VarargLit'].includes(left.expr?.type)) left = left.expr;
  while (right?.type === 'ParenExpr' && !['CallExpr', 'MethodCallExpr', 'VarargLit'].includes(right.expr?.type)) right = right.expr;
  if (left === right) return true;
  if ((left === undefined && Array.isArray(right) && right.length === 0) ||
      (right === undefined && Array.isArray(left) && left.length === 0)) return true;
  if (left === null || right === null || typeof left !== 'object' || typeof right !== 'object') return false;
  if (Array.isArray(left) !== Array.isArray(right)) return false;
  if (left.type === 'IfStat' && right.type === 'IfStat') {
    const flatten = (node: any) => {
      const clauses = [...node.clauses];
      let tail = node.elseBody;
      while (tail?.length === 1 && tail[0].type === 'IfStat') {
        clauses.push(...tail[0].clauses);
        tail = tail[0].elseBody;
      }
      return { clauses, elseBody: tail ?? [] };
    };
    const a = flatten(left), b = flatten(right);
    return equivalentSyntax(a.clauses, b.clauses) && equivalentSyntax(a.elseBody, b.elseBody);
  }
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  for (const key of keys) {
    if (key !== 'loc' && key !== 'raw' && !equivalentSyntax(left[key], right[key])) return false;
  }
  return true;
}

export function formatLiteral(source: string, localName: string) {
  const wrapper = parse(source);
  if (wrapper.errors.length) throw new Error(`wrapper has ${wrapper.errors.length} parse errors`);
  const initializers: any[] = [];
  for (const statement of wrapper.chunk.body) {
    if (statement.type !== 'LocalStat') continue;
    statement.names.forEach((name, index) => {
      if (name === localName) initializers.push(statement.init[index]);
    });
  }
  if (initializers.length !== 1 || initializers[0]?.type !== 'StringLit' || !initializers[0].long) {
    throw new Error(`expected exactly one long-string initializer for ${localName}`);
  }
  const bytes = Buffer.from(initializers[0].value, 'latin1');
  const chunk = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  const parsed = parse(chunk);
  if (parsed.errors.length) throw new Error(`chunk has ${parsed.errors.length} parse errors`);
  const formatted = print(parsed.chunk);
  const roundtrip = parse(formatted);
  if (roundtrip.errors.length || !equivalentSyntax(parsed.chunk, roundtrip.chunk)) {
    throw new Error(`printed chunk failed syntax comparison (${roundtrip.errors.length} parse errors)`);
  }
  const tables: any[] = [];
  walk(parsed.chunk, (node: any) => {
    if (node.type === 'TableExpr' && node.fields.some((field: any) =>
      field.kind === 'named' && field.name === 'tw' && field.value.type === 'FunctionExpr')) tables.push(node);
  });
  const fieldCounts = tables.length === 1 ? tables[0].fields.reduce((result: any, field: any) => {
    result.total++;
    if (field.value.type === 'FunctionExpr') result.functions++;
    return result;
  }, { total: 0, functions: 0 }) : null;
  return { formatted, chunkSha256: hash(bytes), fieldCounts, matchingTables: tables.length };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [sourcePath, localName, outputPath] = process.argv.slice(2);
  if (!sourcePath || !localName || !outputPath) throw new Error('usage: pretty_chunk.ts <wrapper.lua> <literal-local> <output.lua>');
  const source = readFileSync(sourcePath);
  const result = formatLiteral(new TextDecoder('utf-8', { fatal: true }).decode(source), localName);
  const output = '-- coderabbit-ai-generated:v1\n-- Static formatting for inspection; VM bytecode remains virtualized.\n' + result.formatted;
  writeFileSync(outputPath, output);
  console.log(JSON.stringify({ _provenance: { generator: 'CodeRabbit', version: 1 },
    sourceSha256: hash(source), chunkSha256: result.chunkSha256,
    outputSha256: hash(Buffer.from(output)), matchingTables: result.matchingTables,
    fieldCounts: result.fieldCounts, syntaxRoundtrip: true,
    limitations: 'Normalized AST comparison is based on the same parser; it is not independent proof of runtime equivalence or bytecode recovery.' }, null, 2));
}
