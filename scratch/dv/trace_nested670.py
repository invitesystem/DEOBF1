#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Check selected source-derived point rewrites in the conditional 670 trace."""
import hashlib
import json
from pathlib import Path

F, B = 1193198983, 4199977214


def point(mode, instruction, seed):
    g, G, b, p = (instruction[k] for k in ('g', 'G', 'B', 'p'))
    key = seed ^ ((seed >> 14) & 262143) ^ ((seed >> 28) & 15)
    if mode == 'E201' and g == 173:
        w = 7 if G < 16384 else (14 if G < 2097152 else 21)
        return {'g': (G >> w) ^ 57 ^ (key >> 21 & 127),
                'G': (G & ((1 << w) - 1)) ^ 52 ^ (key >> 7 & 127),
                'B': b ^ 104 ^ (key & 127), 'p': p ^ 18 ^ (key >> 14 & 127)}
    if mode == 'E201' and g == 160:
        w = 7 if b < 2097152 else 14
        return {'g': (b >> w) ^ 100 ^ (key >> 21 & 127),
                'G': G ^ 110 ^ (key >> 7 & 127),
                'B': (b & ((1 << w) - 1)) ^ 122 ^ (key & 127),
                'p': p ^ 38 ^ (key >> 14 & 127)}
    if mode == 'Z250' and g == 13:
        w = 7 if p < 16384 else (14 if p < 2097152 else 21)
        return {'g': (p >> w) ^ 55 ^ (key >> 21 & 127),
                'G': G ^ 20 ^ (key & 127), 'B': b ^ 8 ^ (key >> 7 & 127),
                'p': (p & ((1 << w) - 1)) ^ 14 ^ (key >> 14 & 127)}
    if mode == 'Z250' and g == 38:
        w = 7 if b < 2097152 else 14
        return {'g': (b >> w) ^ 89 ^ (key >> 21 & 127),
                'G': G ^ 46 ^ (key & 127), 'p': p ^ 13 ^ (key >> 14 & 127),
                'B': (b & ((1 << w) - 1)) ^ 27 ^ (key >> 7 & 127)}
    if mode == 'Z95' and G == 103:
        w = 7 if g < 2097152 else 14
        return {'g': (g & ((1 << w) - 1)) ^ 91 ^ (key >> 7 & 127),
                'B': b ^ 9 ^ (key >> 14 & 127), 'G': (g >> w) ^ 35 ^ (key >> 21 & 127),
                'p': p ^ 78 ^ (key & 127)}
    if mode == 'Z95' and G == 196:
        w = 7 if b < 16384 else (14 if b < 2097152 else 21)
        return {'g': g ^ 122 ^ (key >> 7 & 127),
                'G': (b >> w) ^ 55 ^ (key >> 21 & 127),
                'B': (b & ((1 << w) - 1)) ^ 105 ^ (key >> 14 & 127), 'p': p ^ 17 ^ (key & 127)}
    if mode == 'Z240' and p == 29:
        w = 7 if b < 16384 else (14 if b < 2097152 else 21)
        return {'p': (b >> w) ^ 79 ^ (key >> 21 & 127),
                'G': G ^ 112 ^ (key & 127),
                'B': (b & ((1 << w) - 1)) ^ 52 ^ (key >> 14 & 127),
                'g': g ^ 52 ^ (key >> 7 & 127)}
    if mode == 'Z240' and p == 14:
        w = 7 if G < 2097152 else 14
        return {'p': (G >> w) ^ 99 ^ (key >> 21 & 127),
                'G': (G & ((1 << w) - 1)) ^ 94 ^ (key & 127),
                'B': b ^ 85 ^ (key >> 14 & 127), 'g': g ^ 25 ^ (key >> 7 & 127)}
    raise ValueError('unsupported point rewrite')


def main():
    base = Path('scratch/dv')
    source = (base/'nested-670-z240-4.json').read_bytes()
    arrays = json.loads(source)['arrays']
    earlier_raw = (base/'nested-670-z95-2.json').read_bytes()
    earlier = json.loads(earlier_raw)['arrays']
    cases = [(8,'E201',B), (56,'E201',B), (219,'E201',B),
             (22,'Z250',F), (31,'Z250',F), (43,'Z250',F), (53,'Z250',F), (61,'Z250',F),
             (70,'Z95',F), (78,'Z95',F), (82,'Z95',F), (98,'Z95',F),
             (106,'Z240',F), (115,'Z240',F), (118,'Z240',F), (124,'Z240',F), (129,'Z240',F),
             (136,'Z240',F), (143,'Z240',F), (147,'Z240',F), (156,'Z240',F), (158,'Z240',F), (164,'Z240',F),
             (166,'Z240',F), (171,'Z240',F), (174,'Z240',F), (186,'Z240',F),
             (194,'Z240',F), (196,'Z240',F), (211,'Z240',F), (212,'Z240',F)]
    rewrites = []
    for pc, mode, seed in cases:
        chosen = earlier if mode != 'Z240' else arrays
        before = {k:chosen[k][pc-1] for k in ('g','G','B','p')}
        rewrites.append({'pc':pc, 'mode':mode, 'before':before, 'after':point(mode,before,seed)})
    print(json.dumps({'_provenance':{'generator':'CodeRabbit','version':1},
                      'input_sha256':{'z240':hashlib.sha256(source).hexdigest(), 'z95':hashlib.sha256(earlier_raw).hexdigest()}, 'rewrites':rewrites,
                      'limitations':'Conditional on earlier block rewrites and seeds; rewrites alone do not establish reachability.'},indent=2))

if __name__ == '__main__': main()
