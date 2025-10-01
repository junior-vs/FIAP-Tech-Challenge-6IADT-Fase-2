import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)  # Go up one level to src
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from domain.route import Route
from app_logging import log_performance, get_logger


class FitnessFunction:

    # Logger para esta classe
    logger = get_logger(__name__)

    # Definir as capacidades (Constantes do Veículo)
    MAX_WEIGHT = 500_000.0      # Capacidade máxima em gramas (500 kg)
    MAX_VOLUME = 5_000_000.0    # Capacidade máxima em cm³ (5 m³)

    # Pesos de Penalidade (Ajuste fino necessário para o AG)
    PENALTY_WEIGHT_FACTOR = 1.0      # Penaliza a sobrecarga de peso (ajuste conforme necessário)
    PENALTY_VOLUME_FACTOR = 0.002    # Penaliza a sobrecarga de volume (ajuste conforme necessário)

    @staticmethod
    @log_performance
    def calculate_fitness_with_constraints(route: Route) -> float:
        """
        Calcula o fitness considerando restrições de capacidade do veículo.
        - Usa DeliveryPoint.product (um único Product por ponto).
        - Peso em gramas.
        - Volume em cm³.
        - Aplica penalidades para excedentes de peso e volume.
        """
        if not hasattr(route, "distancia_total"):
            FitnessFunction.logger.warning("Objeto passado não possui método distancia_total.")
            return 0.0

        total_distance = route.distancia_total()
        if total_distance <= 0:
            FitnessFunction.logger.warning("Fitness calculado para rota com distância zero ou negativa")
            return 0.0

        # 2) Acúmulo de capacidades requisitadas
        total_weight_g = 0.0
        total_volume_cm3 = 0.0

        for point in getattr(route, "delivery_points", []):
            product = getattr(point, "product", None)
            if product is None:
                FitnessFunction.logger.warning("DeliveryPoint sem product; ignorando no cálculo de capacidade.")
                continue

            # Peso em gramas (product.weight já está em gramas)
            try:
                total_weight_g += float(product.weight)
            except Exception:
                FitnessFunction.logger.warning("Produto com peso inválido; considerando 0g.", exc_info=False)

            # Volume em cm³ (product.volume está em cm³)
            vol_cm3 = getattr(product, "volume", None)
            if vol_cm3 is None:
                # fallback: recalcula a partir das dimensões se disponível
                length = float(getattr(product, "length", 0.0))
                width = float(getattr(product, "width", 0.0))
                height = float(getattr(product, "height", 0.0))
                vol_cm3 = length * width * height
            try:
                total_volume_cm3 += float(vol_cm3)
            except Exception:
                FitnessFunction.logger.warning("Produto com volume inválido; considerando 0 cm³.", exc_info=False)

        # 3) Penalidades por exceder capacidades
        weight_overshoot = max(0.0, total_weight_g - FitnessFunction.MAX_WEIGHT)
        volume_overshoot = max(0.0, total_volume_cm3 - FitnessFunction.MAX_VOLUME)

        weight_penalty = weight_overshoot * FitnessFunction.PENALTY_WEIGHT_FACTOR
        volume_penalty = volume_overshoot * FitnessFunction.PENALTY_VOLUME_FACTOR

        # 4) Custo total
        total_cost = total_distance + weight_penalty + volume_penalty

        # Log detalhado para ajuste fino dos fatores de penalidade
        FitnessFunction.logger.debug(
            "Fitness c/ restrições -> dist: %.3f, peso(g): %.1f, vol(cm³): %.0f, "
            "excedente_peso: %.1f, excedente_vol: %.0f, pen_peso: %.1f, pen_vol: %.3f, custo: %.3f",
            total_distance, total_weight_g, total_volume_cm3,
            weight_overshoot, volume_overshoot, weight_penalty, volume_penalty, total_cost
        )

        # 5) Fitness (evita divisão por zero)
        return 1.0 / total_cost if total_cost > 0 else 0.0
    

    @staticmethod
    @log_performance
    def calcular_fitness(individuo: Route) -> float:
        """Calcula o valor de fitness de um indivíduo (Route).

        O valor de fitness é definido como o inverso da distância total
        da Route. Se a distância for 0 (Route vazia), retorna 0.0.
        """
        distancia = individuo.distancia_total()
        if distancia == 0:
            FitnessFunction.logger.warning("Fitness calculado para rota com distância zero")
            return 0.0
        
        fitness = 1 / distancia
        FitnessFunction.logger.debug(f"Fitness calculado: {fitness:.6f} (distância: {distancia:.2f})")
        return fitness

    @staticmethod
    @log_performance
    def calculate_fitness(route: Route) -> float:
        """Calcula o fitness de uma Route (1 / distancia_total).

        Returns 0 for empty or zero-distance (avoid division by zero).
        """
        total_distance = route.distancia_total()
        if total_distance <= 0:
            FitnessFunction.logger.warning("Fitness calculado para rota com distância zero ou negativa")
            return 0
        
        fitness = 1.0 / total_distance
        FitnessFunction.logger.debug(f"Fitness calculado: {fitness:.6f} (distância: {total_distance:.2f})")
        return fitness



