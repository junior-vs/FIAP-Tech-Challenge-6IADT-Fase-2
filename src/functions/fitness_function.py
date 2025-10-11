# src/core/fitness_function.py (Refatorado - Fitness VRP Capacitado)
from typing import List, Tuple, Dict, Optional
from math import inf

from src.functions.app_logging import get_logger, log_performance
from src.domain.route import Route
from src.domain.vehicle import VehicleType
from src.domain.delivery_point import DeliveryPoint

# ---------------------------------------------------------------------------------


class FitnessFunction:
    # Logger para esta classe
    logger = get_logger(__name__)

    # Removido: MAX_WEIGHT e MAX_VOLUME, pois agora vêm do VehicleType

    # Pesos de Penalidade (Ajuste fino necessário para o AG)
    PENALTY_WEIGHT_FACTOR = (
        1.0  # Penaliza a sobrecarga de peso (ajuste conforme necessário)
    )
    PENALTY_VOLUME_FACTOR = (
        0.002  # Penaliza a sobrecarga de volume (ajuste conforme necessário)
    )

    # Penalidade global para inviabilidade de frota/autonomia
    BIG_PENALTY = 1e12

    # Limite global opcional de veículos (None = sem limite)
    MAX_VEHICLES_TOTAL: Optional[int] = 5

    @classmethod
    def set_max_vehicles_total(cls, limit: Optional[int]) -> None:
        """Define limite global de veículos usados na solução (None desativa)."""
        cls.MAX_VEHICLES_TOTAL = limit
        cls.logger.info(f"Limite global de veículos definido para: {limit}")

    @staticmethod
    @log_performance
    def calculate_fitness_with_constraints(
        route: Route,
        vehicle_type: VehicleType,  # <<-- NOVO: Recebe o tipo de veículo
        deposito: DeliveryPoint,  # <<-- NOVO: Recebe o ponto de depósito
    ) -> float:
        """
        Calcula o fitness considerando restrições de capacidade do veículo e distância de roundtrip.
        - Usa vehicle_type para obter as capacidades (max_weight, max_volume).
        - Penaliza a rota se as capacidades forem excedidas.
        - Usa a distância de roundtrip (Depósito -> Pontos -> Depósito).
        """

        # 1) Distância total do roundtrip (VRP)
        # USADO AGORA: distancia_roundtrip, que inclui Depósito -> Pontos -> Depósito
        total_distance = route.distancia_roundtrip(deposito)

        if total_distance <= 0:
            FitnessFunction.logger.warning(
                "Fitness calculado para rota com distância zero ou negativa"
            )
            return 0.0

        # Limites do veículo atribuído (obtidos do VehicleType)
        MAX_W = vehicle_type.max_weight
        MAX_V = vehicle_type.max_volume

        # 2) Acúmulo de capacidades requisitadas (soma dos produtos na rota)
        total_weight_g = 0.0
        total_volume_cm3 = 0.0

        for point in getattr(route, "delivery_points", []):
            product = getattr(point, "product", None)
            if product is None:
                continue

            try:
                total_weight_g += float(product.weight)
            except Exception:
                FitnessFunction.logger.warning(
                    "Produto com peso inválido; considerando 0g."
                )

            vol_cm3 = getattr(product, "volume", 0.0)
            try:
                total_volume_cm3 += float(vol_cm3)
            except Exception:
                # Fallback se volume for nulo
                length = float(getattr(product, "length", 0.0))
                width = float(getattr(product, "width", 0.0))
                height = float(getattr(product, "height", 0.0))
                vol_cm3 = length * width * height
                total_volume_cm3 += float(vol_cm3)

        # 3) Penalidades por exceder capacidades
        weight_overshoot = max(0.0, total_weight_g - FitnessFunction.MAX_WEIGHT)
        volume_overshoot = max(0.0, total_volume_cm3 - FitnessFunction.MAX_VOLUME)

        # Novo: logar motivo(s) da inviabilidade quando houver excedentes
        if weight_overshoot > 0 or volume_overshoot > 0:
            reasons = []
            if weight_overshoot > 0:
                reasons.append(
                    f"peso excedido em {weight_overshoot:.1f} g (total {total_weight_g:.1f} g > máx {FitnessFunction.MAX_WEIGHT:.1f} g)"
                )
            if volume_overshoot > 0:
                reasons.append(
                    f"volume excedido em {volume_overshoot:.0f} cm³ (total {total_volume_cm3:.0f} cm³ > máx {FitnessFunction.MAX_VOLUME:.0f} cm³)"
                )
            FitnessFunction.logger.warning(
                "Solução inviável. Aplicando penalidade. Motivo(s): %s",
                "; ".join(reasons)
            )

        weight_penalty = weight_overshoot * FitnessFunction.PENALTY_WEIGHT_FACTOR
        volume_penalty = volume_overshoot * FitnessFunction.PENALTY_VOLUME_FACTOR

        # --- Penalidade por prioridade ---
        priority_penalty_acc = 0.0
        n = len(route.delivery_points)
        for idx, dp in enumerate(route.delivery_points):
            if (
                hasattr(dp, "product")
                and dp.product
                and hasattr(dp.product, "priority")
            ):
                priority = dp.product.priority
                # Penalidade: prioridade alta em posições tardias. idx=0 é o melhor
                priority_penalty_acc += priority * (idx / max(1, n - 1))

        penalty_weight = 2.0  # ajuste conforme necessário
        final_priority_penalty = priority_penalty_acc * penalty_weight

        # 4) Custo total
        # Custo = Distância (Roundtrip) + Penalidades (Capacidade + Prioridade)
        total_cost = (
            (total_distance + 1e-6)
            + weight_penalty
            + volume_penalty
            + final_priority_penalty
        )

        # Log detalhado (apenas para referência)
        FitnessFunction.logger.debug(
            "Fitness c/ restrições -> dist: %.3f, peso(g): %.1f/%.1f, vol(cm³): %.0f/%.0f, "
            "excedente_peso: %.1f, excedente_vol: %.0f, pen_peso: %.1f, pen_vol: %.3f, pen_prio: %.3f, custo: %.3f",
            total_distance,
            total_weight_g,
            MAX_W,
            total_volume_cm3,
            MAX_V,
            weight_overshoot,
            volume_overshoot,
            weight_penalty,
            volume_penalty,
            final_priority_penalty,
            total_cost,
        )

        # 5) Fitness (evita divisão por zero)
        return 1.0 / total_cost if total_cost > 0 else 0.0

    @staticmethod
    @log_performance
    def calculate_fitness_tsp(route: Route) -> float:
        """
        Calcula o fitness de uma Route (1 / distancia_total), ignorando restrições.
        Este é o fitness padrão do TSP (Caixeiro Viajante tradicional).
        """
        total_distance = route.distancia_total()
        if total_distance <= 0:
            FitnessFunction.logger.warning(
                "Fitness calculado para rota com distância zero ou negativa"
            )
            return 0

        fitness = 1.0 / total_distance
        FitnessFunction.logger.debug(
            f"Fitness calculado: {fitness:.6f} (distância: {total_distance:.2f})"
        )
        return fitness

    # Reatribuindo para manter compatibilidade com o código original (se necessário)
    calculate_fitness = calculate_fitness_tsp
    calcular_fitness = calculate_fitness_tsp

    # --- MÉTODOS DE SPLIT ---

    @staticmethod
    def _roundtrip_distance(delivery_points: List, depot: DeliveryPoint) -> float:
        """
        Calcula a distância total de um roundtrip (ida e volta) do depósito.

        Percurso: depósito -> ponto1 -> ponto2 -> ... -> pontoN -> depósito

        Aplicações:
        - Avaliação de viabilidade de autonomia de veículos
        - Cálculo de custos de combustível/tempo para segmentos de rota
        - Otimização de atribuição veículo-rota no VRP

        Observações técnicas:
        - Usa distância euclidiana como aproximação (pode ser substituída por APIs de roteamento)
        - Aplica fator de escala para converter coordenadas pixel em quilômetros reais
        - Fator 0.1 significa: 10 pixels ≈ 1 km (ajustar conforme mapa)

        Args:
            delivery_points: Lista de pontos de entrega na ordem do percurso
            depot: Ponto do depósito (origem e destino da rota)

        Returns:
            Distância total em quilômetros (considerando o fator de escala)

        Examples:
            >>> points = [point_a, point_b, point_c]
            >>> depot = depot_central
            >>> distance = _roundtrip_distance(points, depot)
            >>> print(f"Rota necessita {distance:.1f} km de autonomia")
        """

        if not delivery_points:
            return 0.0

        # Fator de conversão: pixel -> km (calibrado para o contexto do projeto)
        SCALE_FACTOR = 0.1  # 10 pixels = 1 km

        # Primeira etapa: depósito -> primeiro ponto
        total_distance = depot.distancia_euclidean(delivery_points[0]) * SCALE_FACTOR

        # Etapas intermediárias: ponto_i -> ponto_i+1
        for i in range(len(delivery_points) - 1):
            segment_distance = delivery_points[i].distancia_euclidean(
                delivery_points[i + 1]
            )
            total_distance += segment_distance * SCALE_FACTOR

        # Última etapa: último ponto -> depósito (volta)
        total_distance += delivery_points[-1].distancia_euclidean(depot) * SCALE_FACTOR

        return total_distance

    @staticmethod
    def _split_with_vehicle_choice(
        order: List, deposito, fleet: List[VehicleType]
    ) -> Tuple[float, List[Route], Dict[str, int], float]:
        """
        Divide uma sequência de entregas em múltiplas rotas, escolhendo para cada segmento
        o veículo mais barato que atende a autonomia, a fim de minimizar o custo total.

        Mantém a mesma assinatura e comportamento, porém com organização em helpers para
        melhorar simplicidade e legibilidade.

        Retorna: (custo_total, rotas, uso_por_tipo, penalidade_prioridade_total)
        """

        n = len(order)
        if n == 0:
            return 0.0, [], {}, 0.0

        # 1) Programação dinâmica (cálculo de custos e escolhas de veículos por segmento)
        dp_cost, prev_idx, vehicle_at = FitnessFunction._compute_dp(
            order, deposito, fleet
        )

        # Caso inviável (autonomia), aplicar penalidade gigante
        if dp_cost[-1] == inf:
            return FitnessFunction.BIG_PENALTY, [], {}, 0.0

        # 2) Reconstruir rotas e uso por tipo de veículo
        routes, usage, split_sequences = FitnessFunction._reconstruct_routes(
            order, prev_idx, vehicle_at
        )

        # 3) Penalidades (excesso de frota por tipo e prioridade tardia)
        penalties_total, weighted_priority_penalty = FitnessFunction._compute_penalties(
            usage, split_sequences, fleet
        )

        # 4) Custo final
        total_cost = dp_cost[-1] + penalties_total
        return total_cost, routes, usage, weighted_priority_penalty

    # ------------------------- Helpers privados -------------------------
    @staticmethod
    def _compute_dp(
        order: List, depot: DeliveryPoint, fleet: List[VehicleType]
    ) -> Tuple[List[float], List[int], List[Optional[VehicleType]]]:
        """
        Calcula a solução ótima de particionamento de rota usando programação dinâmica.

        Algoritmo:
        - Para cada posição j, calcula o menor custo para atender pontos [0:j]
        - Testa todos os cortes possíveis i < j, considerando segmento [i:j]
        - Para cada segmento, escolhe o veículo mais econômico que atende a autonomia
        - Aplica otimização early-break quando distância > maior autonomia disponível

        Complexidade: O(n² * |fleet|) onde n = número de pontos

        Args:
            order: Sequência de pontos de entrega a serem particionados
            depot: Ponto do depósito para cálculo de distâncias roundtrip
            fleet: Frota disponível com especificações de autonomia e custo

        Returns:
            Tupla com:
            - dp_cost: array de custos mínimos para cada posição [0..n]
            - prev_idx: array de índices de corte anterior para reconstrução
            - vehicle_at: array de veículos escolhidos para cada segmento
        """

        n = len(order)
        dp_cost, prev_idx, vehicle_at = FitnessFunction._initialize_dp_arrays(n)

        # Cache de distâncias e informações da frota para otimização
        distance_cache, max_autonomy = FitnessFunction._setup_dp_optimization(fleet)

        # Função auxiliar para obter distância com cache
        def get_cached_distance(start_idx: int, end_idx: int) -> float:
            return FitnessFunction._get_cached_roundtrip_distance(
                start_idx, end_idx, order, depot, distance_cache
            )

        # Programação dinâmica: testar todos os cortes possíveis
        for i in range(n):
            if dp_cost[i] == inf:
                continue  # Estado inalcançável

            for j in range(i + 1, n + 1):
                # Otimização: parar se distância já excede maior autonomia
                segment_distance = get_cached_distance(i, j)
                if segment_distance > max_autonomy:
                    break

                # Encontrar veículo mais econômico para este segmento
                best_vehicle = FitnessFunction._find_cheapest_vehicle(
                    segment_distance, fleet
                )
                if best_vehicle is None:
                    continue

                # Atualizar solução se encontrou custo menor
                candidate_cost = dp_cost[i] + (
                    best_vehicle.cost_per_km * segment_distance
                )
                if candidate_cost < dp_cost[j]:
                    dp_cost[j] = candidate_cost
                    prev_idx[j] = i
                    vehicle_at[j] = best_vehicle

        return dp_cost, prev_idx, vehicle_at

    @staticmethod
    def _initialize_dp_arrays(
        n: int,
    ) -> Tuple[List[float], List[int], List[Optional[VehicleType]]]:
        """Inicializa arrays da programação dinâmica com valores padrão."""
        dp_cost = [inf] * (n + 1)
        prev_idx = [-1] * (n + 1)
        vehicle_at = [None] * (n + 1)
        dp_cost[0] = 0.0  # Custo zero para o estado inicial
        return dp_cost, prev_idx, vehicle_at

    @staticmethod
    def _setup_dp_optimization(
        fleet: List[VehicleType],
    ) -> Tuple[Dict[Tuple[int, int], float], float]:
        """Configura otimizações para o algoritmo de programação dinâmica."""
        distance_cache = {}
        max_autonomy = max((vehicle.autonomy for vehicle in fleet), default=0.0)
        return distance_cache, max_autonomy

    @staticmethod
    def _get_cached_roundtrip_distance(
        start_idx: int,
        end_idx: int,
        order: List,
        depot: DeliveryPoint,
        cache: Dict[Tuple[int, int], float],
    ) -> float:
        """Obtém distância roundtrip com cache para evitar recálculos."""
        cache_key = (start_idx, end_idx)
        if cache_key in cache:
            return cache[cache_key]

        segment = order[start_idx:end_idx]
        distance = FitnessFunction._roundtrip_distance(segment, depot)
        cache[cache_key] = distance
        return distance

    @staticmethod
    def _find_cheapest_vehicle(
        distance: float, fleet: List[VehicleType]
    ) -> Optional[VehicleType]:
        """Encontra o veículo mais econômico que pode percorrer a distância especificada."""
        best_vehicle = None
        lowest_cost = inf

        for vehicle in fleet:
            if distance <= vehicle.autonomy:
                cost = vehicle.cost_per_km * distance
                if cost < lowest_cost:
                    lowest_cost = cost
                    best_vehicle = vehicle

        return best_vehicle

    @staticmethod
    def _reconstruct_routes(
        order: List, prev_idx: List[int], vehicle_at: List[Optional[VehicleType]]
    ) -> Tuple[List[Route], Dict[str, int], List[List[DeliveryPoint]]]:
        """
        Reconstrói as rotas otimizadas a partir da solução da programação dinâmica.

        Processo:
        1. Segue os índices anteriores (prev_idx) de trás para frente
        2. Extrai cada segmento de rota [i:j]
        3. Cria objeto Route e associa o veículo escolhido
        4. Contabiliza uso de cada tipo de veículo
        5. Inverte as listas para ordem correta (primeiro -> último)

        Args:
            order: Sequência original de pontos de entrega
            prev_idx: Array de índices de corte da programação dinâmica
            vehicle_at: Array de veículos escolhidos para cada segmento

        Returns:
            Tupla com:
            - routes: Lista de objetos Route otimizados
            - usage: Contagem de uso por tipo de veículo {nome: quantidade}
            - split_sequences: Sequências de pontos para cálculo de penalidades
        """

        routes = []
        vehicle_usage = {}
        split_sequences = []

        # Reconstrução reversa: do final para o início
        current_pos = len(order)
        while current_pos > 0:
            # Obter segmento atual
            previous_pos = prev_idx[current_pos]
            segment_points = order[previous_pos:current_pos]
            assigned_vehicle = vehicle_at[current_pos]

            # Criar e configurar rota
            route = Route(segment_points[:])
            FitnessFunction._assign_vehicle_to_route(route, assigned_vehicle)

            # Acumular dados
            routes.append(route)
            split_sequences.append(segment_points)
            vehicle_usage[assigned_vehicle.name] = (
                vehicle_usage.get(assigned_vehicle.name, 0) + 1
            )

            # Mover para segmento anterior
            current_pos = previous_pos

        # Corrigir ordem (primeiro segmento deve vir primeiro)
        routes.reverse()
        split_sequences.reverse()

        return routes, vehicle_usage, split_sequences

    @staticmethod
    def _assign_vehicle_to_route(route: Route, vehicle: VehicleType) -> None:
        """
        Associa um veículo a uma rota usando o método disponível.

        Tenta primeiro o método assign_vehicle, depois atributo vehicle_type.
        Fallback silencioso se nenhum método estiver disponível.
        """
        if hasattr(route, "assign_vehicle"):
            route.assign_vehicle(vehicle.name)
        else:
            try:
                route.vehicle_type = vehicle.name
            except Exception:
                # Fallback silencioso: alguns objetos Route podem não suportar
                pass

    @staticmethod
    def _compute_penalties(
        vehicle_usage: Dict[str, int],
        split_sequences: List[List[DeliveryPoint]],
        fleet: List[VehicleType],
    ) -> Tuple[float, float]:
        """
        Calcula penalidades por violações de restrições da frota e prioridades.

        Tipos de penalidades:
        1. Excesso de frota: quando usa mais veículos de um tipo do que disponível
        2. Prioridade tardia: produtos prioritários entregues em posições tardias

        Estratégia de penalização:
        - Excesso de frota: BIG_PENALTY escalado por quantidade excedente
        - Prioridade: posição relativa no segmento * prioridade * peso_configurável

        Args:
            vehicle_usage: Uso real de cada tipo de veículo
            split_sequences: Sequências de pontos para análise de prioridade
            fleet: Especificações da frota (capacidades disponíveis)

        Returns:
            Tupla com:
            - penalty_total: penalidade total acumulada
            - weighted_priority_penalty: penalidade de prioridade ponderada
        """

        total_penalty = 0.0

        # 1. Penalidade por excesso de frota
        fleet_penalty = FitnessFunction._calculate_fleet_excess_penalty(
            vehicle_usage, fleet
        )
        total_penalty += fleet_penalty

        # 2. Penalidade por prioridade tardia
        priority_penalty = FitnessFunction._calculate_priority_penalty(split_sequences)
        total_penalty += priority_penalty

        # 3. Limite global de veículos: penaliza se exceder (se configurado)
        max_allowed = FitnessFunction.MAX_VEHICLES_TOTAL
        if max_allowed is not None:
            total_used = sum(vehicle_usage.values()) if vehicle_usage else 0
            if total_used > max_allowed:
                excess = total_used - max_allowed
                total_penalty += excess * FitnessFunction.BIG_PENALTY
                FitnessFunction.logger.debug(
                    "Penalidade por exceder limite global de veículos: usado=%d, limite=%d, excesso=%d",
                    total_used, max_allowed, excess,
                )

        return total_penalty, priority_penalty

    @staticmethod
    def _calculate_fleet_excess_penalty(
        usage: Dict[str, int], fleet: List[VehicleType]
    ) -> float:
        """
        Calcula penalidade por usar mais veículos do que disponível.

        Fórmula: (quantidade_usada - quantidade_disponível) * BIG_PENALTY * 0.01
        """
        penalty = 0.0
        fleet_capacity = {vehicle.name: vehicle.count for vehicle in fleet}

        for vehicle_type, used_count in usage.items():
            available_count = fleet_capacity.get(vehicle_type, 0)
            if used_count > available_count:
                excess = used_count - available_count
                penalty += excess * FitnessFunction.BIG_PENALTY * 0.01

        return penalty

    @staticmethod
    def _calculate_priority_penalty(
        split_sequences: List[List[DeliveryPoint]],
    ) -> float:
        """
        Calcula penalidade por entregas prioritárias em posições tardias.

        Para cada segmento:
        - Produtos com maior prioridade devem ser entregues primeiro
        - Penalidade = prioridade * (posição_relativa_no_segmento)
        - Posição 0 = sem penalidade, posição final = penalidade máxima
        """
        PRIORITY_WEIGHT = 2.0  # Fator de ajuste da penalidade
        priority_penalty_acc = 0.0

        for segment in split_sequences:
            segment_length = len(segment)
            if segment_length <= 1:
                continue  # Sem penalidade para segmentos unitários

            # Calcular penalidade para cada ponto no segmento
            for position, delivery_point in enumerate(segment):
                product = getattr(delivery_point, "product", None)
                priority_level = getattr(product, "priority", 0.0) if product else 0.0

                # Posição relativa: 0.0 (primeira) a 1.0 (última)
                relative_position = position / (segment_length - 1)
                priority_penalty_acc += priority_level * relative_position

        return priority_penalty_acc * PRIORITY_WEIGHT

    @staticmethod
    @log_performance
    def calculate_fitness_with_fleet(
        route: Route, deposito, fleet: List[VehicleType]
    ) -> Tuple[float, List[Route], Dict[str, int]]:
        """
        Calcula o fitness de uma rota considerando múltiplos tipos de veículos (VRP).

        Estratégia:
        - Divide a rota em segmentos otimizados para diferentes tipos de veículos
        - Escolhe o veículo mais econômico que atende a autonomia de cada segmento
        - Aplica penalidades por excesso de frota e prioridade de entrega
        - Retorna fitness invertido (1/custo_total) para maximização no AG

        Args:
            route: Rota com pontos de entrega a serem otimizados
            deposito: Ponto do depósito (origem/destino)
            fleet: Lista de tipos de veículos disponíveis com suas especificações

        Returns:
            Tupla contendo:
            - fitness: valor de fitness (1/custo_total, maior é melhor)
            - routes: lista de rotas otimizadas por veículo
            - usage: dicionário com uso de cada tipo de veículo {tipo: quantidade}

        Raises:
            Retorna fitness 0.0 para soluções inviáveis (autonomia insuficiente)
        """

        # Validação de entrada
        delivery_points = getattr(route, "delivery_points", None)
        if not delivery_points:
            FitnessFunction.logger.warning("Rota vazia para cálculo com frota.")
            return 0.0, [], {}

        # Otimização de rota com escolha de veículos
        total_cost, optimized_routes, vehicle_usage, priority_penalty = (
            FitnessFunction._split_with_vehicle_choice(delivery_points, deposito, fleet)
        )

        # Se custo indica inviabilidade, logar motivo(s) antes de retornar
        if FitnessFunction._is_solution_infeasible(total_cost):
            reasons = FitnessFunction._infer_infeasibility_reasons(
                delivery_points=delivery_points,
                deposito=deposito,
                fleet=fleet,
                usage=vehicle_usage if vehicle_usage else None,
            )
            FitnessFunction.logger.warning(
                "Solução inviável (autonomia/frota). Motivo(s): %s. Aplicando penalidade.",
                "; ".join(reasons) if reasons else "não determinado",
            )
            return 0.0, [], {}

        FitnessFunction._log_solution_details(
            total_cost, optimized_routes, vehicle_usage, priority_penalty
        )

        fitness = FitnessFunction._calculate_fitness_score(total_cost)
        return fitness, optimized_routes, vehicle_usage

    @staticmethod
    def _is_solution_infeasible(total_cost: float) -> bool:
        """Verifica se a solução é inviável baseada no custo total."""
        return total_cost >= FitnessFunction.BIG_PENALTY

    @staticmethod
    def _log_solution_details(
        total_cost: float, routes: List[Route], usage: Dict[str, int], penalty: float
    ) -> None:
        """Registra detalhes da solução para debugging e monitoramento."""
        FitnessFunction.logger.debug(
            "VRP Fleet -> custo_total: %.3f, rotas: %d, uso_veiculos: %s, penalidade_prioridade: %.3f",
            total_cost,
            len(routes),
            usage,
            penalty,
        )

    @staticmethod
    def _calculate_fitness_score(total_cost: float) -> float:
        """Calcula o score de fitness invertendo o custo (maior fitness = melhor solução)."""
        return 1.0 / total_cost if total_cost > 0 else 0.0

    @staticmethod
    def _infer_infeasibility_reasons(
        delivery_points: List[DeliveryPoint],
        deposito: DeliveryPoint,
        fleet: List[VehicleType],
        usage: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """
        Deduz razões prováveis para uma solução inviável de VRP.

        Regras:
        - Se houver uso de veículos e o limite global estiver configurado, acusa excesso.
        - Se não for excesso global, verifica autonomia: pontos cuja ida-e-volta
          (depósito -> ponto -> depósito) excedem a autonomia máxima disponível.
        - Considera também casos de frota vazia ou autonomia máxima não positiva.

        Retorna:
            Lista de mensagens de motivo para logging.
        """
        reasons: List[str] = []

        # 1) Limite global de veículos excedido
        max_allowed = FitnessFunction.MAX_VEHICLES_TOTAL
        if usage and max_allowed is not None:
            total_used = sum(usage.values())
            if total_used > max_allowed:
                reasons.append(
                    f"limite global de veículos excedido (usado={total_used}, limite={max_allowed})"
                )

        # 2) Frota vazia ou autonomia inválida
        if not fleet:
            reasons.append("frota vazia (nenhum veículo disponível)")
            return reasons

        max_autonomy = max((v.autonomy for v in fleet), default=0.0)
        if max_autonomy <= 0:
            reasons.append("autonomia máxima da frota é zero ou negativa")
            return reasons

        # 3) Autonomia insuficiente para pontos individuais (segmentos mínimos)
        #    Se qualquer ponto isolado requer roundtrip acima da autonomia máxima, é inviável.
        offending: List[float] = []
        for dp in delivery_points:
            dist = FitnessFunction._roundtrip_distance([dp], deposito)
            if dist > max_autonomy:
                offending.append(dist)

        if offending:
            worst = max(offending)
            reasons.append(
                f"{len(offending)} ponto(s) sem veículo com autonomia suficiente "
                f"(maior distância necessária={worst:.1f} km, autonomia máx={max_autonomy:.1f} km)"
            )

        return reasons
