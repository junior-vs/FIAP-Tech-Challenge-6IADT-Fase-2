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
    logger = get_logger(__name__)

    MAX_WEIGHT = 500_000.0
    MAX_VOLUME = 5_000_000.0
    PENALTY_WEIGHT_FACTOR = 1.0
    PENALTY_VOLUME_FACTOR = 0.002
    BIG_PENALTY = 1e12

    # ===============================
    # --- MÉTODOS AUXILIARES ---
    # ===============================
    @staticmethod
    def _roundtrip_distance(points: List, deposito) -> float:
        """Distância depósito -> pontos -> depósito (pixels → km)."""
        if not points:
            return 0.0
        scale = 0.1
        total = deposito.distancia_euclidean(points[0]) * scale
        for i in range(len(points) - 1):
            total += points[i].distancia_euclidean(points[i + 1]) * scale
        total += points[-1].distancia_euclidean(deposito) * scale
        return total

    # ===============================
    # --- FITNESS COM FROTA (VRP) ---
    # ===============================
    @staticmethod
    def _split_with_vehicle_choice(order: List, deposito, fleet: List[VehicleType]) -> Tuple[float, List[Route], Dict[str, int], float]:
        """Divide a sequência em subrotas válidas, escolhendo o veículo ideal."""
        N = len(order)
        best_cost = [inf] * (N + 1)
        prev = [-1] * (N + 1)
        veh_at: List[Optional[VehicleType]] = [None] * (N + 1)
        best_cost[0] = 0.0

        route_splits = [None] * (N + 1)

        for i in range(N):
            if best_cost[i] == inf:
                continue
            for j in range(i + 1, N + 1):
                seq = order[i:j]
                dist = FitnessFunction._roundtrip_distance(seq, deposito)

                # Veículo mais barato que atende autonomia
                chosen, chosen_cost = None, inf
                for vt in fleet:
                    if dist <= vt.autonomy:
                        c = vt.cost_per_km * dist
                        if c < chosen_cost:
                            chosen_cost = c
                            chosen = vt

                if chosen is None:
                    continue

                cand = best_cost[i] + chosen_cost
                if cand < best_cost[j]:
                    best_cost[j] = cand
                    prev[j] = i
                    veh_at[j] = chosen
                    route_splits[j] = seq[:]

        if best_cost[N] == inf:
            return FitnessFunction.BIG_PENALTY, [], {}, 0.0

        # Reconstrói rotas
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
                r.vehicle_type = vt.name
            routes.append(r)
            usage[vt.name] = usage.get(vt.name, 0) + 1
            j = i
        routes.reverse()
        split_sequences.reverse()

        # Penalização por excesso de veículos
        penalty = 0.0
        caps = {vt.name: vt.count for vt in fleet}
        for t, used in usage.items():
            if used > caps.get(t, 0):
                penalty += (used - caps.get(t, 0)) * FitnessFunction.BIG_PENALTY * 0.01

        # Penalidade de prioridade (produtos importantes no fim da rota)
        priority_penalty = 0.0
        for seq in split_sequences:
            n = len(seq)
            for idx, dp in enumerate(seq):
                prod = getattr(dp, "product", None)
                if prod and hasattr(prod, "priority"):
                    priority_penalty += prod.priority * (idx / max(1, n - 1))
        penalty += priority_penalty * 2.0

        return best_cost[N] + penalty, routes, usage, penalty

    # ===============================
    # --- FITNESS PRINCIPAL (VRP) ---
    # ===============================
    @staticmethod
    @log_performance
    def calculate_fitness_with_constraints(route: Route) -> float:
        """
        Calcula o fitness considerando restrições básicas de capacidade (TSP simples).
        Aplica penalizações por excesso de peso e volume.
        """
        if not hasattr(route, "distancia_total"):
            FitnessFunction.logger.warning("Objeto passado não possui método distancia_total.")
            return 0.0

        total_distance = route.distancia_total()
        if total_distance <= 0:
            return 0.0

        total_weight_g = 0.0
        total_volume_cm3 = 0.0
        for point in getattr(route, "delivery_points", []):
            prod = getattr(point, "product", None)
            if not prod:
                continue
            try:
                total_weight_g += float(prod.weight)
                vol_cm3 = getattr(prod, "volume", prod.length * prod.width * prod.height)
                total_volume_cm3 += float(vol_cm3)
            except Exception:
                continue

        # Penalidades se exceder capacidade
        weight_overshoot = max(0.0, total_weight_g - FitnessFunction.MAX_WEIGHT)
        volume_overshoot = max(0.0, total_volume_cm3 - FitnessFunction.MAX_VOLUME)
        penalty = weight_overshoot * FitnessFunction.PENALTY_WEIGHT_FACTOR \
                  + volume_overshoot * FitnessFunction.PENALTY_VOLUME_FACTOR

        total_cost = total_distance + penalty + 1e-6
        return 1.0 / total_cost if total_cost > 0 else 0.0


    @staticmethod
    @log_performance
    def calculate_fitness_with_fleet(route: Route, deposito, fleet: List[VehicleType]) -> Tuple[float, List[Route], Dict[str, int]]:
        """Calcula o fitness considerando frota e restrições de unicidade."""
        order = getattr(route, "delivery_points", None)
        if not order:
            FitnessFunction.logger.warning("Rota vazia para cálculo com frota.")
            return 0.0, [], {}

        # ---- (1) Garantir unicidade de cidades ----
        seen = set()
        filtered_order = []
        for city in order:
            if city not in seen:
                seen.add(city)
                filtered_order.append(city)
            else:
                FitnessFunction.logger.debug(f"[VRP] Cidade duplicada detectada: {city}")
        missing = len(order) - len(filtered_order)

        # ---- (2) Avaliação principal ----
        total_cost, routes, usage, penalty = FitnessFunction._split_with_vehicle_choice(filtered_order, deposito, fleet)

        # ---- (3) Penalização se houver duplicatas ou cidades omitidas ----
        extra_penalty = 0.0
        if missing > 0:
            extra_penalty += missing * 1e6
        # Caso o número de cidades nas rotas não bata com o total esperado
        total_in_routes = sum(len(r.delivery_points) for r in routes)
        if total_in_routes != len(filtered_order):
            diff = abs(len(filtered_order) - total_in_routes)
            extra_penalty += diff * 1e6

        total_cost += extra_penalty

        if total_cost >= FitnessFunction.BIG_PENALTY:
            FitnessFunction.logger.warning("Solução inviável (autonomia/frota). Aplicando penalidade.")
            return 0.0, [], {}

        FitnessFunction.logger.debug(
            "VRP Fleet -> custo_total: %.3f, rotas: %d, uso: %s, penalidades: %.3f + %.3f",
            total_cost, len(routes), usage, penalty, extra_penalty
        )

        fitness = 1.0 / total_cost if total_cost > 0 else 0.0
        return fitness, routes, usage
