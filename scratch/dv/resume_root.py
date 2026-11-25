#!/usr/bin/env python3
# coderabbit-ai-generated:v1
"""Explore conditional root continuations after pcall, without executing Lua."""
import hashlib
import json
from pathlib import Path

from static_walk import walk

base = Path('scratch/dv')
raw = (base / 'z240-backtrace.json').read_bytes()
buffer = (base / 'z240-backtrace.bin').read_bytes()
snapshot = json.loads(raw)
if snapshot['pc'] != 358 or snapshot['stop_reason'] != 'unknown_call':
    raise ValueError('unexpected source snapshot')
source_regs = {int(k): v for k, v in snapshot['registers'].items()}
# These are all captured registers of record 436, plus results of pcall.
invalidated = {3, 4, 98, 214, 86, 132, 135, 134, 212, 213, 123, 111, 125, 126, 120, 121}
prior = {event['pc'] for event in snapshot['events'] if 'record' in event}
branches = []
for status in (False, True):
    regs = {k:v for k,v in source_regs.items() if k not in invalidated}
    # The initialized table maps false->true and true->false; pc 360 negates
    # the pcall status before pc 361. This assumes that table is unchanged.
    regs[3] = status
    result = walk(snapshot['arrays'], buffer, snapshot['updated_offsets'], 362, regs,
                  snapshot['f_seed'], snapshot['b_seed'], prior, 1000,
                  noop_registers=snapshot['noop_registers'], inert_lookup_pcs=(221, 742), uncached_pcs=(830, 1163),
                  initial_constant_cache=snapshot['constant_cache'], returning_call_pcs=(830, 1164),
                  call_clobbers={830: (120, 121), 1164: (120, 121)})
    if status and result['pc'] == 7175:
        children = []
        for returned_truth in (False, True):
            child_regs = dict(result['registers'])
            # 7175 negates the unknown value in u98; the boolean map negates it again.
            child_regs[3] = returned_truth
            child_regs.pop(98, None)
            child = walk(result['arrays'], result['data'], result['updated_offsets'], 7177,
                         child_regs, result['f_seed'], result['b_seed'], prior, 1000,
                         noop_registers=result['noop_registers'],
                         initial_constant_cache=result['constant_cache'], uncached_pcs=(5395, 7621),
                         returning_call_pcs=(5395,), call_clobbers={5395:(120, 121)})
            child.pop('data'); child.pop('arrays')
            child['returned_value_truthy'] = returned_truth
            children.append(child)
        result['return_truth_branches'] = children
        result['stop_reason'] = 'split_on_unknown_return_truthiness'
    result.pop('data')
    result.pop('arrays')
    result['pcall_status'] = status
    result['limitations'] = ('Conditional on pcall returning and the shared buffer, instruction arrays, '
                             'constant caches, and boolean lookup table remaining unchanged. '
                             'The writers and closure 727 retain their source-derived identities, and unrelated frame registers are unchanged. The 830, 5395, and 7621 constant caches are assumed empty. The pc 830/5395 calls assume the writer closure 720 returns and affects captured registers 120/121 only.  The closure 436 return value is unknown; nested continuations separately assume its truthiness. The pc 1163 constant cache is assumed initially empty. At pc 1164, the conditional summary of closure 727 writes captures 120/121. Captured registers and the second pcall result are unknown; closing upvalues at 221/742 is assumed to preserve frame registers.')
    branches.append(result)
print(json.dumps({'_provenance':{'generator':'CodeRabbit','version':1},
                  'input_sha256':{'snapshot':hashlib.sha256(raw).hexdigest(),
                                  'buffer':hashlib.sha256(buffer).hexdigest()},
                  'branches':branches}, indent=2))
