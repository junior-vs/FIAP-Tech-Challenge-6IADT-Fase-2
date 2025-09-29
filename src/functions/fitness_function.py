import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)  # Go up one level to src
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from domain.route import Route


class FitnessFunction:

    @staticmethod
    def calcular_fitness(individuo: Route) -> float:
        """Calcula o valor de fitness de um indivíduo (Route).

        O valor de fitness é definido como o inverso da distância total
        da Route. Se a distância for 0 (Route vazia), retorna 0.0.
        """
        distancia = individuo.distancia_total()
        if distancia == 0:
            return 0.0
        return 1 / distancia

    @staticmethod
    def calculate_fitness(route: Route) -> float:
        """Calcula o fitness de uma Route (1 / distancia_total).

        Returns 0 for empty or zero-distance (avoid division by zero).
        """
        total_distance = route.distancia_total()
        return 1.0 / total_distance if total_distance > 0 else 0



