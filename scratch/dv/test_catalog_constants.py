import unittest
from catalog_constants import catalog


class ConstantCatalogTest(unittest.TestCase):
    def test_candidates_and_unresolved_records_are_distinct(self):
        result = catalog(bytes.fromhex('f26700'), [0, 2, 500])
        self.assertEqual(result[0]['status'], 'candidate')
        self.assertEqual(result[0]['value'], 7)
        self.assertEqual(result[1]['status'], 'unresolved')
        self.assertEqual(result[2]['status'], 'unresolved_offset')


if __name__ == '__main__':
    unittest.main()
