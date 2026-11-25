#!/usr/bin/env python3
"""Apply a source-derived block rewrite as a static data transform."""
import argparse
import hashlib
import json
from pathlib import Path

MASK29 = (1 << 29) - 1
MASK32 = (1 << 32) - 1


def patch(arrays: dict[str, list[int]], pc: int, seed: int, mode: str = 'E201') -> dict:
    if mode not in ('E201', 'Z250', 'Z95', 'Z240'):
        raise ValueError('unsupported dispatcher')
    if not 0 <= seed <= MASK32 or pc < 1:
        raise ValueError('invalid seed or program counter')
    arrays = {name: list(arrays[name]) for name in ('g', 'G', 'B', 'p')}
    if any(pc > len(values) for values in arrays.values()):
        raise ValueError('program counter outside arrays')
    for values in arrays.values():
        if any(not isinstance(value, int) or not 0 <= value <= MASK32 for value in values):
            raise ValueError('array entries must be unsigned 32-bit integers')
    at = pc - 1
    opcode_field = {'Z95': 'G', 'Z240': 'p'}.get(mode, 'g')
    opcode = arrays[opcode_field][at]
    expected = {'E201': (59, 119, 170), 'Z250': (35, 49, 83), 'Z95': (75, 100, 121), 'Z240': (0, 93, 177)}[mode]
    if opcode not in expected:
        raise ValueError('unexpected opcode for dispatcher at program counter')
    direct = (mode, opcode) in (('E201', 170), ('Z250', 49), ('Z95', 121), ('Z240', 93))
    start_field = {('E201', 170): 'G', ('Z250', 49): 'p', ('Z95', 121): 'B'}.get((mode, opcode),
        {'E201': 'B', 'Z250': 'G', 'Z95': 'p', 'Z240': 'G'}[mode])
    count_field = {('E201', 170): 'B', ('Z250', 49): 'B', ('Z95', 121): 'g', ('Z240', 0): 'B', ('Z240', 177): 'B'}.get((mode, opcode),
        {'Z95': 'B', 'Z240': 'g'}.get(mode, 'p'))
    start = arrays[start_field][at] + 1  # Lua's one-based PC
    count = arrays[count_field][at]
    if count and (start < 1 or any(start + count - 1 > len(values) for values in arrays.values())):
        raise ValueError('rewrite range outside arrays')
    state_field = {('E201', 170): 'p', ('Z250', 49): 'G', ('Z95', 121): 'p', ('Z240', 0): 'g', ('Z240', 177): 'g'}.get((mode, opcode),
        {'E201': 'G', 'Z250': 'B', 'Z95': 'g', 'Z240': 'B'}[mode])
    state = arrays[state_field][at]
    if not direct:
        state ^= (seed ^ ((seed >> 29) & 7)) & MASK29
    initial_state = state
    for pos in range(start - 1, start - 1 + count):
        state = (state ^ ((state << 13) & MASK32)) & MASK29
        state ^= state >> 13
        state = (state ^ ((state << 14) & MASK32)) & MASK29
        names = {'E201': ('B', 'G', 'p', 'g'), 'Z250': ('G', 'B', 'p', 'g'), 'Z95': ('p', 'g', 'B', 'G'), 'Z240': ('G', 'g', 'B', 'p')}[mode]
        for name, shift in zip(names, (0, 7, 14, 21)):
            arrays[name][pos] ^= (state >> shift) & 127
    arrays[opcode_field][at] = {'E201': 27, 'Z250': 164, 'Z95': 179, 'Z240': 154}[mode]
    return {'_provenance': {'generator': 'CodeRabbit', 'version': 1},
            'pc': pc, 'opcode': opcode, 'mode': mode, 'seed': seed, 'initial_state': initial_state,
            'start': start, 'count': count, 'arrays': arrays,
            'limitations': 'Only the specified block rewrite and opcode replacement are applied; earlier mutations are not included.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arrays', type=Path, help='previous block-rewrite JSON')
    parser.add_argument('--code', type=Path)
    parser.add_argument('--g-operand', type=Path)
    parser.add_argument('--b-operand', type=Path)
    parser.add_argument('--p-operand', type=Path)
    parser.add_argument('--pc', type=int, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--mode', choices=('E201', 'Z250', 'Z95', 'Z240'), default='E201')
    args = parser.parse_args()
    paths = {'g': args.code, 'G': args.g_operand, 'B': args.b_operand, 'p': args.p_operand}
    if args.arrays:
        if any(paths.values()):
            parser.error('--arrays cannot be combined with individual array files')
        raw = {'arrays': args.arrays.read_bytes()}
        decoded = json.loads(raw['arrays'])['arrays']
    else:
        if not all(paths.values()):
            parser.error('provide --arrays or all four individual array files')
        raw = {name: path.read_bytes() for name, path in paths.items()}
        decoded = {name: json.loads(content)['values'] for name, content in raw.items()}
    result = patch(decoded, args.pc, args.seed, args.mode)
    result['input_sha256'] = {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()}
    print(json.dumps(result, indent=2))
