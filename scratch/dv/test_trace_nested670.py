import unittest
from trace_nested670 import point, F, B


class Nested670PointTest(unittest.TestCase):
    def test_key_and_nonce_point_rewrites(self):
        self.assertEqual(point('E201', {'g':173,'G':1654948,'B':82,'p':155}, B),
                         {'g':14,'G':227,'B':17,'p':220})
        self.assertEqual(point('Z250', {'g':38,'G':16777302,'B':28987,'p':97}, F),
                         {'g':131,'G':16777216,'B':19,'p':19})
        self.assertEqual(point('Z95', {'g':20730,'G':103,'B':103,'p':54}, F),
                         {'g':18,'G':186,'B':17,'p':0})

    def test_unknown_rewrite_is_rejected(self):
        with self.assertRaises(ValueError):
            point('Z95', {'g':0,'G':0,'B':0,'p':0}, F)


if __name__ == '__main__': unittest.main()
