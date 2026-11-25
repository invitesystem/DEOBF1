#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Source-derived 2288 byte transform; captured tables are explicit inputs."""
import argparse
import hashlib
import json
from pathlib import Path


def unmask(data, seed, record_index, words, next_indices):
    if not 0 <= seed <= 255 or not isinstance(record_index, int) or record_index < 0:
        raise ValueError('invalid seed or record index')
    if len(words) != 256 or len(next_indices) != 256:
        raise ValueError('captured tables must contain 256 entries')
    if any(not isinstance(v, int) or not 0 <= v <= 0xffffffff for v in words):
        raise ValueError('captured words must be unsigned 32-bit integers')
    if any(not isinstance(v, int) or not 0 <= v <= 255 for v in next_indices):
        raise ValueError('captured indices must be bytes')
    data = bytes(data)
    output = bytearray()
    index = (seed + record_index) % 256
    end = len(data) - len(data) % 4
    for pos in range(0, end, 4):
        value = int.from_bytes(data[pos:pos+4], 'little') ^ words[index] ^ (seed * 0x01010101)
        output.extend(value.to_bytes(4, 'little'))
        index = next_indices[index]
    for pos in range(end, len(data)):
        index = (181 * index + 99) % 256
        output.append(data[pos] ^ seed ^ index)
    return bytes(output), index


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--tables', type=Path, required=True, help='JSON object with words and next_indices arrays')
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--record-index', type=int, required=True)
    args = ap.parse_args()
    data, table_data = args.input.read_bytes(), args.tables.read_bytes()
    tables = json.loads(table_data)
    out, end_index = unmask(data, args.seed, args.record_index, tables['words'], tables['next_indices'])
    args.output.write_bytes(out)
    print(json.dumps({'_provenance':{'generator':'CodeRabbit','version':1},
                      'input_sha256':hashlib.sha256(data).hexdigest(),
                      'table_sha256':hashlib.sha256(table_data).hexdigest(),
                      'output_sha256':hashlib.sha256(out).hexdigest(),
                      'seed':args.seed, 'record_index':args.record_index, 'end_index':end_index,
                      'limitations':'The captured tables, data range, seed and reachability are external hypotheses; no tw or Lua code is executed.'}, indent=2))

if __name__ == '__main__': main()
