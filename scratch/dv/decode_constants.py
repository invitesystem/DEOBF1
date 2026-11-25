#!/usr/bin/env python3
"""Decode selected lazy constants using the source's tag-specific data formulas."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from init_table import read_value


def table_word(index: int) -> tuple[int, int]:
    word = 0
    for shift in (0, 8, 16, 24):
        index = (173 * index + 3) % 256
        word |= index << shift
    return word, index


def decode(data: bytes, offsets: list[int], index: int) -> dict:
    if not 1 <= index <= len(offsets):
        raise ValueError('constant index outside table')
    pos = offsets[index - 1]
    if not 0 <= pos < len(data):
        raise ValueError('constant offset outside buffer')
    tag = data[pos]
    if tag in (113, 170):
        length, start, _ = read_value(data, pos + 1)
        if start + length > len(data):
            raise ValueError('constant data outside buffer')
        salt = 69 if tag == 113 else 253
        state = (index + salt) % 256
        value = bytearray()
        for at in range(start, start + length - length % 4, 4):
            word, state = table_word(state)
            value.extend((int.from_bytes(data[at:at + 4], 'little') ^ word ^ (salt * 0x01010101)).to_bytes(4, 'little'))
        for at in range(start + length - length % 4, start + length):
            state = (173 * state + 3) % 256
            value.append(data[at] ^ state ^ salt)
        if tag == 170:
            count, cursor, _ = read_value(value, 0)
            captures = []
            for _ in range(count):
                encoded, cursor, _ = read_value(value, cursor)
                kind, capture_index = encoded & 3, encoded >> 2
                if kind == 0:
                    size, cursor, _ = read_value(value, cursor)
                    size += 1
                else:
                    size = 9644
                captures.append([kind, size, capture_index])
            return {'index': index, 'offset': pos, 'tag': tag, 'length': length,
                    'hex': bytes(value).hex(), 'captures': captures,
                    'remaining_hex': bytes(value[cursor:]).hex()}
        try:
            decoded = bytes(value).decode('utf-8')
        except UnicodeDecodeError:
            decoded = None
        return {'index': index, 'offset': pos, 'tag': tag, 'length': length,
                'hex': bytes(value).hex(), 'utf8': decoded}
    if tag in (70, 237):
        if pos + 5 > len(data):
            raise ValueError('constant data outside buffer')
        word, _ = table_word((index + (128 if tag == 70 else 47)) % 256)
        bits = int.from_bytes(data[pos + 1:pos + 5], 'little') ^ word ^ (2155905152 if tag == 70 else 791621423)
        value = struct.unpack('<i', bits.to_bytes(4, 'little'))[0] if tag == 70 else bits
        return {'index': index, 'offset': pos, 'tag': tag, 'value': value}
    if tag in (28, 167, 203):
        # mw reads one float32, a Vector2 or a Vector3 from successive XOR words.
        salt, count = {28: (41, 2), 167: (200, 1), 203: (55, 3)}[tag]
        if pos + 1 + count * 4 > len(data):
            raise ValueError('constant data outside buffer')
        state = (index + salt) % 256
        values, bits_hex, classifications = [], [], []
        for n in range(count):
            word, state = table_word(state)
            bits = (int.from_bytes(data[pos + 1 + 4*n:pos + 5 + 4*n], 'little') ^
                    word ^ (salt * 0x01010101)).to_bytes(4, 'little')
            value = struct.unpack('<f', bits)[0]
            values.append(value if math.isfinite(value) else None)
            bits_hex.append(bits.hex())
            classifications.append('finite' if math.isfinite(value) else ('nan' if math.isnan(value) else ('-inf' if value < 0 else 'inf')))
        if count == 1:
            return {'index': index, 'offset': pos, 'tag': tag, 'value': values[0],
                    'bits_hex': bits_hex[0], 'classification': classifications[0]}
        return {'index': index, 'offset': pos, 'tag': tag,
                'kind': 'Vector2' if count == 2 else 'Vector3', 'components': values,
                'bits_hex': bits_hex, 'classifications': classifications}
    if tag in (195, 244):
        if pos + 3 > len(data):
            raise ValueError('constant data outside buffer')
        salt = 88 if tag == 195 else 16
        state = (index + salt) % 256
        raw = bytearray()
        for at in range(pos + 1, pos + 3):
            state = (173 * state + 3) % 256
            raw.append(data[at] ^ state ^ salt)
        return {'index': index, 'offset': pos, 'tag': tag,
                'value': int.from_bytes(raw, 'little', signed=tag == 195)}
    if tag == 104:
        # mw states 24 -> 52 -> 91 -> 107 -> 48 -> 59 -> 132/13.
        if pos + 9 > len(data):
            raise ValueError('constant data outside buffer')
        word1, state = table_word((index + 237) % 256)
        word2, _ = table_word(state)
        low = int.from_bytes(data[pos + 1:pos + 5], 'little') ^ word1 ^ 0xedededed
        high = int.from_bytes(data[pos + 5:pos + 9], 'little') ^ word2 ^ 0xedededed
        signed_high = high - (1 << 32) if high >= (1 << 31) else high
        # Luau numbers are doubles; round the mathematical integer as a double.
        value = int(float(low + signed_high * (1 << 32)))
        return {'index': index, 'offset': pos, 'tag': tag, 'value': value,
                'low_word': low, 'high_word': high}
    if tag == 218:
        if pos + 9 > len(data):
            raise ValueError('constant data outside buffer')
        word1, state = table_word((index + 23) % 256)
        word2, _ = table_word(state)
        masks = (word1, word2)
        bits = b''.join((int.from_bytes(data[pos + 1 + n * 4:pos + 5 + n * 4], 'little') ^
                         masks[n] ^ 0x17171717).to_bytes(4, 'little') for n in range(2))
        value = struct.unpack('<d', bits)[0]
        return {'index': index, 'offset': pos, 'tag': tag, 'bits_hex': bits.hex(),
                'value': value if math.isfinite(value) else None,
                'classification': 'finite' if math.isfinite(value) else ('nan' if math.isnan(value) else ('-inf' if value < 0 else 'inf'))}
    if tag in (31, 169, 242):
        if pos + 2 > len(data):
            raise ValueError('constant data outside buffer')
        salt = {31: 46, 169: 141, 242: 244}[tag]
        key = (173 * ((index + salt) % 256) + 3) % 256
        value = data[pos + 1] ^ salt ^ key
        if tag == 31:
            value = value != 255
        elif tag == 169:
            value = -value
        return {'index': index, 'offset': pos, 'tag': tag, 'value': value}
    raise ValueError(f'unsupported constant tag {tag} at index {index}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--buffer', type=Path, required=True)
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--indices', required=True, help='comma-separated, source-derived indices')
    args = parser.parse_args()
    buffer = args.buffer.read_bytes()
    table_raw = args.table.read_bytes()
    table = json.loads(table_raw)
    offsets = table.get('updated_offsets', table.get('values'))
    values = [decode(buffer, offsets, int(value)) for value in args.indices.split(',')]
    print(json.dumps({'_provenance': {'generator': 'CodeRabbit', 'version': 1},
                      'input_sha256': {'buffer': hashlib.sha256(buffer).hexdigest(),
                                       'table': hashlib.sha256(table_raw).hexdigest()},
                      'constants': values,
                      'limitations': 'Only tags 28, 31, 70, 104, 113, 167, 169, 170, 195, 203, 218, 237, 242 and 244 are implemented; the indices and input mutations are external static hypotheses.'}, indent=2, ensure_ascii=False))
