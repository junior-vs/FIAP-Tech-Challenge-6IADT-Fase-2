import sys
import os
from typing import List, Tuple, Dict, Optional
from math import inf

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)  # Go up one level to src
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from domain.route import Route
from app_logging import log_performance, get_logger

# === frota (tipos de veículos) ===
try:
    from domain.vehicle import VehicleType
except Exception: 
    class VehicleType:
        def __init__(self, name: str, count: int, autonomy: float, cost_per_km: float = 1.0):
            self.name = name
            self.count = count
            self.autonomy = float(autonomy)
            self.cost_per_km = float(cost_per_km)


class FitnessFunction:

    # Logger para esta classe
    logger = get_logger(__name__)

    MAX_WEIGHT = 500_000.0      # Capacidade máxima em gramas (500 kg)
    MAX_VOLUME = 5_000_000.0    # Capacidade máxima em cm³ (5 m³)

    # Pesos de Penalidade (Ajuste fino necessário para o AG)
    PENALTY_WEIGHT_FACTOR = 1.0      # Penaliza a sobrecarga de peso (ajuste conforme necessário)
    PENALTY_VOLUME_FACTOR = 0.002    # Penaliza a sobrecarga de volume (ajuste conforme necessário)

    # Penalidade global para inviabilidade de frota/autonomia
    BIG_PENALTY = 1e12


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

        # --- Penalidade por prioridade ---
        penalty = 0.0
        n = len(route.delivery_points)
        for idx, dp in enumerate(route.delivery_points):
            if hasattr(dp, "product") and dp.product and hasattr(dp.product, "priority"):
                priority = dp.product.priority
                # Penalidade: prioridade alta em posições tardias
                penalty += priority * (idx / max(1, n-1))  # idx=0 é início, idx=n-1 é fim
        # Normaliza penalidade (quanto menor, melhor)
        penalty_weight = 2.0  # ajuste conforme necessário

        # 4) Custo total
        total_cost = (total_distance + penalty_weight * penalty + 1e-6) + weight_penalty + volume_penalty

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


    @staticmethod
    def _roundtrip_distance(points: List, deposito) -> float:
        """Distância depósito -> points... -> depósito.
        Aplica um fator de escala para converter pixels em km, facilitando o uso de autonomia realista.
        """
        if not points:
            return 0.0

        scale = 0.1  # 0.1 = 10px ≈ 1km

        total = deposito.distancia_euclidean(points[0]) * scale
        for i in range(len(points) - 1):
            total += points[i].distancia_euclidean(points[i + 1]) * scale
        total += points[-1].distancia_euclidean(deposito) * scale

        return total


    @staticmethod
    def _split_with_vehicle_choice(order: List, deposito, fleet: List[VehicleType]) -> Tuple[float, List[Route], Dict[str, int], float]:
        N = len(order)
        best_cost = [inf] * (N + 1)
        prev = [-1] * (N + 1)
        veh_at: List[Optional[VehicleType]] = [None] * (N + 1)
        best_cost[0] = 0.0

        # --- Armazena as rotas para penalidade de prioridade ---
        route_splits = [None] * (N + 1)

        for i in range(N):
            if best_cost[i] == inf:
                continue
            for j in range(i + 1, N + 1):
                seq = order[i:j]
                dist = FitnessFunction._roundtrip_distance(seq, deposito)

                # escolhe veículo mais barato que atende autonomia
                chosen: Optional[VehicleType] = None
                chosen_cost = inf
                for vt in fleet:
                    if dist <= vt.autonomy:
                        c = vt.cost_per_km * dist
                        if c < chosen_cost:
                            chosen_cost = c
                            chosen = vt

                if chosen is None:
                    continue  # nenhum veículo atende esta rota

                cand = best_cost[i] + chosen_cost
                if cand < best_cost[j]:
                    best_cost[j] = cand
                    prev[j] = i
                    veh_at[j] = chosen
                    route_splits[j] = seq[:]  # Salva a sequência para penalidade

        if best_cost[N] == inf:
            return FitnessFunction.BIG_PENALTY, [], {}, 0.0

        # reconstrói rotas e contabiliza uso por tipo
        routes: List[Route] = []
        usage: Dict[str, int] = {}
        j = N
        split_sequences = []
        while j > 0:
            i = prev[j]
            seq = order[i:j]
            split_sequences.append(seq)
            r = Route(seq[:])
            vt = veh_at[j]
            if hasattr(r, "assign_vehicle"):
                r.assign_vehicle(vt.name)
            else:
                try:
                    r.vehicle_type = vt.name
                except Exception:
                    pass
            routes.append(r)
            usage[vt.name] = usage.get(vt.name, 0) + 1
            j = i
        routes.reverse()
        split_sequences.reverse()

        # penaliza excesso de quantidade por tipo
        penalty = 0.0
        caps: Dict[str, int] = {vt.name: vt.count for vt in fleet}
        for t, used in usage.items():
            if used > caps.get(t, 0):
                penalty += (used - caps.get(t, 0)) * FitnessFunction.BIG_PENALTY * 0.01

        # --- PENALIDADE DE PRIORIDADE ---
        priority_penalty = 0.0
        priority_weight = 2.0  # Ajustar conforme necessário
        for seq in split_sequences:
            n = len(seq)
            for idx, dp in enumerate(seq):
                if hasattr(dp, "product") and dp.product and hasattr(dp.product, "priority"):
                    priority = dp.product.priority
                    # Penaliza prioridade alta em posições tardias
                    priority_penalty += priority * (idx / max(1, n-1)) if n > 1 else 0

        penalty += priority_penalty * priority_weight

        return best_cost[N] + penalty, routes, usage, penalty

    @staticmethod
    @log_performance
    def calculate_fitness_with_fleet(route: Route, deposito, fleet: List[VehicleType]) -> Tuple[float, List[Route], Dict[str, int]]:
        order = getattr(route, "delivery_points", None)
        if not order:
            FitnessFunction.logger.warning("Rota vazia para cálculo com frota.")
            return 0.0, [], {}

        total_cost, routes, usage, penalty = FitnessFunction._split_with_vehicle_choice(order, deposito, fleet)

        if total_cost >= FitnessFunction.BIG_PENALTY:
            FitnessFunction.logger.warning("Solução inviável (autonomia/frota). Aplicando penalidade.")
            return 0.0, [], {}

        FitnessFunction.logger.debug(
            "VRP Fleet -> custo_total: %.3f, rotas: %d, uso: %s, penalidade_qtd: %.3f",
            total_cost, len(routes), usage, penalty
        )

        fitness = 1.0 / total_cost if total_cost > 0 else 0.0
        return fitness, routes, usage
