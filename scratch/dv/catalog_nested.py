#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Extract candidate tag-184 prototypes from a conditional snapshot as data."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_nested import extract_nested


def catalog(data, offsets, seed=186):
    records, failures = [], []
    for index, offset in enumerate(offsets, 1):
        if not isinstance(offset, int) or not 0 <= offset < len(data) or data[offset] != 184:
            continue
        try:
            records.append(extract_nested(data, offsets, index, seed))
        except (ValueError, IndexError, OverflowError) as error:
            failures.append({'index':index, 'offset':offset, 'reason':str(error)})
    return records, failures


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--buffer', type=Path, required=True)
    ap.add_argument('--table', type=Path, required=True)
    args = ap.parse_args()
    data, raw = args.buffer.read_bytes(), args.table.read_bytes()
    meta = json.loads(raw)
    offsets = meta.get('updated_offsets', meta.get('values'))
    if offsets is None: raise ValueError('missing offsets')
    records, failures = catalog(data, offsets)
    print(json.dumps({'_provenance': {'generator':'CodeRabbit','version':1},
                      'input_sha256': {'buffer':hashlib.sha256(data).hexdigest(),
                                       'table':hashlib.sha256(raw).hexdigest()},
                      'counts': {'vm':sum('tables' in x for x in records),
                                 'native_factory':sum('native_factory' in x for x in records),
                                 'unresolved':len(failures)},
                      'records': records, 'unresolved': failures,
                      'limitations':'Candidates only: input mutations, factory captures and reachability remain unproven.'}, indent=2))

if __name__ == '__main__': main()
