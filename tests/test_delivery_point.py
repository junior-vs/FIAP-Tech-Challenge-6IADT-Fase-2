import unittest
import numpy as np
from src.domain.delivery_point import DeliveryPoint

class DummyProduct:
    def __init__(self, name="P1"):
        self.name = name

class TestDeliveryPoint(unittest.TestCase):
    def setUp(self):
        self.p1 = DummyProduct("A")
        self.p2 = DummyProduct("B")
        self.dp1 = DeliveryPoint(0.0, 0.0, self.p1)
        self.dp2 = DeliveryPoint(3.0, 4.0, self.p2)
        self.dp3 = DeliveryPoint(0.0, 0.0, self.p1)

    def test_distancia_np(self):
        self.assertAlmostEqual(self.dp1.distancia_np(self.dp2), 5.0)

    def test_distancia_euclidean(self):
        self.assertAlmostEqual(self.dp1.distancia_euclidean(self.dp2), 5.0)

    def test_distancia_pura(self):
        self.assertAlmostEqual(self.dp1.distancia_pura(self.dp2), 5.0)

    def test_compute_distance_matrix(self):
        points = [self.dp1, self.dp2]
        mat = DeliveryPoint.compute_distance_matrix(points)
        self.assertIsInstance(mat, np.ndarray)
        self.assertEqual(mat.shape, (2,2))
        self.assertAlmostEqual(mat[0,1], 5.0)
        self.assertAlmostEqual(mat[1,0], 5.0)
        self.assertEqual(mat[0,0], 0.0)

    def test_repr(self):
        r = repr(self.dp1)
        self.assertIn("x=0.0", r)
        self.assertIn("product=A", r)

    def test_eq_and_hash(self):
        self.assertEqual(self.dp1, self.dp3)
        self.assertNotEqual(self.dp1, self.dp2)
        s = {self.dp1, self.dp3, self.dp2}
        self.assertEqual(len(s), 2)

if __name__ == "__main__":
    unittest.main()
