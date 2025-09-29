import numpy as np
from scipy.spatial.distance import euclidean
import math
from typing import List

class DeliveryPoint:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distancia_np(self, other: "DeliveryPoint") -> float:
        # Usando numpy
        return np.linalg.norm(np.array([self.x, self.y]) - np.array([other.x, other.y]))

    def distancia_euclidean(self, other: "DeliveryPoint") -> float:
        """
        Calcula a distância entre duas cidades usando a função euclidean do scipy.
        """
        return euclidean([self.x, self.y], [other.x, other.y])

    def distancia_pura(self, other: "DeliveryPoint") -> float:
        """
        Calcula a distância entre duas cidades usando apenas operações matemáticas básicas.
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    @staticmethod
    def compute_distance_matrix(points: List["DeliveryPoint"]) -> "np.ndarray":
        """
        Compute an NxN distance matrix for the given delivery points.
        Uses distancia_pura for stability (avoids scipy dependency in hot loops).
        """
        n = len(points)
        mat = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                mat[i, j] = points[i].distancia_pura(points[j])
        return mat

    def __repr__(self):
        return f"Delivery Point (x={self.x}, y={self.y})"