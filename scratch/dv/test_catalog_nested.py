import unittest
from catalog_nested import catalog
from unmask_record import unmask


class NestedCatalogTest(unittest.TestCase):
    def test_native_and_invalid_prototypes(self):
        plain = bytes.fromhex('020100b77c020132')
        data = bytes.fromhex('b808') + unmask(plain, 186, 187) + bytes.fromhex('b80500')
        records, failures = catalog(data, [0, 10, 500])
        self.assertEqual(records[0]['native_factory']['selector'], 7164)
        self.assertEqual(failures[0]['index'], 2)
        self.assertEqual(len(records), 1)


if __name__ == '__main__': unittest.main()
