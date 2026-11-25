#!/usr/bin/env python3
"""Apply an explicitly supplied sequence of source-derived record XOR operations."""
import argparse
import hashlib
import json
from pathlib import Path

from init_table import read_value


def extract(data: bytes, offsets: list[int], arrays: dict[str, list[int]],
            pcs: list[int], f_seed: int, b_seed: int, mode: str = 'E201') -> tuple[bytes, list[int], list[dict]]:
    if mode not in ('E201', 'Z250', 'Z95', 'Z240'):
        raise ValueError('unsupported dispatcher')
    if not all(0 <= value <= 0xffffffff for value in (f_seed, b_seed)):
        raise ValueError('seeds must be unsigned 32-bit integers')
    data = bytearray(data)
    offsets = list(offsets)
    records = []
    for pc in pcs:
        fields = ('g', 'G', 'B', 'p') if mode in ('Z95', 'Z240') else ('g', 'G', 'B')
        if pc < 1 or any(pc > len(arrays[name]) for name in fields):
            raise ValueError(f'pc out of range: {pc}')
        i = pc - 1
        opcode = arrays[{'Z95': 'G', 'Z240': 'p'}.get(mode, 'g')][i]
        expected = {'E201': (53, 99, 172), 'Z250': (56, 129), 'Z95': (14, 24, 63), 'Z240': (120,)}[mode]
        if opcode not in expected:
            raise ValueError(f'unexpected record opcode at pc {pc}')
        if (mode, opcode) == ('E201', 172) and ('p' not in arrays or pc > len(arrays['p'])):
            raise ValueError(f'pc out of range for direct record index: {pc}')
        index = arrays['p' if (mode, opcode) == ('E201', 172) else
                       {'E201': 'B', 'Z250': 'G', 'Z95': 'p', 'Z240': 'g'}[mode]][i]
        if not 1 <= index <= len(offsets):
            raise ValueError(f'record index out of range at pc {pc}')
        if (mode, opcode) in (('E201', 172), ('Z95', 24), ('Z240', 120)):
            key = arrays['G' if mode == 'Z240' else 'B'][i]
        else:
            seed = f_seed if opcode in (53, 56, 14) else b_seed
            encoded_key = arrays[{'E201': 'G', 'Z250': 'B', 'Z95': 'g'}[mode]][i]
            key = encoded_key ^ ((seed ^ ((seed >> 29) & 7)) & 0x1fffffff)
        if not 0 <= key <= 255:
            raise ValueError(f'non-byte XOR key at pc {pc}')
        offset = offsets[index - 1] ^ 236682589
        length, start, _ = read_value(data, offset + 1)
        if start + length > len(data):
            raise ValueError(f'record out of bounds at pc {pc}')
        offsets[index - 1] = offset
        for j in range(start, start + length):
            data[j] ^= key
        records.append({'pc': pc, 'opcode': opcode, 'index': index, 'key': key,
                        'offset': offset, 'start': start, 'length': length,
                        'result_hex': bytes(data[start:start + length]).hex()})
    return bytes(data), offsets, records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--arrays', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offset', type=int, required=True)
    parser.add_argument('--length', type=int, required=True)
    parser.add_argument('--f-seed', type=int, required=True)
    parser.add_argument('--b-seed', type=int, required=True)
    parser.add_argument('--mode', choices=('E201', 'Z250', 'Z95', 'Z240'), default='E201')
    parser.add_argument('--pcs', required=True, help='comma-separated, explicitly established PC order')
    args = parser.parse_args()
    raw = {'buffer': args.buffer.read_bytes(), 'table': args.table.read_bytes(), 'arrays': args.arrays.read_bytes()}
    if args.offset < 0 or args.length < 0 or args.offset + args.length > len(raw['buffer']):
        raise ValueError('block outside buffer')
    pcs = [int(value) for value in args.pcs.split(',')]
    table = json.loads(raw['table'])
    offsets = table.get('updated_offsets', table.get('values'))
    if offsets is None:
        raise ValueError('table has neither values nor updated_offsets')
    result, offsets, records = extract(raw['buffer'][args.offset:args.offset + args.length],
                                       offsets, json.loads(raw['arrays'])['arrays'],
                                       pcs, args.f_seed, args.b_seed, args.mode)
    args.output.write_bytes(result)
    print(json.dumps({'_provenance': {'generator': 'CodeRabbit', 'version': 1},
                      'input_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()},
                      'block_offset': args.offset, 'block_length': args.length,
                      'f_seed': args.f_seed, 'b_seed': args.b_seed, 'mode': args.mode,
                      'output_sha256': hashlib.sha256(result).hexdigest(),
                      'updated_offsets': offsets, 'records': records,
                      'limitations': 'The supplied PC order is an external static hypothesis; control flow is not evaluated.'}, indent=2))
