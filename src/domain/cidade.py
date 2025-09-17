import numpy as np
from scipy.spatial.distance import euclidean
import math

class Cidade:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distancia_np(self, outra: "Cidade") -> float:
        # Usando numpy
        return np.linalg.norm(np.array([self.x, self.y]) - np.array([outra.x, outra.y]))

    def distancia_euclidean(self, outra: "Cidade") -> float:
        """
        Calcula a distância entre duas cidades usando a função euclidean do scipy.
        """
        return euclidean([self.x, self.y], [outra.x, outra.y])

    def distancia_pura(self, outra: "Cidade") -> float:
        """
        Calcula a distância entre duas cidades usando apenas operações matemáticas básicas.
        """
        return math.sqrt((self.x - outra.x) ** 2 + (self.y - outra.y) ** 2)

    def __repr__(self):
        return f"Cidade(x={self.x}, y={self.y})"