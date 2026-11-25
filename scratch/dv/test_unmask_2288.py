import unittest
from unmask_2288 import unmask


class Unmask2288Test(unittest.TestCase):
    def test_four_bytes_then_tail_and_reversibility(self):
        words = [0] * 256
        next_indices = [0] * 256
        words[0], next_indices[0] = 0x01020304, 7
        plain, end = unmask(bytes.fromhex('0001020304'), 42, 214, words, next_indices)
        self.assertEqual(plain.hex(), '2e282a2878')
        self.assertEqual(end, 86)
        self.assertEqual(unmask(plain, 42, 214, words, next_indices)[0], bytes.fromhex('0001020304'))

    def test_requires_valid_captured_tables(self):
        with self.assertRaises(ValueError):
            unmask(b'', 0, 0, [], [])
        with self.assertRaises(ValueError):
            unmask(b'', 256, 0, [0]*256, [0]*256)
        with self.assertRaises(ValueError):
            unmask(b'', 0, 0, [0]*255 + [-1], [0]*256)


if __name__ == '__main__': unittest.main()
