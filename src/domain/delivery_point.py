import numpy as np
from scipy.spatial.distance import euclidean
import math
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    # Import only for type checking to avoid any potential circular imports at runtime
    from product import Product

class DeliveryPoint:
    def __init__(self, x: float, y: float, product: "Product"):
        self.x = x
        self.y = y
        self.product = product

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
                mat[i, j] = points[i].distancia_euclidean(points[j])
        return mat

    def __repr__(self):
        pname = getattr(self.product, "name", None)
        return f"Delivery Point (x={self.x}, y={self.y}, product={pname})"
    
    # Adicionar ao final da classe DeliveryPoint (delivery_point.py)
    def __eq__(self, other: object) -> bool:
        """Compara dois DeliveryPoints. Eles são iguais se tiverem a mesma posição (x, y)."""
        if not isinstance(other, DeliveryPoint):
            return NotImplemented
        # Comparamos apenas as coordenadas. O produto associado não define o ponto de entrega.
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Define o hash para que DeliveryPoint possa ser usado em sets e dicionários."""
        return hash((self.x, self.y))

    @staticmethod
    def create_depot(center_x: float, center_y: float) -> "DeliveryPoint":
        """
        Cria um ponto de depósito sem produto associado.
        
        Args:
            center_x: Coordenada X do depósito
            center_y: Coordenada Y do depósito
            
        Returns:
            DeliveryPoint representando o depósito
        """
        return DeliveryPoint(center_x, center_y, product=None)

    @classmethod
    def generate_random_points(cls, num_points: int, min_x: int, max_x: int, 
                              min_y: int, max_y: int, priority_percentage: float) -> List["DeliveryPoint"]:
        """
        Gera pontos de entrega aleatórios com produtos.
        
        Args:
            num_points: Número de pontos a gerar
            min_x, max_x: Limites X da área
            min_y, max_y: Limites Y da área
            priority_percentage: Porcentagem para prioridade de produtos
            
        Returns:
            Lista de pontos de entrega gerados
        """
        import random
        from product import Product
        
        points = []
        for i in range(num_points):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            product = Product.make_random_product(i, priority_percentage)
            points.append(cls(x, y, product))
        return points

    @classmethod
    def generate_circle_points(cls, num_points: int, center_x: float, center_y: float, 
                              radius: float, priority_percentage: float) -> List["DeliveryPoint"]:
        """
        Gera pontos de entrega em formato circular.
        
        Args:
            num_points: Número de pontos a gerar
            center_x, center_y: Centro do círculo
            radius: Raio do círculo
            priority_percentage: Porcentagem para prioridade de produtos
            
        Returns:
            Lista de pontos de entrega em círculo
        """
        import math
        from product import Product
        
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            product = Product.make_random_product(i, priority_percentage)
            points.append(cls(int(x), int(y), product))
        return points