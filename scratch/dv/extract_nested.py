#!/usr/bin/env python3
"""Extract explicitly selected nested records as data; never execute their code."""
import argparse
import hashlib
import json
from pathlib import Path

from init_table import read_value
from nested_tables import extract as extract_tables
from unmask_record import unmask


def extract_nested(data: bytes, offsets: list[int], index: int, seed: int) -> dict:
    if not 0 <= seed <= 255:
        raise ValueError('seed must be a byte')
    if not 1 <= index <= len(offsets):
        raise ValueError('record index outside table')
    offset = offsets[index - 1]
    if not 0 <= offset < len(data):
        raise ValueError('record offset outside buffer')
    if data[offset] != 184:
        raise ValueError(f'expected nested-record tag 184 at index {index}')
    length, start, _ = read_value(data, offset + 1)
    if start + length > len(data):
        raise ValueError('nested record outside buffer')
    initial_index = (seed + index) % 256
    plain = unmask(data[start:start + length], seed, initial_index)
    result = {'index': index, 'offset': offset, 'start': start, 'length': length,
              'seed': seed, 'mask_index': initial_index,
              'decoded_sha256': hashlib.sha256(plain).hexdigest()}
    if plain.startswith(b'\x02\x01\x00'):
        selector, cursor, _ = read_value(plain, 3)
        result['native_factory'] = {'selector': selector, 'selector_end': cursor,
                                    'remaining_hex': plain[cursor:].hex(),
                                    'limitations': 'The 02 01 00 header follows the source-derived direct-factory path; remaining bytes are not interpreted.'}
    else:
        result['tables'] = extract_tables(plain)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--indices', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    data = args.buffer.read_bytes()
    table_data = args.table.read_bytes()
    table = json.loads(table_data)
    offsets = table.get('updated_offsets', table.get('values'))
    if offsets is None:
        raise ValueError('table has neither values nor updated_offsets')
    records = [extract_nested(data, offsets, int(i), args.seed) for i in args.indices.split(',')]
    print(json.dumps({'_provenance': {'generator': 'CodeRabbit', 'version': 1},
                      'input_sha256': {'buffer': hashlib.sha256(data).hexdigest(),
                                       'table': hashlib.sha256(table_data).hexdigest()},
                      'records': records,
                      'limitations': 'Indices, record mutations and reachability are external hypotheses; decoded tables are not executed.'}, indent=2))
