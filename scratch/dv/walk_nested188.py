#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Propagate a source-derived subset of Z95 from a conditional prototype-188 state.

This is a bounded static data analysis, not a Lua or VM runner. Unsupported
operations and uncertain values stop propagation; calls are never invoked.
"""
import argparse
import hashlib
from collections import Counter, deque
import json
from pathlib import Path

from decode_constants import decode
from patch_block import patch

MASK = 0xffffffff
FIELDS = ('g', 'G', 'B', 'p')


class UncertainTable(dict):
    pass


class Opaque:
    def __init__(self, name): self.name = name


def integer(x):
    return isinstance(x, int) and not isinstance(x, bool)


def u32(x):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError('expected integer')
    return x & MASK


def truth(x):
    return x is not None and x is not False


def lua_equal(a, b):
    if isinstance(a, bool) != isinstance(b, bool): return False
    if isinstance(a, dict) or isinstance(b, dict): return a is b
    return a == b


def point(arrays, pc, seed):
    """Rewrite the current instruction using source formulas for Z95 103/196."""
    i = pc - 1
    g, G, B, p = (arrays[k][i] for k in FIELDS)
    key = seed ^ ((seed >> 14) & 262143) ^ ((seed >> 28) & 15)
    if G == 103:
        width = 7 if g < 2097152 else 14
        result = {'g': (g & ((1 << width) - 1)) ^ 91 ^ ((key >> 7) & 127),
                  'B': B ^ 9 ^ ((key >> 14) & 127),
                  'G': (g >> width) ^ 35 ^ ((key >> 21) & 127),
                  'p': p ^ 78 ^ (key & 127)}
    elif G == 196:
        width = 7 if B < 16384 else (14 if B < 2097152 else 21)
        result = {'B': (B & ((1 << width) - 1)) ^ 105 ^ ((key >> 14) & 127),
                  'p': p ^ 17 ^ (key & 127),
                  'g': g ^ 122 ^ ((key >> 7) & 127),
                  'G': (B >> width) ^ 55 ^ ((key >> 21) & 127)}
    else:
        raise ValueError('not a point rewrite')
    for name in FIELDS:
        arrays[name][i] = result[name]
    return result


def table(values=()):
    return {i: value for i, value in enumerate(values, 1) if value is not None}


def length(t):
    if not isinstance(t, dict):
        raise ValueError('length of unknown table')
    n = 0
    while n + 1 in t:
        n += 1
    if any(isinstance(k, int) and k > n for k in t):
        raise ValueError('table length ambiguous')
    return n


def walk(arrays, data, offsets, registers, pc, f, b, max_steps=100000, compact=False):
    arrays = {k: list(arrays[k]) for k in FIELDS}
    data = bytearray(data)
    registers = dict(registers)
    cache, events = {}, []
    counts, tail = Counter(), deque(maxlen=20)
    reason = 'step_limit'
    for _ in range(max_steps):
        if pc < 1 or any(pc > len(arrays[k]) for k in FIELDS):
            reason = 'pc_out_of_bounds'; break
        i = pc - 1
        g, op, B, p = (arrays[k][i] for k in FIELDS)
        event = {'pc': pc, 'opcode': op, 'g': g, 'B': B, 'p': p}
        nxt = pc + 1
        def reg(index): return registers.get(index)
        def numeric(x):
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                raise ValueError('unknown numeric operand')
            return x
        def const(kind, index):
            key = (kind, pc)
            if key not in cache:
                entry = decode(data, offsets, index)
                if 'value' not in entry or entry['value'] is None:
                    raise ValueError('unknown constant')
                cache[key] = entry['value']
            return cache[key]
        def get(t, key):
            if not isinstance(t, dict) or key is None or (isinstance(t, UncertainTable) and key not in t):
                raise ValueError('unknown table access')
            return t.get(key)
        def set_(t, key, value):
            if not isinstance(t, dict) or key is None:
                raise ValueError('unknown table write')
            if value is None: t.pop(key, None)
            else: t[key] = value
        try:
            if op in (103, 196):
                event['point'] = point(arrays, pc, f); nxt = pc
            elif op in (75, 100, 121):
                result = patch(arrays, pc, b if op == 75 else f, 'Z95')
                arrays = result.pop('arrays'); event['rewrite'] = {k: result[k] for k in ('start', 'count', 'initial_state')}
            elif op == 179: pass
            elif op == 162: nxt = g + 1
            elif op == 185: nxt = numeric(reg(g)) + 1
            elif op == 176: registers[B] = p
            elif op == 41: registers[B] = reg(g)
            elif op == 122: registers[p], registers[p+1] = reg(B), reg(g)
            elif op == 183: registers[B] = {}
            elif op == 190: registers[B] = {}  # table.create capacity only
            elif op == 85:
                target = reg(B)
                for j in range(p): set_(target, g+j+1, reg(B+j+1))
            elif op == 136: registers[p] = get(reg(B), g)
            elif op == 182: registers[B] = get(reg(p), reg(g))
            elif op == 184: set_(reg(B), g, reg(p))
            elif op == 88:
                target, key, value = reg(B), reg(g), reg(p)
                event['table_write'] = {'key': key, 'previous': get(target,key), 'value': value}
                set_(target, key, value)
            elif op == 114: registers[g] = length(reg(p))
            elif op == 171: registers[g] = const('n', B)
            elif op == 131: registers[g], registers[g+1] = const('P', p), const('n', B)
            elif op == 143: registers[p] = numeric(const('n', B)) + numeric(const('L', g))
            elif op == 3: registers[g] = p - numeric(reg(B))
            elif op == 25: registers[B] = numeric(reg(g)) - p
            elif op in (52, 101): registers[B] = numeric(reg(g)) + p
            elif op == 150: registers[B] = numeric(reg(g)) + numeric(reg(p))
            elif op == 193: registers[g] = numeric(reg(B)) % numeric(reg(p))
            elif op == 194: registers[B] = numeric(const('L', g)) % numeric(reg(p))
            elif op == 109: registers[B] = numeric(reg(p)) + numeric(const('L', g))
            elif op == 198: registers[g] = numeric(reg(p)) - numeric(reg(B))
            elif op in (81, 191): registers[B] = u32(const('L', g)) | u32(reg(p))
            elif op == 23: registers[B] = numeric(const('P', p)) + numeric(reg(g))
            elif op == 91: registers[B] = f
            elif op == 110 and g in (6, 10, 63, 76): registers[B] = Opaque(f'd[{g}]')
            elif op == 46:
                fn, arg, index, value = reg(B), reg(B+1), reg(B+2), reg(B+3)
                if not (g == 3 and p == 0 and isinstance(fn, Opaque) and fn.name == 'd[76]' and isinstance(arg, Opaque) and arg.name == 'shared_buffer' and integer(index) and 0 <= index <= len(data)-4 and integer(value)):
                    raise ValueError('unknown call')
                before = bytes(data[index:index+4]).hex()
                data[index:index+4] = u32(value).to_bytes(4, 'little')
                event['static_buffer_write'] = {'offset': index, 'before': before, 'after': bytes(data[index:index+4]).hex()}
            elif op == 94:
                fn, arg, index = reg(p), reg(p+1), reg(p+2)
                if not (isinstance(fn, Opaque) and fn.name == 'd[6]' and isinstance(arg, Opaque) and arg.name == 'shared_buffer' and integer(index) and 0 <= index <= len(data)-2):
                    raise ValueError('unknown call')
                value = int.from_bytes(data[index:index+2], 'little', signed=True)
                registers[p] = value
                event['static_buffer_read'] = {'offset': index, 'size': 2, 'value': value}
            elif op == 187:
                if pc >= len(arrays['p']): raise ValueError('missing fused instruction')
                base = arrays['p'][pc]
                fn, arg, index = reg(base), reg(base+1), reg(g)
                if not (B == base+2 and isinstance(fn, Opaque) and fn.name == 'd[63]' and isinstance(arg, Opaque) and arg.name == 'shared_buffer' and integer(index) and 0 <= index < len(data)):
                    raise ValueError('unknown fused call')
                registers[B] = index
                registers[base] = data[index]
                event['static_buffer_read'] = {'offset': index, 'size': 1, 'value': data[index]}
                nxt = pc + 2
            elif op == 105 and isinstance(reg(p), Opaque) and reg(p).name == 'd[10]' and isinstance(reg(g), Opaque) and reg(g).name == 'shared_buffer': registers[B] = len(data)
            elif op == 95: registers[B] = not lua_equal(reg(p), g)
            elif op == 60: registers[p] = numeric(reg(g)) <= B
            elif op == 130: registers[g] = numeric(reg(B)) >= numeric(reg(p))
            elif op == 28: registers[B] = numeric(reg(p)) <= numeric(reg(g))
            elif op == 146: registers[p] = not truth(reg(g))
            elif op in (86, 155): nxt = (p if truth(reg(g)) else B) + 1
            elif op == 156: nxt = pc + 1 if numeric(reg(B)) <= g else p + 1
            elif op == 129: registers[g] = u32(reg(p))
            elif op == 111: registers[g] = u32(reg(B)) & u32(reg(p))
            elif op == 195: registers[B] = u32(reg(g)) & u32(p)
            elif op == 108: registers[g] = u32(reg(p)) | u32(reg(B))
            elif op == 0: registers[B] = u32(reg(g)) | u32(p)
            elif op == 164: registers[g] = u32(reg(B)) ^ u32(p)
            elif op == 174: registers[B] = u32(reg(p)) & u32(const('L', g))
            elif op == 51: registers[p] = u32(const('L', g)) & u32(reg(B))
            elif op == 98: registers[B] = u32(g) ^ u32(reg(p))
            elif op == 123: registers[p] = u32(reg(B)) ^ u32(const('L', g))
            elif op == 189: registers[g] = (u32(p) * u32(reg(B))) & MASK
            elif op == 181: registers[B] = (u32(p) * u32(reg(g))) & MASK
            elif op == 20: registers[B] = u32(reg(p)) ^ u32(reg(g))
            elif op == 5: registers[B] = ~u32(reg(g)) & MASK
            elif op == 72: registers[p] = (u32(reg(g)) << B) & MASK
            elif op == 99: registers[B] = u32(reg(p)) >> g
            elif op == 54: registers[g] = (u32(reg(p)) * u32(reg(B))) & MASK
            elif op == 168: registers[g] = (u32(const('n', B)) * u32(reg(p))) & MASK
            else: reason = 'unsupported_opcode'; break
        except (ValueError, TypeError, IndexError, KeyError, OverflowError, ZeroDivisionError) as exc:
            reason = str(exc); break
        counts['steps'] += 1
        for name in ('point', 'rewrite', 'table_write', 'static_buffer_read', 'static_buffer_write'):
            if name in event: counts[name] += 1
        tail.append(event)
        if not compact or ('table_write' in event or ('point' in event and counts['point'] <= 100) or
                           ('rewrite' in event and counts['rewrite'] <= 100) or
                           ('static_buffer_read' in event and counts['static_buffer_read'] <= 16) or
                           ('static_buffer_write' in event and counts['static_buffer_write'] <= 16)):
            events.append(event)
        pc = nxt
    return {'pc': pc, 'stop_reason': reason, 'counts': dict(counts), 'tail': list(tail), 'stop_instruction': ({k: arrays[k][pc-1] for k in FIELDS} if pc >= 1 and all(pc <= len(arrays[k]) for k in FIELDS) else None), 'events': events, 'arrays': arrays, 'registers': registers,
            'data': data, 'constant_cache': [{'kind': k[0], 'pc': k[1], 'value': v} for k, v in cache.items()]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--nested', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--buffer', type=Path, required=True)
    ap.add_argument('--table', type=Path, required=True)
    ap.add_argument('--max-steps', type=int, default=100000)
    ap.add_argument('--output-buffer', type=Path)
    ap.add_argument('--compact', action='store_true')
    args = ap.parse_args()
    raw = {k: getattr(args,k).read_bytes() for k in ('nested','parent','buffer','table')}
    nested = json.loads(raw['nested'])['records'][0]['tables']['arrays']
    parent = json.loads(raw['parent'])['arrays']
    f, b = 1263948163, 3290891004
    arrays = nested
    for pc, seed, mode in ((755,f,'E201'), (756,b,'E201'), (757,f,'E201'), (758,f,'E201'),
                           (713,b,'Z95'), (462,b,'Z95'), (512,b,'Z95')):
        arrays = patch(arrays, pc, seed, mode)['arrays']
    for pc in (337,648,461,470,514,508,506): point(arrays, pc, f)
    for pc, values in {745:(51,24,5,2), 752:(51,5,45,14), 582:(138,0,95,336)}.items():
        for name, value in zip(FIELDS, values): arrays[name][pc-1] = value
    p, B, G, g = (table(parent[k]) for k in ('p','B','G','g'))
    registers = {6:18, 22:484, 29:530914979, 30:UncertainTable({4:Opaque('shared_buffer')}), 31:p, 32:B, 33:G, 34:g,
                 35:table((p,B,G,g)), 36:p, 37:B, 38:G, 39:g}
    info = json.loads(raw['table'])
    result = walk(arrays, raw['buffer'], info['updated_offsets'], registers, 485, f, b, args.max_steps, args.compact)
    updated_buffer = result.pop('data')
    if args.output_buffer: args.output_buffer.write_bytes(updated_buffer)
    result['output_buffer_sha256'] = hashlib.sha256(updated_buffer).hexdigest()
    result['parent_arrays'] = {k: v for k,v in zip(('p','B','G','g'), (p,B,G,g))}
    result['registers'] = {str(k): ({'opaque': v.name} if isinstance(v, Opaque) else v) for k,v in result['registers'].items() if not isinstance(v,dict)}
    result['_provenance'] = {'generator':'CodeRabbit','version':1}
    result['input_sha256'] = {k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['limitations'] = ('Conditional snapshot and prior parent-path hypotheses; fresh per-PC constant caches assumed. '
                             'Partial Z95 transfer only; known buffer intrinsics are modeled as data operations, and unknown calls stop the walk.')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
