import unittest

from static_walk import walk


class StaticWalkTest(unittest.TestCase):
    def test_branch_indirect_jump_and_unknown_stop(self):
        arrays = {'g': [0, 4, 0, 7, 0], 'G': [7, 3, 0, 0, 0],
                  'B': [2, 7, 0, 0, 0], 'p': [69, 147, 82, 70, 255]}
        arrays['G'][2] = 3
        result = walk(arrays, b'', [], 1, {}, 0, 0)
        self.assertEqual([e['pc'] for e in result['events']], [1, 2, 3, 4])
        self.assertEqual(result['pc'], 3)
        self.assertEqual(result['stop_reason'], 'repeated_abstract_state')

        result = walk(arrays, b'', [], 2, {}, 0, 0)
        self.assertEqual(result['pc'], 2)
        self.assertEqual(result['stop_reason'], 'unknown_branch')
        self.assertEqual(result['events'], [])

    def test_seeded_z240_block_requires_known_seed(self):
        arrays = {'g': [1, 0], 'G': [1, 0], 'B': [1, 0], 'p': [177, 255]}
        result = walk(arrays, b'', [], 1, {}, 0, 0, max_steps=1)
        self.assertEqual(result['events'][0]['rewrite']['initial_state'], 1)
        self.assertEqual(result['arrays']['p'][0], 154)
        arrays = {'g': [3, 1, 0], 'G': [0, 2, 0], 'B': [0, 1, 0], 'p': [40, 177, 255]}
        result = walk(arrays, b'', [], 1, {}, 0, 0)
        self.assertEqual(result['stop_reason'], 'unknown_block_rewrite_seed')
        self.assertEqual(result['pc'], 2)

    def test_record_rewrite_and_previously_mutated_pc(self):
        arrays = {'g': [1], 'G': [18], 'B': [0], 'p': [120]}
        data = bytes([0, 3, 1, 2, 3])
        result = walk(arrays, data, [236682589], 1, {}, 0, 0)
        self.assertEqual(result['data'], bytes([0, 3, 19, 16, 17]))
        self.assertEqual(result['updated_offsets'], [0])
        self.assertEqual([result['arrays'][x][0] for x in ('g', 'G', 'B', 'p')], [23, 157, 228, 154])
        self.assertEqual(arrays['p'][0], 120)
        result = walk(arrays, data, [236682589], 1, {}, 0, 0, {1})
        self.assertEqual(result['stop_reason'], 'previous_record_mutation_requires_reconciliation')
        self.assertEqual(result['data'], data)

    def test_block_rewrite_and_stop_on_external_call(self):
        arrays = {'g': [1, 0], 'G': [1, 0], 'B': [1, 0], 'p': [93, 0]}
        result = walk(arrays, b'', [], 1, {}, 0, 0)
        self.assertEqual(result['events'][0]['rewrite']['count'], 1)
        self.assertEqual(result['arrays']['p'][0], 154)
        self.assertEqual(result['stop_reason'], 'unsupported_opcode')
        self.assertEqual(result['pc'], 2)

    def test_unknown_value_does_not_become_zero(self):
        arrays = {'g': [0, 5], 'G': [4, 0], 'B': [5, 0], 'p': [54, 70]}
        result = walk(arrays, b'', [], 1, {5: 42}, 0, 0)
        self.assertNotIn(5, result['registers'])
        self.assertEqual(result['stop_reason'], 'unknown_indirect_target')

    def test_noop_call_and_slot_require_explicit_facts(self):
        arrays = {'g': [3, 131, 0, 131], 'G': [0, 3, 131, 3],
                  'B': [37, 1, 1, 1], 'p': [99, 125, 69, 125]}
        data = bytes.fromhex('71057ce0eae3af')
        unverified = walk(arrays, data, [0], 1, {}, 0, 0)
        self.assertEqual(unverified['stop_reason'], 'unverified_table_lookup')
        unknown_call = walk(arrays, data, [0], 1, {}, 0, 0, inert_slots={37})
        self.assertEqual(unknown_call['stop_reason'], 'unknown_call')
        unknown_cache = walk(arrays, data, [0], 1, {}, 0, 0,
                             noop_registers={131}, inert_slots={37})
        self.assertEqual(unknown_cache['stop_reason'], 'unknown_constant_cache')
        result = walk(arrays, data, [0], 1, {}, 0, 0,
                      noop_registers={131}, inert_slots={37}, uncached_pcs={2})
        self.assertEqual(result['events'][1]['constant']['utf8'], 'hello')
        self.assertEqual(result['stop_reason'], 'unknown_call')
        self.assertEqual(result['pc'], 4)

    def test_unknown_seed_and_effect_free_register_call(self):
        arrays = {'g': [3, 0, 4, 5], 'G': [0, 0, 6, 0],
                  'B': [0, 3, 131, 0], 'p': [40, 47, 203, 70]}
        result = walk(arrays, b'', [], 1, {3: 5}, 10, 20, noop_registers={131})
        self.assertEqual(result['f_seed'], 5)
        self.assertEqual(result['registers'][3], 5)
        self.assertEqual(result['stop_reason'], 'unknown_indirect_target')
        result = walk(arrays, b'', [], 1, {}, 10, 20, noop_registers={131})
        self.assertIsNone(result['f_seed'])
        self.assertNotIn(3, result['registers'])
        self.assertEqual(result['events'][0]['unknown_seed'], 'f')

    def test_point_rewrite_revisits_same_instruction(self):
        arrays = {'g': [22], 'G': [97], 'B': [6986], 'p': [29]}
        result = walk(arrays, b'', [], 1, {}, 4060069839, 0)
        self.assertEqual(result['events'][0]['rewrite'], {'g': 82, 'G': 47, 'B': 15, 'p': 118})
        self.assertEqual(result['events'][0]['next_pc'], 1)
        self.assertEqual(result['pc'], 1)
        self.assertEqual(result['stop_reason'], 'unknown_constant_cache')

        arrays = {'g': [3, 22], 'G': [0, 97], 'B': [0, 6986], 'p': [40, 29]}
        result = walk(arrays, b'', [], 1, {}, 10, 0)
        self.assertEqual(result['stop_reason'], 'unknown_self_rewrite_seed')
        self.assertEqual(result['arrays']['p'][1], 29)
        arrays = {'g': [8165], 'G': [4178130], 'B': [127], 'p': [14]}
        result = walk(arrays, b'', [], 1, {}, 1912518349, 0, max_steps=1)
        self.assertEqual(result['events'][0]['rewrite'], {'g': 8094, 'G': 188, 'B': 87, 'p': 147})

    def test_numeric_constant_xor_requires_cache_hypothesis(self):
        arrays = {'g': [1], 'G': [1], 'B': [4], 'p': [43]}
        data = bytes.fromhex('46c8a50e27')
        stopped = walk(arrays, data, [0], 1, {}, 0, 0)
        self.assertEqual(stopped['stop_reason'], 'unknown_constant_cache')
        result = walk(arrays, data, [0], 1, {}, 0, 0, uncached_pcs={1})
        self.assertEqual(result['registers'][4], 0)
        self.assertEqual(len(result['constant_cache']), 2)

    def test_assumed_table_write_invalidates_slot_fact(self):
        arrays = {'g': [0, 3], 'G': [1, 0], 'B': [1, 7], 'p': [23, 99]}
        data = bytes.fromhex('f267')  # index 1 decodes to integer 7
        stopped = walk(arrays, data, [0], 1, {}, 0, 0, inert_slots={7}, uncached_pcs={1})
        self.assertEqual(stopped['stop_reason'], 'unverified_table_write')
        result = walk(arrays, data, [0], 1, {}, 0, 0,
                      inert_slots={7}, uncached_pcs={1}, inert_lookup_pcs={1})
        self.assertEqual(result['events'][0]['constant_key']['value'], 7)
        self.assertEqual(result['stop_reason'], 'unverified_table_lookup')
        self.assertEqual(result['pc'], 2)

    def test_restored_cache_and_summarized_call(self):
        arrays = {'g': [1], 'G': [1], 'B': [4], 'p': [43]}
        cached = [{'field': 'W', 'pc': 1, 'value': {'tag': 242, 'value': 7}},
                  {'field': 'L', 'pc': 1, 'value': {'tag': 242, 'value': 3}}]
        result = walk(arrays, b'', [], 1, {}, 0, 0, initial_constant_cache=cached)
        self.assertEqual(result['registers'][4], 4)
        arrays = {'g': [3], 'G': [4], 'B': [9], 'p': [203]}
        result = walk(arrays, b'', [], 1, {120: 5, 121: 6, 122: 7}, 0, 0,
                      returning_call_pcs={1}, call_clobbers={1: (120, 121)})
        self.assertNotIn(120, result['registers'])
        self.assertNotIn(121, result['registers'])
        self.assertEqual(result['registers'][122], 7)
        self.assertEqual(result['events'][0]['clobbered_registers'], [120, 121])

    def test_indexed_register_write_is_guarded(self):
        arrays = {'g': [3], 'G': [4], 'B': [17], 'p': [171]}
        stopped = walk(arrays, b'', [], 1, {3:7}, 0, 0)
        self.assertEqual(stopped['stop_reason'], 'unknown_register_target')
        result = walk(arrays, b'', [], 1, {3:7, 4:5}, 0, 0)
        self.assertEqual(result['registers'][22], 7)
        self.assertEqual(result['events'][0]['register_write'], 22)

    def test_static_left_shift(self):
        arrays = {'g': [14], 'G': [3], 'B': [3], 'p': [108]}
        result = walk(arrays, b'', [], 1, {3:0x12345678}, 0, 0)
        self.assertEqual(result['registers'][3], 0x159e0000)

    def test_lua_truthiness_and_comparison_are_not_python_truthiness(self):
        arrays = {'g': [0, 3, 3, 0, 0], 'G': [3, 4, 0, 0, 0],
                  'B': [0, 3, 3, 0, 0], 'p': [69, 89, 168, 255, 255]}
        result = walk(arrays, b'', [], 1, {}, 0, 0)
        self.assertEqual(result['events'][1]['next_pc'], 5)  # Lua treats 0 as truthy.
        result = walk(arrays, b'', [], 3, {3: 0}, 0, 0)
        self.assertIs(result['registers'][3], True)
        arrays['p'][0], arrays['g'][0], arrays['G'][0] = 12, 3, 3
        result = walk(arrays, b'', [], 1, {3: True}, 0, 0)
        self.assertNotIn(3, result['registers'])


if __name__ == '__main__':
    unittest.main()
