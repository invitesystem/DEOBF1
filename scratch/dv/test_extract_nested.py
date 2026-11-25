import hashlib
from pathlib import Path
import unittest

from extract_nested import extract_nested
from nested_tables import extract
from unmask_record import unmask


class ExtractNestedTest(unittest.TestCase):
    def test_known_nested_record(self):
        plain = (Path(__file__).parent / 'nested-720.bin').read_bytes()
        seed, index = 186, 1
        # 856 is encoded by the source's two-byte length format.
        encrypted = unmask(plain, seed, (seed + index) % 256)
        record = bytes.fromhex('b88658') + encrypted
        result = extract_nested(record, [0], index, seed)
        self.assertEqual(result['decoded_sha256'], hashlib.sha256(plain).hexdigest())
        self.assertEqual(result['tables'], extract(plain))

    def test_invalid_records(self):
        for data, offsets, index, seed in (
            (b'\x00', [0], 1, 186),
            (b'\xb8\x05x', [0], 1, 186),
            (b'\xb8', [4], 1, 186),
            (b'\xb8', [0], 0, 186),
            (b'\xb8', [0], 1, 256),
        ):
            with self.assertRaises(ValueError):
                extract_nested(data, offsets, index, seed)

    def test_direct_native_factory_header(self):
        plain = bytes.fromhex('020100b77c020132')
        encrypted = unmask(plain, 186, 187)
        result = extract_nested(bytes.fromhex('b808') + encrypted, [0], 1, 186)
        self.assertEqual(result['native_factory']['selector'], 7164)
        self.assertEqual(result['native_factory']['remaining_hex'], '020132')
        self.assertNotIn('tables', result)


if __name__ == '__main__':
    unittest.main()
