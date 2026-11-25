import unittest
from patch_block import patch


class PatchBlockTest(unittest.TestCase):
    def test_first_record_and_opcode_replacement(self):
        arrays = {'g': [59, 175], 'G': [309453703, 11585],
                  'B': [1, 124], 'p': [1, 65]}
        result = patch(arrays, 1, 2044757032)
        self.assertEqual(result['initial_state'], 194078636)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [173, 11640, 119, 89])
        self.assertEqual(result['arrays']['g'][0], 27)
        self.assertEqual(arrays['g'][0], 59)

    def test_bad_ranges_and_opcodes(self):
        arrays = {'g': [59], 'G': [0], 'B': [1], 'p': [1]}
        with self.assertRaises(ValueError):
            patch(arrays, 1, 0)

    def test_opcode_119_with_second_seed(self):
        arrays = {'g': [119, 109], 'G': [353183648, 118],
                  'B': [1, 115], 'p': [1, 5]}
        result = patch(arrays, 1, 3891349218)
        self.assertEqual(result['initial_state'], 318529861)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [116, 25, 16, 54])
        arrays['g'][0] = 1
        with self.assertRaises(ValueError):
            patch(arrays, 1, 0)

    def test_opcode_83_swaps_operand_fields(self):
        arrays = {'g': [83, 37], 'G': [1, 80],
                  'B': [462504977, 215], 'p': [1, 51]}
        result = patch(arrays, 1, 3891349218, 'Z250')
        self.assertEqual(result['initial_state'], 476054260)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [2, 80, 145, 74])
        self.assertEqual(result['arrays']['g'][0], 164)
        with self.assertRaises(ValueError):
            patch(arrays, 1, 3891349218, 'E201')

    def test_opcode_35_with_first_seed(self):
        arrays = {'g': [35, 78], 'G': [1, 158],
                  'B': [206601448, 5501], 'p': [1, 97]}
        result = patch(arrays, 1, 2044757032, 'Z250')
        self.assertEqual(result['initial_state'], 363919555)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [0, 153, 5478, 69])

    def test_z95_rewrites_opcode_in_g_field(self):
        arrays = {'g': [201003383, 8524], 'G': [75, 42],
                  'B': [1, 101], 'p': [1, 193]}
        result = patch(arrays, 1, 3891349218, 'Z95')
        self.assertEqual(result['initial_state'], 202004370)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [8460, 93, 87, 147])
        self.assertEqual(result['arrays']['G'][0], 179)

    def test_z240_direct_seed_and_field_order(self):
        arrays = {'g': [1, 0], 'G': [1, 0], 'B': [1, 0], 'p': [93, 0]}
        result = patch(arrays, 1, 0, 'Z240')
        self.assertEqual(result['initial_state'], 1)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                         [64, 0, 0, 64])
        self.assertEqual(result['arrays']['p'][0], 154)

    def test_z240_seeded_block_variants(self):
        for opcode in (0, 177):
            arrays = {'g': [1, 0], 'G': [1, 0], 'B': [1, 0], 'p': [opcode, 0]}
            result = patch(arrays, 1, 0, 'Z240')
            self.assertEqual(result['initial_state'], 1)
            self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')],
                             [64, 0, 0, 64])
            self.assertEqual(result['arrays']['p'][0], 154)

    def test_direct_seed_for_z95_and_z250(self):
        for mode, arrays, expected, opcode_field, replacement in (
            ('Z95', {'g': [1, 0], 'G': [121, 0], 'B': [1, 0], 'p': [1, 0]},
             [64, 64, 0, 0], 'G', 179),
            ('Z250', {'g': [49, 0], 'G': [1, 0], 'B': [1, 0], 'p': [1, 0]},
             [64, 0, 64, 0], 'g', 164),
        ):
            result = patch(arrays, 1, 0, mode)
            self.assertEqual(result['initial_state'], 1)
            self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')], expected)
            self.assertEqual(result['arrays'][opcode_field][0], replacement)

    def test_e201_direct_seed_variant(self):
        arrays = {'g': [170, 0], 'G': [1, 0], 'B': [1, 0], 'p': [1, 0]}
        result = patch(arrays, 1, 123, 'E201')
        self.assertEqual(result['initial_state'], 1)
        self.assertEqual([result['arrays'][name][1] for name in ('g', 'G', 'B', 'p')], [64, 64, 0, 0])
        self.assertEqual(result['arrays']['g'][0], 27)


if __name__ == '__main__':
    unittest.main()
