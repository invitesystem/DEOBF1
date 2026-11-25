import unittest

from walk_nested188 import Opaque, UncertainTable, lua_equal, point, walk


class Nested188WalkTest(unittest.TestCase):
    def test_lua_boolean_is_not_number(self):
        self.assertFalse(lua_equal(False, 0))
        self.assertFalse(lua_equal(True, 1))
        self.assertTrue(lua_equal(1, 1.0))

    def test_known_point_rewrites(self):
        arrays = {'g': [190813629, 41], 'G': [196, 196], 'B': [6449, 8728], 'p': [74, 79]}
        self.assertEqual(point(arrays, 1, 1263948163), {'g': 190813630, 'G': 95, 'B': 5, 'p': 5})
        self.assertEqual(point(arrays, 2, 1263948163), {'g': 42, 'G': 41, 'B': 44, 'p': 0})

    def test_table_write_and_unknown_opcode_stop(self):
        target = {1: 9}
        arrays = {'g': [2, 0], 'G': [88, 255], 'B': [1, 0], 'p': [3, 0]}
        result = walk(arrays, b'', [], {1:target, 2:1, 3:7}, 1, 0, 0)
        self.assertEqual(target[1], 7)
        self.assertEqual(result['events'][0]['table_write'], {'key':1, 'previous':9, 'value':7})
        self.assertEqual((result['pc'], result['stop_reason']), (2, 'unsupported_opcode'))

    def test_unknown_context_field_stops(self):
        arrays = {'g': [2], 'G': [136], 'B': [30], 'p': [3]}
        result = walk(arrays, b'', [], {30: UncertainTable({4: Opaque('buffer')})}, 1, 0, 0)
        self.assertEqual(result['stop_reason'], 'unknown table access')

    def test_buffer_write_reaches_subsequent_read(self):
        arrays = {'g': [3, 0], 'G': [46, 94], 'B': [1, 0], 'p': [0, 5]}
        buf = Opaque('shared_buffer')
        result = walk(arrays, b'\x00\x00\x00\x00', [],
                      {1:Opaque('d[76]'), 2:buf, 3:0, 4:0x12345678,
                       5:Opaque('d[6]'), 6:buf, 7:0}, 1, 0, 0)
        self.assertEqual(result['data'], bytes.fromhex('78563412'))
        self.assertEqual(result['registers'][5], 0x5678)
        self.assertEqual(result['stop_reason'], 'pc_out_of_bounds')


if __name__ == '__main__':
    unittest.main()
