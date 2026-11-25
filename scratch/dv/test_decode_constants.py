import unittest
from decode_constants import decode


class ConstantDecodeTest(unittest.TestCase):
    def test_string_with_word_and_tail(self):
        result = decode(bytes.fromhex('71057ce0eae3af'), [0], 1)
        self.assertEqual(result['utf8'], 'hello')

    def test_signed_integer_and_byte(self):
        self.assertEqual(decode(bytes.fromhex('46c8a50e27'), [0], 1)['value'], 0x12345678)
        self.assertEqual(decode(bytes.fromhex('edce02414d'), [0] * 764, 764)['value'], 2634154227)
        self.assertEqual(decode(bytes.fromhex('f267'), [0], 1)['value'], 7)

    def test_upvalue_capture_triples(self):
        result = decode(bytes.fromhex('aa050b998437c6'), [0] * 472, 472)
        self.assertEqual(result['hex'], '0283678363')
        self.assertEqual(result['captures'], [[3, 9644, 121], [3, 9644, 120]])

    def test_boolean_sentinel(self):
        self.assertIs(decode(bytes.fromhex('1f53'), [0] * 45, 45)['value'], False)
        self.assertIs(decode(bytes.fromhex('1f1b'), [0] * 84, 84)['value'], True)

    def test_negative_byte(self):
        self.assertEqual(decode(bytes.fromhex('a982'), [0] * 10, 10)['value'], -1)

    def test_float_and_vectors(self):
        self.assertEqual(decode(bytes.fromhex('a75b929d02'), [0] * 8, 8)['value'], 0.25)
        v2 = decode(bytes.fromhex('1c6af3c39b036c5497'), [0] * 432, 432)
        self.assertEqual(v2['kind'], 'Vector2')
        self.assertAlmostEqual(v2['components'][0], 0.595, places=6)
        v3 = decode(bytes.fromhex('cb838e963118d803e445949fe8'), [0] * 142, 142)
        self.assertEqual(v3['kind'], 'Vector3')
        self.assertAlmostEqual(v3['components'][2], 0.37131017, places=6)

    def test_signed_and_unsigned_short(self):
        self.assertEqual(decode(bytes.fromhex('c36fc9'), [0] * 297, 297)['value'], -7673)
        self.assertEqual(decode(bytes.fromhex('f4626a'), [0] * 302, 302)['value'], 667)

    def test_signed_64_bit_integer(self):
        result = decode(bytes.fromhex('68a8493aa356e586bf'), [0] * 157, 157)
        self.assertEqual((result['low_word'], result['high_word']), (0, 2))
        self.assertEqual(result['value'], 8589934592)
        self.assertEqual(decode(bytes.fromhex('68cbba99e09f5e4d24'), [0], 1)['value'], -1)
        with self.assertRaises(ValueError):
            decode(bytes.fromhex('6801'), [0], 1)

    def test_double_uses_successive_stream_words(self):
        result = decode(bytes.fromhex('dab7635910bd57ff39'), [0] * 594, 594)
        self.assertEqual(result['classification'], 'finite')
        self.assertEqual(result['value'], 0.9432631033482535)

    def test_rejects_unknown_tags_and_short_records(self):
        for data in (bytes.fromhex('00'), bytes.fromhex('710361'), bytes.fromhex('4601'), bytes.fromhex('f2'), bytes.fromhex('1f'), bytes.fromhex('a9'), bytes.fromhex('da00')):
            with self.assertRaises(ValueError):
                decode(data, [0], 1)


if __name__ == '__main__':
    unittest.main()
