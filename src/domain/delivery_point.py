import numpy as np
from scipy.spatial.distance import euclidean
import math

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

    def __repr__(self):
        return f"Delivery Point (x={self.x}, y={self.y})"