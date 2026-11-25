#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Propagate known schedule words from a conditional Z240 entry as data."""
import hashlib
import json
from pathlib import Path
from static_walk import walk

base = Path('scratch/dv')
raw = (base/'z240-backtrace.json').read_bytes()
data = (base/'z240-backtrace.bin').read_bytes()
snapshot = json.loads(raw)
result = walk(snapshot['arrays'], data, snapshot['updated_offsets'], 4723, {},
              snapshot['f_seed'], snapshot['b_seed'], max_steps=1000)
result.pop('data'); result.pop('arrays')
result.update({'_provenance':{'generator':'CodeRabbit','version':1},
               'input_sha256':{'snapshot':hashlib.sha256(raw).hexdigest(),
                               'buffer':hashlib.sha256(data).hexdigest()},
               'initial_assumptions':{'pc':4723, 'registers_known':{},
                                      'f_seed':snapshot['f_seed'], 'b_seed':snapshot['b_seed']},
               'limitations':'Starting PC, current instruction arrays and seeds are conditional; unknown u172 makes a later self-rewrite seed unknown. The path is not proven reachable.'})
print(json.dumps(result, indent=2))
