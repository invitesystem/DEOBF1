import unittest
from extract_records import extract


class RecordExtractionTest(unittest.TestCase):
    def test_known_data_and_pointer_rewrite(self):
        data = bytes([0, 3, 1, 2, 3])
        arrays = {'g': [53], 'G': [18], 'B': [1]}
        result, offsets, records = extract(data, [236682589], arrays, [1], 0, 0)
        self.assertEqual(result, bytes([0, 3, 19, 16, 17]))
        self.assertEqual(offsets, [0])
        self.assertEqual(records[0]['result_hex'], '131011')
        self.assertEqual(data, bytes([0, 3, 1, 2, 3]))

    def test_invalid_opcode_and_truncated_record(self):
        with self.assertRaises(ValueError):
            extract(b'', [0], {'g': [1], 'G': [0], 'B': [1]}, [1], 0, 0)
        with self.assertRaises(ValueError):
            extract(bytes([0, 3, 1]), [236682589], {'g': [53], 'G': [18], 'B': [1]}, [1], 0, 0)

    def test_z250_swaps_index_and_key_fields(self):
        arrays = {'g': [56], 'G': [1], 'B': [18]}
        result, offsets, _ = extract(bytes([0, 3, 1, 2, 3]), [236682589], arrays, [1], 0, 0, 'Z250')
        self.assertEqual(result, bytes([0, 3, 19, 16, 17]))
        self.assertEqual(offsets, [0])

    def test_z95_seeded_and_direct_key(self):
        for opcode in (14, 24):
            arrays = {'g': [18], 'G': [opcode], 'B': [18], 'p': [1]}
            result, _, _ = extract(bytes([0, 3, 1, 2, 3]), [236682589], arrays, [1], 0, 0, 'Z95')
            self.assertEqual(result, bytes([0, 3, 19, 16, 17]))

    def test_z240_direct_key_and_opcode_field(self):
        arrays = {'g': [1], 'G': [18], 'B': [0], 'p': [120]}
        result, offsets, _ = extract(bytes([0, 3, 1, 2, 3]), [236682589], arrays, [1], 0, 0, 'Z240')
        self.assertEqual(result, bytes([0, 3, 19, 16, 17]))
        self.assertEqual(offsets, [0])

    def test_e201_direct_key_and_index(self):
        arrays = {'g': [172], 'G': [0], 'B': [18], 'p': [1]}
        result, offsets, _ = extract(bytes([0, 3, 1, 2, 3]), [236682589], arrays, [1], 0, 0)
        self.assertEqual(result, bytes([0, 3, 19, 16, 17]))
        self.assertEqual(offsets, [0])
        with self.assertRaises(ValueError):
            extract(bytes([0, 3, 1, 2, 3]), [236682589], {'g': [172], 'G': [0], 'B': [18]}, [1], 0, 0)


if __name__ == '__main__':
    unittest.main()
