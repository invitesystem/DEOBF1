#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Catalog candidate constants from a conditional static snapshot.

Offsets and tags can still be encrypted. An apparently decodable entry is not
proof that it is reachable or that its record is fully decrypted.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

from decode_constants import decode


def catalog(data, offsets):
    entries = []
    for index, offset in enumerate(offsets, 1):
        if not isinstance(offset, int) or not 0 <= offset < len(data):
            entries.append({'index': index, 'offset': offset, 'status': 'unresolved_offset'})
            continue
        try:
            entry = decode(data, offsets, index)
        except (ValueError, IndexError, OverflowError) as error:
            entries.append({'index': index, 'offset': offset, 'tag': data[offset],
                            'status': 'unresolved', 'reason': str(error)})
            continue
        entry['status'] = 'candidate'
        entries.append(entry)
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--buffer', type=Path, required=True)
    ap.add_argument('--table', type=Path, required=True)
    args = ap.parse_args()
    data, raw = args.buffer.read_bytes(), args.table.read_bytes()
    table = json.loads(raw)
    offsets = table.get('updated_offsets', table.get('values'))
    if offsets is None: raise ValueError('missing offsets')
    entries = catalog(data, offsets)
    print(json.dumps({'_provenance': {'generator': 'CodeRabbit', 'version': 1},
                      'input_sha256': {'buffer': hashlib.sha256(data).hexdigest(),
                                       'table': hashlib.sha256(raw).hexdigest()},
                      'counts': dict(collections.Counter(e['status'] for e in entries)),
                      'entries': entries,
                      'limitations': 'Candidates only: prior decryption, cache state and reachability are unproven.'},
                     ensure_ascii=True, indent=2, allow_nan=False))

if __name__ == '__main__':
    main()
