"""
Population factory for genetic algorithm initialization.

This module provides utilities for creating initial populations of routes
following the Factory pattern and Single Responsibility Principle.
"""

import random
from typing import List
from src.domain.route import Route
from src.domain.delivery_point import DeliveryPoint
from src.functions.app_logging import get_logger


class PopulationFactory:
    """Factory for creating genetic algorithm populations."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def create_initial_population(self, delivery_points: List[DeliveryPoint], population_size: int) -> List[Route]:
        """Create an initial population of randomized routes.

        Args:
            delivery_points: List of delivery points.
            population_size: Desired population size (> 0).

        Returns:
            A list of Route instances with shuffled points.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not delivery_points:
            raise ValueError("Lista de pontos de entrega não pode estar vazia")
        if population_size <= 0:
            raise ValueError("Tamanho da população deve ser maior que zero")

        self.logger.info(f"Inicializando população de tamanho {population_size}")

        population: List[Route] = []
        for _ in range(population_size):
            shuffled = list(delivery_points)
            random.shuffle(shuffled)
            population.append(Route(shuffled))

        self.logger.debug(f"População inicializada com {len(population)} rotas")
        return population

    @staticmethod
    def create_random_route(delivery_points: List[DeliveryPoint]) -> Route:
        """Create a single random route from given points."""
        if not delivery_points:
            raise ValueError("Lista de pontos de entrega não pode estar vazia")
        shuffled = list(delivery_points)
        random.shuffle(shuffled)
        return Route(shuffled)