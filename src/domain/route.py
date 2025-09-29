"""Domain model for a route used by the TSP genetic algorithm.

This module provides the :class:`Route` class which encapsulates a
sequence of :class:`DeliveryPoint` instances and implements common
operations used by genetic operators (distance calculation and
mutations).

The attribute name chosen in this project is ``delivery_points`` and is
a list holding the ordered delivery points.
"""

from typing import List, Iterator
from delivery_point import DeliveryPoint
import random


class Route:
    """Representa uma Route (sequência cíclica) de pontos de entrega.

    Args:
        delivery_points: lista de :class:`DeliveryPoint` que compõem a Route.
    """

    def __init__(self, delivery_points: List[DeliveryPoint]):
        # guarda uma cópia da lista passada
        self.delivery_points: List[DeliveryPoint] = list(delivery_points)

    def __len__(self) -> int:
        """Retorna o número de pontos nesta Route."""
        return len(self.delivery_points)

    def copy(self) -> "Route":
        """Cria uma cópia rasa da Route (lista de pontos copiada)."""
        return Route(self.delivery_points[:])

    def __iter__(self) -> Iterator[DeliveryPoint]:
        """Iterador sobre os pontos da Route."""
        return iter(self.delivery_points)

    def distancia_total(self) -> float:
        """Calcula a distância total do ciclo da Route.

        Usa o método ``distancia_euclidean`` de :class:`PontoDeEntrega`.
        Retorna 0.0 se a Route não contém pontos.
        """
        if not self.delivery_points:
            return 0.0
        total = 0.0
        n = len(self.delivery_points)
        for i in range(n):
            ponto_a = self.delivery_points[i]
            ponto_b = self.delivery_points[(i + 1) % n]  # volta ao início
            total += ponto_a.distancia_euclidean(ponto_b)
        return total

    def __repr__(self) -> str:
        return f"Route({self.delivery_points})"

