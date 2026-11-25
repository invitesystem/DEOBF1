#!/usr/bin/env python3
"""Propagate a small, source-derived subset of Z240 instructions as data.

Unknown calls, branches, and instructions stop the walk. This never runs Lua or
executes an extracted function; its starting state and path are hypotheses.
"""
import argparse
import hashlib
import json
from pathlib import Path

from decode_constants import decode
from extract_nested import extract_nested
from extract_records import extract
from patch_block import patch

FIELDS = ('g', 'G', 'B', 'p')


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def walk(arrays, data, offsets, pc, registers, f_seed, b_seed, previous_record_pcs=(), max_steps=1000,
         noop_registers=(), inert_slots=(), uncached_pcs=(), inert_lookup_pcs=(), returning_call_pcs=(),
         initial_constant_cache=(), call_clobbers=None):
    arrays = {name: list(arrays[name]) for name in FIELDS}
    data, offsets, registers = bytes(data), list(offsets), dict(registers)
    if pc < 1 or max_steps < 1 or not all(0 <= x <= 0xffffffff for x in (f_seed, b_seed)):
        raise ValueError('invalid initial pc, seeds or step limit')
    if any(not isinstance(k, int) or k < 0 or not isinstance(v, int) for k, v in registers.items()):
        raise ValueError('registers must map nonnegative indices to integers')
    previous_record_pcs = set(previous_record_pcs)
    noop_registers, inert_slots, uncached_pcs = set(noop_registers), set(inert_slots), set(uncached_pcs)
    inert_lookup_pcs = set(inert_lookup_pcs)
    returning_call_pcs = set(returning_call_pcs)
    call_clobbers = {} if call_clobbers is None else dict(call_clobbers)
    if not set(call_clobbers).issubset(returning_call_pcs):
        raise ValueError('call clobbers require an assumed returning call')
    if any(not isinstance(n, int) or n < 0 for n in noop_registers | inert_slots | uncached_pcs | inert_lookup_pcs | returning_call_pcs):
        raise ValueError('assumed registers and slots must be nonnegative integers')
    events = []
    seen = set()
    constants_cache = {(item['field'], item['pc']): item['value'] for item in initial_constant_cache}
    if len(constants_cache) != len(initial_constant_cache):
        raise ValueError('duplicate cached constant')
    nested_cache = {}

    def constant(kind, index, at=None):
        at = pc if at is None else at
        key = (kind, at)
        if key not in constants_cache:
            if at not in uncached_pcs:
                raise LookupError('unknown prior constant cache')
            value = decode(data, offsets, index)
            constants_cache[key] = value
            seen.clear()
        return constants_cache[key]

    reason = 'step_limit'
    for _ in range(max_steps):
        if any(pc > len(arrays[name]) for name in FIELDS) or pc < 1:
            reason = 'pc_out_of_bounds'
            break
        # A repeated abstract state is only a loop if no mutable data changed.
        state = (pc, f_seed, b_seed,
                 tuple((k, type(v).__name__, v) for k, v in sorted(registers.items())),
                 tuple(sorted(noop_registers)))
        if state in seen:
            reason = 'repeated_abstract_state'
            break
        seen.add(state)
        i = pc - 1
        g, G, B, op = (arrays[name][i] for name in FIELDS)
        event = {'pc': pc, 'opcode': op, 'g': g, 'G': G, 'B': B}
        next_pc = pc + 1
        destination = None
        new_noop = False
        if op == 69:
            destination = G
            registers[G] = B
        elif op == 129:
            destination = g
            registers.pop(g, None)  # A fresh table is not an integer fact.
        elif op == 143:
            registers[G], registers[G + 1] = g, B
            noop_registers.discard(G)
            noop_registers.discard(G + 1)
        elif op == 140:
            values = (registers.get(B), registers.get(G))
            noops = (B in noop_registers, G in noop_registers)
            for target, value, is_noop in zip((g, g + 1), values, noops):
                if value is None:
                    registers.pop(target, None)
                else:
                    registers[target] = value
                if is_noop:
                    noop_registers.add(target)
                else:
                    noop_registers.discard(target)
        elif op == 36:
            try:
                decoded = (constant('n', B), constant('L', g))
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if any(entry['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244) for entry in decoded):
                reason = 'unknown_constant'
                break
            for target, entry in zip((G, G + 1), decoded):
                value = entry.get('value')
                if isinstance(value, (int, bool)):
                    registers[target] = value
                else:
                    registers.pop(target, None)
                noop_registers.discard(target)
            event['constants'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 54:
            destination = B
            if G in registers:
                registers[B] = registers[G]
            else:
                registers.pop(B, None)
        elif op == 47:
            destination = B
            if f_seed is None:
                registers.pop(B, None)
            else:
                registers[B] = f_seed
        elif op == 134:
            destination = B
            if b_seed is None:
                registers.pop(B, None)
            else:
                registers[B] = b_seed
        elif op in (40, 92):
            source = g if op == 40 else G
            value = registers.get(source)
            if value is not None and (not integer(value) or not 0 <= value <= 0xffffffff):
                reason = 'invalid_seed'
                break
            if op == 40:
                f_seed = value
            else:
                b_seed = value
            if value is None:
                event['unknown_seed'] = 'f' if op == 40 else 'b'
        elif op == 171:
            index = registers.get(G)
            if not integer(index) or B + index < 0:
                reason = 'unknown_register_target'
                break
            destination = B + index
            if g in registers:
                registers[destination] = registers[g]
            else:
                registers.pop(destination, None)
            new_noop = g in noop_registers
            event['register_write'] = destination
        elif op == 108:
            destination = B
            value = registers.get(G)
            if integer(value):
                registers[B] = ((value & 0xffffffff) << g) & 0xffffffff if g < 32 else 0
            else:
                registers.pop(B, None)
        elif op == 12:
            destination = g
            if integer(registers.get(G)):
                registers[g] = (registers[G] & 0xffffffff) ^ B
            else:
                registers.pop(g, None)
        elif op == 43:
            try:
                left, right = constant('W', G), constant('L', g)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            values = (left.get('value'), right.get('value'))
            if any(not isinstance(v, int) or isinstance(v, bool) for v in values):
                reason = 'unknown_constant'
                break
            destination = B
            registers[B] = (values[0] ^ values[1]) & 0xffffffff
            event['constants'] = [left, right]
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op in (118, 146):
            try:
                decoded = constant('L', g)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            value = decoded.get('value')
            if not integer(value):
                reason = 'non_numeric_bit_operand'
                break
            destination = B if op == 118 else G
            source = G if op == 118 else B
            if integer(registers.get(source)):
                number = registers[source] & 0xffffffff
                registers[destination] = number & value if op == 118 else number ^ (value & 0xffffffff)
            else:
                registers.pop(destination, None)
            event['constant'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 58:
            destination = G
            if integer(registers.get(B)) and integer(registers.get(g)):
                registers[G] = (registers[B] | registers[g]) & 0xffffffff
            else:
                registers.pop(G, None)
        elif op == 199:
            destination = B
            if integer(registers.get(g)) and integer(registers.get(G)):
                registers[B] = (registers[g] ^ registers[G]) & 0xffffffff
            else:
                registers.pop(B, None)
        elif op in (18, 48):
            destination = G if op == 18 else g
            left = registers.get(B)
            right = g if op == 18 else registers.get(G)
            if integer(left) and integer(right) and abs(left) <= 2**53 and abs(right) <= 2**53 and abs(left + right) <= 2**53:
                registers[destination] = left + right
            else:
                registers.pop(destination, None)
        elif op == 61:
            destination = B
            left, right = registers.get(g), registers.get(G)
            if integer(left) and integer(right) and abs(left) <= 2**53 and abs(right) <= 2**53 and abs(left - right) <= 2**53:
                registers[B] = left - right
            else:
                registers.pop(B, None)
        elif op == 184:
            try:
                decoded = constant('n', B)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            value, left = decoded.get('value'), registers.get(G)
            if not integer(value):
                reason = 'non_numeric_arithmetic_operand'
                break
            destination = g
            if integer(left) and abs(left) <= 2**53 and abs(left - value) <= 2**53:
                registers[g] = left - value
            else:
                registers.pop(g, None)
            event['constant'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 166:
            destination = G
            if integer(registers.get(g)):
                registers[G] = (registers[g] * B) & 0xffffffff
            else:
                registers.pop(G, None)
        elif op == 102:
            destination = B
            value = registers.get(G)
            if integer(value) and abs(value) <= 2**53 and abs(value * g) <= 2**53:
                registers[B] = value * g
            else:
                registers.pop(B, None)
        elif op == 173:
            destination = G
            if integer(registers.get(g)):
                registers[G] = registers[g] % 0x100000000
            else:
                registers.pop(G, None)
        elif op == 70:
            if not integer(registers.get(g)):
                reason = 'unknown_indirect_target'
                break
            next_pc = registers[g] + 1
        elif op == 82:
            next_pc = G + 1
        elif op == 147:
            if not integer(registers.get(B)):
                reason = 'unknown_branch'
                break
            next_pc = pc + 1 if registers[B] <= G else g + 1
        elif op == 168:
            destination = g
            if B in registers:
                registers[g] = integer(registers[B]) and registers[B] == G
            else:
                registers.pop(g, None)
        elif op in (89, 115):
            if B not in registers:
                reason = 'unknown_branch'
                break
            truthy = registers[B] is not False
            target = (G if truthy else g) if op == 89 else (g if truthy else G)
            next_pc = target + 1
        elif op == 154:
            pass  # The source's P < 155 branch is empty for P == 154.
        elif op == 26:
            try:
                decoded = constant('L', g)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if decoded['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            destination = B
            value = decoded.get('value')
            if isinstance(value, (int, bool)):
                registers[B] = value
            else:
                registers.pop(B, None)
            event['constant'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op in (4, 152, 196):
            if pc not in inert_lookup_pcs:
                reason = 'unverified_object_lookup'
                break
            try:
                decoded = constant('L' if op == 4 else 'n', g if op == 4 else B)
                if op == 152:
                    second = constant('L', g)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if decoded['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            if op == 152 and second['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            destination = G
            registers.pop(G, None)
            event['constant'] = decoded
            if op == 152:
                event['second_constant'] = second
            event['assumption'] = 'object lookup succeeds without mutating VM registers'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op in (23, 156):
            if pc not in inert_lookup_pcs:
                reason = 'unverified_table_write'
                break
            try:
                key = constant('n' if op == 23 else 'L', B if op == 23 else g)
                value = constant('W', G)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if key['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244) or value['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            scalar_key = key.get('value', key.get('utf8'))
            if op == 23 and isinstance(scalar_key, int) and not isinstance(scalar_key, bool):
                inert_slots.discard(scalar_key)
            event['constant_key'] = key
            event['assumption'] = 'table write succeeds without mutating VM registers'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 132:
            if pc not in inert_lookup_pcs:
                reason = 'unverified_table_write'
                break
            event['assumption'] = 'table move succeeds without mutating VM registers'
        elif op in (57, 126):
            if pc not in inert_lookup_pcs:
                reason = 'unverified_upvalue_close'
                break
            event['assumption'] = 'closing upvalues does not mutate VM registers'
        elif op == 116:
            if pc not in inert_lookup_pcs:
                reason = 'unverified_table_write'
                break
            if any(pc + 2 > len(arrays[name]) for name in FIELDS):
                reason = 'pc_out_of_bounds'
                break
            try:
                pairs = [(constant('L', arrays['g'][i + n], pc + n),
                          constant('W', arrays['G'][i + n], pc + n)) for n in range(3)]
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if any(entry['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244) for pair in pairs for entry in pair):
                reason = 'unknown_constant'
                break
            event['assumption'] = 'three table writes succeed without mutating VM registers'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
            event['constant_keys'] = [pair[0] for pair in pairs]
            next_pc = pc + 3
        elif op in (19, 49, 190):
            if pc not in inert_lookup_pcs:
                reason = 'unverified_table_write'
                break
            count = 2 if op == 190 else 1
            if any(pc + count - 1 > len(arrays[name]) for name in FIELDS):
                reason = 'pc_out_of_bounds'
                break
            try:
                if op == 49:
                    decoded = [constant('n', B)]
                elif op == 19:
                    decoded = [constant('L', g)]
                else:
                    decoded = [entry for n in range(2) for entry in
                               (constant('L', arrays['g'][i + n], pc + n),
                                constant('W', arrays['G'][i + n], pc + n))]
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if any(entry['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244) for entry in decoded):
                reason = 'unknown_constant'
                break
            event['assumption'] = 'table writes succeed without mutating VM registers'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
            event['constants'] = decoded
            next_pc = pc + count
        elif op == 155:
            if pc not in inert_lookup_pcs:
                reason = 'unverified_table_write'
                break
            try:
                decoded = constant('W', G)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if decoded['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            event['constant_key'] = decoded
            event['assumption'] = 'object write succeeds without mutating VM registers; external effects are unknown'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 123:
            if pc not in inert_lookup_pcs:
                reason = 'unverified_closure_creation'
                break
            try:
                captures = constant('n', B)
                if pc not in nested_cache:
                    if pc not in uncached_pcs:
                        raise LookupError('unknown prior function cache')
                    nested_cache[pc] = extract_nested(data, offsets, G, 186)
                    seen.clear()
                nested = nested_cache[pc]
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_closure_record'
                break
            if captures['tag'] != 170 or captures.get('remaining_hex'):
                reason = 'unknown_closure_capture'
                break
            if 'tables' not in nested:
                reason = 'unsupported_native_factory'
                break
            destination = g
            registers.pop(g, None)
            table = nested['tables']
            # This exact entry sequence copies arguments into fresh registers
            # and returns; with no captures it cannot change the parent frame.
            new_noop = (not captures['captures'] and table['mode'] == 201 and
                        table['slot'] == 16374 and table['prefixes'][0] == 1 and
                        table['arrays']['g'][:2] == [58, 63] and
                        len(table['arrays']['G']) > 0 and len(table['arrays']['B']) > 0 and
                        table['arrays']['G'][0] == 2 and table['arrays']['B'][0] == 9)
            event['closure'] = {'index': G, 'sha256': nested['decoded_sha256'],
                                'captures': captures['captures'], 'effect_free': new_noop}
            event['assumption'] = 'closure construction succeeds without mutating VM registers'
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 99:
            if B not in inert_slots:
                reason = 'unverified_table_lookup'
                break
            destination = g
            registers.pop(g, None)
            event['assumption'] = f'd[{B}] lookup is inert'
        elif op == 125:
            if g not in noop_registers:
                reason = 'unknown_call'
                break
            try:
                decoded = constant('n', B)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_call_argument'
                break
            if decoded['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_call_argument'
                break
            event['assumption'] = f'u[{g}] is an effect-free closure'
            event['constant'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
        elif op == 7:
            reason = 'unknown_call'
            break
        elif op in (91, 203):
            callee = G if op == 91 else B
            if callee not in noop_registers and pc not in returning_call_pcs:
                reason = 'unknown_call'
                break
            clobbered = call_clobbers.get(pc, ())
            for target in clobbered:
                registers.pop(target, None)
                noop_registers.discard(target)
            event['assumption'] = (f'u[{callee}] is an effect-free closure' if callee in noop_registers
                                   else 'call returns and changes only the listed frame registers; external effects are unknown')
            if clobbered: event['clobbered_registers'] = list(clobbered)
        elif op in (98, 194):
            if pc not in returning_call_pcs:
                reason = 'unknown_call'
                break
            destination = g
            registers.pop(g, None)
            event['assumption'] = 'call returns without mutating VM registers; result is unknown'
        elif op == 112:
            if pc not in returning_call_pcs:
                reason = 'unknown_call'
                break
            if g > 100000:
                reason = 'result_range_too_large'
                break
            for target in range(G, G + g):
                registers.pop(target, None)
                noop_registers.discard(target)
            event['assumption'] = 'call returns without mutating VM registers; results are unknown'
        elif op == 164:
            if pc not in returning_call_pcs and g not in noop_registers:
                reason = 'unknown_call'
                break
            try:
                left, right = constant('n', B), constant('W', G)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_call_argument'
                break
            if any(item['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244) for item in (left, right)):
                reason = 'unknown_call_argument'
                break
            clobbered = call_clobbers.get(pc, ())
            for target in clobbered:
                registers.pop(target, None)
                noop_registers.discard(target)
            event['constants'] = [left, right]
            event['clobbered_registers'] = list(clobbered)
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
            event['assumption'] = 'call returns and changes only the listed frame registers; external effects are unknown'
        elif op in (1, 149):
            if B not in noop_registers and pc not in returning_call_pcs:
                reason = 'unknown_call'
                break
            try:
                decoded = constant('W', G)
            except LookupError:
                reason = 'unknown_constant_cache'
                break
            except (ValueError, IndexError):
                reason = 'unknown_constant'
                break
            if decoded['tag'] not in (31, 70, 104, 113, 167, 169, 195, 218, 237, 242, 244):
                reason = 'unknown_constant'
                break
            if op == 149:
                destination = g
                registers.pop(g, None)
            event['constant'] = decoded
            event['cache_assumption'] = 'cached from initial state or assumed empty before first access'
            event['assumption'] = 'call returns without mutating VM registers; result is unknown'
        elif op in (0, 93, 177):
            seed = 0 if op == 93 else (b_seed if op == 0 else f_seed)
            if seed is None:
                reason = 'unknown_block_rewrite_seed'
                break
            result = patch(arrays, pc, seed, 'Z240')
            arrays = result['arrays']
            event['rewrite'] = {'start': result['start'], 'count': result['count'],
                                'initial_state': result['initial_state']}
            seen.clear()
        elif op in (14, 29):
            if f_seed is None:
                reason = 'unknown_self_rewrite_seed'
                break
            key = f_seed ^ ((f_seed >> 14) & 262143) ^ ((f_seed >> 28) & 15)
            if op == 29:
                width = 7 if B < 16384 else (14 if B < 2097152 else 21)
                arrays['p'][i] = (B >> width) ^ 79 ^ ((key >> 21) & 127)
                arrays['G'][i] = G ^ 112 ^ (key & 127)
                arrays['B'][i] = (B & ((1 << width) - 1)) ^ 52 ^ ((key >> 14) & 127)
                arrays['g'][i] = g ^ 52 ^ ((key >> 7) & 127)
            else:
                width = 7 if G < 2097152 else 14
                arrays['p'][i] = (G >> width) ^ 99 ^ ((key >> 21) & 127)
                arrays['G'][i] = (G & ((1 << width) - 1)) ^ 94 ^ (key & 127)
                arrays['B'][i] = B ^ 85 ^ ((key >> 14) & 127)
                arrays['g'][i] = g ^ 25 ^ ((key >> 7) & 127)
            event['rewrite'] = {name: arrays[name][i] for name in FIELDS}
            next_pc = pc
            seen.clear()
        elif op == 120:
            if pc in previous_record_pcs:
                reason = 'previous_record_mutation_requires_reconciliation'
                break
            # Z240/120 uses its direct byte key, never either seed.
            data, offsets, records = extract(data, offsets, arrays, [pc], 0, 0, 'Z240')
            event['record'] = {k: records[0][k] for k in ('index', 'key', 'offset', 'start', 'length')}
            for name, value in zip(FIELDS, (23, 157, 228, 154)):
                arrays[name][i] = value
            previous_record_pcs.add(pc)
            seen.clear()
        else:
            reason = 'unsupported_opcode'
            break
        if destination is not None:
            noop_registers.discard(destination)
            if new_noop:
                noop_registers.add(destination)
        event['next_pc'] = next_pc
        events.append(event)
        pc = next_pc
    return {'pc': pc, 'registers': registers, 'f_seed': f_seed, 'b_seed': b_seed,
            'stop_reason': reason, 'events': events, 'arrays': arrays, 'noop_registers': sorted(noop_registers),
            'constant_cache': [{'field': field, 'pc': at, 'value': value}
                               for (field, at), value in sorted(constants_cache.items())],
            'updated_offsets': offsets, 'data': data}


def parse_register(text):
    index, value = text.split('=', 1)
    return int(index), int(value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arrays', type=Path, required=True)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--previous-records', type=Path, action='append', default=[])
    parser.add_argument('--pc', type=int, required=True)
    parser.add_argument('--register', type=parse_register, action='append', default=[])
    parser.add_argument('--f-seed', type=int, required=True)
    parser.add_argument('--b-seed', type=int, required=True)
    parser.add_argument('--max-steps', type=int, default=1000)
    parser.add_argument('--assume-noop-register', type=int, action='append', default=[])
    parser.add_argument('--assume-inert-slot', type=int, action='append', default=[])
    parser.add_argument('--assume-uncached-pc', type=int, action='append', default=[])
    parser.add_argument('--assume-inert-lookup-pc', type=int, action='append', default=[])
    parser.add_argument('--assume-returning-call-pc', type=int, action='append', default=[])
    parser.add_argument('--output-buffer', type=Path, required=True)
    args = parser.parse_args()
    sources = {'arrays': args.arrays.read_bytes(), 'buffer': args.buffer.read_bytes(),
               'table': args.table.read_bytes()}
    table = json.loads(sources['table'])
    offsets = table.get('updated_offsets', table.get('values'))
    if offsets is None:
        raise ValueError('table has neither values nor updated_offsets')
    previous = set()
    for path in args.previous_records:
        raw = path.read_bytes()
        sources[str(path)] = raw
        previous.update(record['pc'] for record in json.loads(raw).get('records', []))
    result = walk(json.loads(sources['arrays'])['arrays'], sources['buffer'], offsets,
                  args.pc, dict(args.register), args.f_seed, args.b_seed, previous, args.max_steps,
                  args.assume_noop_register, args.assume_inert_slot, args.assume_uncached_pc,
                  args.assume_inert_lookup_pc, args.assume_returning_call_pc)
    data = result.pop('data')
    args.output_buffer.write_bytes(data)
    result.update({'_provenance': {'generator': 'CodeRabbit', 'version': 1},
                   'input_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
                   'output_sha256': hashlib.sha256(data).hexdigest(),
                   'initial_assumptions': {'pc': args.pc, 'registers': dict(args.register),
                       'f_seed': args.f_seed, 'b_seed': args.b_seed,
                       'effect_free_registers': args.assume_noop_register,
                       'inert_slots': args.assume_inert_slot, 'uncached_pcs': args.assume_uncached_pc,
                       'inert_lookup_pcs': args.assume_inert_lookup_pc,
                       'returning_call_pcs': args.assume_returning_call_pc,
                       'max_steps': args.max_steps},
                   'limitations': 'Only supported Z240 transfers are propagated. Input state, prior mutations and explicitly supplied cache/call/lookup assumptions are hypotheses; unknown effects, branches and opcodes stop the analysis.'})
    print(json.dumps(result, indent=2))
