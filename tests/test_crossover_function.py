import unittest
import random
from src.functions.crossover_function import Crossover
from src.domain.route import Route
from src.domain.delivery_point import DeliveryPoint

class DummyProduct:
    def __init__(self, name, priority=0):
        self.name = name
        self.priority = priority

class TestCrossover(unittest.TestCase):
    def setUp(self):
        # Deterministic random for reproducibility
        random.seed(42)
        # Create 5 delivery points with unique products
        self.points = [DeliveryPoint(x, x, DummyProduct(f"P{x}", priority=x)) for x in range(5)]
        self.route1 = Route(self.points)
        self.route2 = Route(list(reversed(self.points)))

    def test_order_crossover(self):
        child = Crossover.order_crossover(self.route1, self.route2)
        self.assertEqual(len(child.delivery_points), 5)
        self.assertEqual(set(child.delivery_points), set(self.points))

    def test_order_crossover_v2(self):
        child = Crossover.order_crossover_v2(self.route1, self.route2)
        self.assertEqual(len(child.delivery_points), 5)
        self.assertEqual(set(child.delivery_points), set(self.points))

    def test_erx_crossover(self):
        child = Crossover.erx_crossover(self.route1, self.route2)
        self.assertEqual(len(child.delivery_points), 5)
        self.assertEqual(set(child.delivery_points), set(self.points))

    def test_crossover_ordenado_ox1(self):
        c1, c2 = Crossover.crossover_ordenado_ox1(self.route1, self.route2)
        self.assertEqual(len(c1.delivery_points), 5)
        self.assertEqual(len(c2.delivery_points), 5)
        self.assertEqual(set(c1.delivery_points), set(self.points))
        self.assertEqual(set(c2.delivery_points), set(self.points))

    def test_crossover_de_ciclo_cx(self):
        c1, c2 = Crossover.crossover_de_ciclo_cx(self.route1, self.route2)
        self.assertEqual(len(c1.delivery_points), 5)
        self.assertEqual(len(c2.delivery_points), 5)
        self.assertEqual(set(c1.delivery_points), set(self.points))
        self.assertEqual(set(c2.delivery_points), set(self.points))

    def test_crossover_multiplos_pontos_kpoint(self):
        c1, c2 = Crossover.crossover_multiplos_pontos_kpoint(self.route1, self.route2, k=2)
        self.assertEqual(len(c1.delivery_points), 5)
        self.assertEqual(len(c2.delivery_points), 5)
        self.assertEqual(set(c1.delivery_points), set(self.points))
        self.assertEqual(set(c2.delivery_points), set(self.points))

    def test_crossover_parcialmente_mapeado_pmx(self):
        c1, c2 = Crossover.crossover_parcialmente_mapeado_pmx(self.route1, self.route2)
        self.assertEqual(len(c1.delivery_points), 5)
        self.assertEqual(len(c2.delivery_points), 5)
        self.assertEqual(set(c1.delivery_points), set(self.points))
        self.assertEqual(set(c2.delivery_points), set(self.points))

    def test_prioritize(self):
        shuffled = list(self.points)
        random.shuffle(shuffled)
        prioritized = Crossover._prioritize(shuffled)
        priorities = [p.product.priority for p in prioritized]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

if __name__ == "__main__":
    unittest.main()
