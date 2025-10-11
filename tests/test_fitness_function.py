import unittest
from unittest.mock import MagicMock
from src.functions.fitness_function import FitnessFunction
from src.domain.route import Route
from src.domain.vehicle import VehicleType
from src.domain.delivery_point import DeliveryPoint

class TestFitnessFunction(unittest.TestCase):
    def setUp(self):
        # Mock delivery points and products
        self.depot = MagicMock(spec=DeliveryPoint)
        self.product = MagicMock()
        self.product.weight = 1000.0
        self.product.volume = 1000.0
        self.product.priority = 1
        self.dp = MagicMock(spec=DeliveryPoint)
        self.dp.product = self.product
        self.route = MagicMock(spec=Route)
        self.route.delivery_points = [self.dp, self.dp]
        self.route.distancia_roundtrip = MagicMock(return_value=100.0)
        # Mock vehicle type
        self.vehicle = MagicMock(spec=VehicleType)
        self.vehicle.max_weight = 2000.0
        self.vehicle.max_volume = 2000.0
        # Fleet for VRP
        self.fleet = [self.vehicle]

    def test_calculate_fitness_with_constraints_valid(self):
        fitness = FitnessFunction.calculate_fitness_with_constraints(self.route, self.vehicle, self.depot)
        self.assertGreater(fitness, 0.0)

    def test_calculate_fitness_with_constraints_overweight(self):
        self.product.weight = 3000.0
        fitness = FitnessFunction.calculate_fitness_with_constraints(self.route, self.vehicle, self.depot)
        self.assertGreaterEqual(fitness, 0.0)

    def test_calculate_fitness_tsp(self):
        self.route.distancia_total = MagicMock(return_value=100.0)
        fitness = FitnessFunction.calculate_fitness_tsp(self.route)
        self.assertAlmostEqual(fitness, 1.0/100.0)

    def test_calculate_fitness_with_fleet_valid(self):
        fitness, routes, usage = FitnessFunction.calculate_fitness_with_fleet(self.route, self.depot, self.fleet)
        self.assertGreaterEqual(fitness, 0.0)
        self.assertIsInstance(routes, list)
        self.assertIsInstance(usage, dict)

    def test_calculate_fitness_with_fleet_empty_route(self):
        self.route.delivery_points = []
        fitness, routes, usage = FitnessFunction.calculate_fitness_with_fleet(self.route, self.depot, self.fleet)
        self.assertEqual(fitness, 0.0)
        self.assertEqual(routes, [])
        self.assertEqual(usage, {})

if __name__ == "__main__":
    unittest.main()
