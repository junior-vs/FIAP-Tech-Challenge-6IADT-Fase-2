from typing import Tuple, Optional, List, Dict, Set
import random
from route import Route
from delivery_point import DeliveryPoint

# === ETAPA 1: IMPLEMENTAÇÃO DOS OPERADORES DE CROSSOVER ===

class Crossover:

    @staticmethod
    def order_crossover(parent1: Route, parent2: Route) -> Route:
        """Order Crossover (OX). Retorna um filho. Se tamanho < 2, retorna cópia do pai."""
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy()

        start_index, end_index = sorted(random.sample(range(size), 2))
        child_segment = parent_a_points[start_index:end_index]
        remaining_genes = [gene for gene in parent_b_points if gene not in child_segment]
        child = [None] * size
        child[start_index:end_index] = child_segment
        fill_index = 0
        for i in range(size):
            if child[i] is None:
                child[i] = remaining_genes[fill_index]
                fill_index += 1
        return Route(child)

    @staticmethod
    def erx_crossover(parent1: Route, parent2: Route) -> Route:
        """Edge Recombination Crossover (ERX). Usa índices; retorna cópia se trivial."""
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy()

        def build_edge_map(points_a: List[DeliveryPoint], points_b: List[DeliveryPoint]) -> Dict[int, Set[int]]:
            edge_map: Dict[int, Set[int]] = {i: set() for i in range(len(points_a))}
            for points in (points_a, points_b):
                for i in range(len(points)):
                    left = (i - 1) % len(points)
                    right = (i + 1) % len(points)
                    edge_map[i].update([left, right])
            return edge_map

        def select_next(current: int, edge_map: Dict[int, Set[int]], visited: List[int]) -> Optional[int]:
            for neighbor in edge_map.get(current, []):
                edge_map[neighbor].discard(current)
            edge_map.pop(current, None)

            candidates = [(node, len(edge_map[node])) for node in edge_map if node not in visited]
            if not candidates:
                return None
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        edge_map = build_edge_map(parent_a_points, parent_b_points)
        current = random.randint(0, len(parent_a_points) - 1)
        visited = [current]

        while len(visited) < len(parent_a_points):
            next_idx = select_next(current, edge_map, visited)
            if next_idx is None:
                remaining = [i for i in range(len(parent_a_points)) if i not in visited]
                next_idx = random.choice(remaining)
            visited.append(next_idx)
            current = next_idx

        child_points = [parent_a_points[i] for i in visited]
        return Route(child_points)

    @staticmethod
    def crossover_ordenado_ox1(parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy(), parent2.copy()

        child1, child2 = [None] * size, [None] * size
        start, end = sorted(random.sample(range(size), 2))
        child1[start:end] = parent_a_points[start:end]
        child2[start:end] = parent_b_points[start:end]

        parent2_genes = [item for item in parent_b_points if item not in child1]
        idx = 0
        for i in range(size):
            if child1[i] is None:
                child1[i] = parent2_genes[idx]
                idx += 1

        parent1_genes = [item for item in parent_a_points if item not in child2]
        idx = 0
        for i in range(size):
            if child2[i] is None:
                child2[i] = parent1_genes[idx]
                idx += 1

        return Route(child1), Route(child2)

    @staticmethod
    def crossover_parcialmente_mapeado_pmx(parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy(), parent2.copy()
        child1 = parent_a_points[:]
        child2 = parent_b_points[:]
        start, end = sorted(random.sample(range(size), 2))

        mapping1 = {}
        mapping2 = {}
        for i in range(start, end):
            child1[i], child2[i] = parent_b_points[i], parent_a_points[i]
            mapping1[child1[i]] = child2[i]
            mapping2[child2[i]] = child1[i]

        def repair(child, mapping):
            for i in range(size):
                if not (start <= i < end):
                    val = child[i]
                    while val in child[start:end]:
                        val = mapping.get(val, val)
                    child[i] = val
            return child

        child1 = repair(child1, mapping2)
        child2 = repair(child2, mapping1)
        return Route(child1), Route(child2)

    @staticmethod
    def crossover_de_ciclo_cx(parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy(), parent2.copy()

        child1, child2 = [None] * size, [None] * size
        visited = [False] * size
        for i in range(size):
            if visited[i]:
                continue
            cycle = []
            idx = i
            while not visited[idx]:
                cycle.append(idx)
                visited[idx] = True
                value = parent_b_points[idx]
                idx = parent_a_points.index(value)
            for j in cycle:
                child1[j] = parent_a_points[j]
                child2[j] = parent_b_points[j]

        for k in range(size):
            if child1[k] is None:
                child1[k] = parent_b_points[k]
            if child2[k] is None:
                child2[k] = parent_a_points[k]

        return Route(child1), Route(child2)

    @staticmethod
    def crossover_multiplos_pontos_kpoint(parent1: Route, parent2: Route, k: int = 2) -> Tuple[Route, Route]:
        parent_a_points = parent1.delivery_points
        parent_b_points = parent2.delivery_points
        size = len(parent_a_points)
        if size < 2:
            return parent1.copy(), parent2.copy()

        assert 1 <= k < size, "k deve ser >=1 e < tamanho"
        child1, child2 = [None] * size, [None] * size
        points = sorted(random.sample(range(1, size), k))
        all_points = [0] + points + [size]

        for i in range(len(all_points) - 1):
            start, end = all_points[i], all_points[i+1]
            if i % 2 == 0:
                child1[start:end] = parent_a_points[start:end]
                child2[start:end] = parent_b_points[start:end]

        def fill_gaps(child, other_points):
            other_genes = [g for g in other_points if g not in child]
            gi = 0
            for i in range(size):
                if child[i] is None:
                    child[i] = other_genes[gi]
                    gi += 1
            return child

        child1 = fill_gaps(child1, parent_b_points)
        child2 = fill_gaps(child2, parent_a_points)
        return Route(child1), Route(child2)

