"""Domain model for a route used by the TSP genetic algorithm.

This module provides the :class:`Route` class which encapsulates a
sequence of :class:`DeliveryPoint` instances and implements common
operations used by genetic operators (distance calculation and
mutations).

The attribute name chosen in this project is ``delivery_points`` and is
a list holding the ordered delivery points.
"""

from typing import List, Iterator, Optional
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
        self.vehicle_type: Optional[str] = None

    def __len__(self) -> int:
        """Retorna o número de pontos nesta Route."""
        return len(self.delivery_points)

    def copy(self) -> "Route":
        """Cria uma cópia rasa da Route (lista de pontos copiada)."""
        r = Route(self.delivery_points[:])
        r.vehicle_type = self.vehicle_type
        return r

    def __iter__(self) -> Iterator[DeliveryPoint]:
        """Iterador sobre os pontos da Route."""
        return iter(self.delivery_points)

    # ---------------------------
    # Distâncias
    # ---------------------------

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

    def distancia_roundtrip(self, deposito: DeliveryPoint) -> float:
        """(VRP) Distância depósito -> pontos na ordem -> depósito.

        Se a rota estiver vazia, retorna 0.0.
        """
        if not self.delivery_points:
            return 0.0
        total = 0.0
        # depósito -> primeiro
        total += deposito.distancia_euclidean(self.delivery_points[0])
        # dentro da rota
        for i in range(len(self.delivery_points) - 1):
            total += self.delivery_points[i].distancia_euclidean(self.delivery_points[i + 1])
        # último -> depósito
        total += self.delivery_points[-1].distancia_euclidean(deposito)
        return total

    def cost_roundtrip(self, deposito: DeliveryPoint, cost_per_km: float) -> float:
        """(VRP) Custo da rota considerando o custo por km do veículo."""
        return self.distancia_roundtrip(deposito) * float(cost_per_km)

    # ---------------------------
    # Utilidades de VRP
    # ---------------------------

    def assign_vehicle(self, name: Optional[str]) -> None:
        """Atribui/atualiza o rótulo do tipo de veículo desta rota."""
        self.vehicle_type = name

    def __repr__(self) -> str:
        v = f", vehicle_type={self.vehicle_type!r}" if self.vehicle_type else ""
        return f"Route({self.delivery_points}{v})"
