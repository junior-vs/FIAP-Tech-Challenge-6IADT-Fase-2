from typing import List, Tuple, Optional
from app_logging import get_logger
from route import Route
from delivery_point import DeliveryPoint
from selection_functions import Selection
from crossover_function import Crossover
from mutation_function import Mutation
from fitness_function import FitnessFunction


class GeneticEngine:
    """
    Encapsula o processo do Algoritmo Genético (AG) desacoplado da UI.

    Responsabilidades:
    - Manter população e parâmetros do AG
    - Executar seleção, crossover, mutação
    - Calcular fitness (TSP ou VRP com frota)
    - Rastrear melhor solução e histórico
    """

    def __init__(
        self,
        population_size: int = 50,
        selection_method: str = "roulette",
        crossover_method: str = "pmx",
        mutation_method: str = "swap",
        elitism: bool = True,
        use_fleet: bool = True,
    ) -> None:
        self.logger = get_logger(__name__)

        # Parâmetros do AG
        self.population_size = population_size
        self.selection_method = selection_method
        self.crossover_method = crossover_method
        self.mutation_method = mutation_method
        self.elitism = elitism
        self.use_fleet = use_fleet

        # Estado
        self.delivery_points: List[DeliveryPoint] = []
        self.population: List[Route] = []
        self.current_generation: int = 0
        self.best_route: Optional[Route] = None
        self.best_fitness: float = 0.0
        self.fitness_history: List[float] = []
        self.mean_fitness_history: List[float] = []

        # VRP
        self.depot: Optional[DeliveryPoint] = None
        self.fleet = None

        # Caches
        self._selection_method_cache = {}
        self._crossover_method_cache = {}
        self._mutation_method_cache = {}

    # ---------- Config ----------
    def set_delivery_points(self, points: List[DeliveryPoint]) -> None:
        self.delivery_points = list(points)

    def set_vrp_context(self, depot: Optional[DeliveryPoint], fleet) -> None:
        self.depot = depot
        self.fleet = fleet

    def clear_caches(self) -> None:
        self._selection_method_cache.clear()
        self._crossover_method_cache.clear()
        self._mutation_method_cache.clear()

    # ---------- Operadores ----------
    def initialize_population(self) -> None:
        if not self.delivery_points:
            self.logger.warning("Sem pontos de entrega para inicializar população")
            self.population = []
            return
        base = list(self.delivery_points)
        self.population = []
        import random
        for _ in range(self.population_size):
            shuffled = base.copy()
            random.shuffle(shuffled)
            self.population.append(Route(shuffled))

    def _select(self, population: List[Route], fitness_scores: List[float]) -> List[Route]:
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            self.logger.warning("Total de fitness zero, copiando população.")
            return population.copy()
        if self.selection_method not in self._selection_method_cache:
            if self.selection_method == "roulette":
                self._selection_method_cache[self.selection_method] = Selection.roulette
            elif self.selection_method == "tournament":
                self._selection_method_cache[self.selection_method] = (
                    lambda pop, scores: Selection.tournament_refined(pop, scores, tournament_size=3)
                )
            elif self.selection_method == "rank":
                self._selection_method_cache[self.selection_method] = Selection.rank
            else:
                self._selection_method_cache[self.selection_method] = Selection.roulette
        selection_func = self._selection_method_cache[self.selection_method]
        new_population = [selection_func(population, fitness_scores).copy() for _ in range(len(population))]
        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
            new_population[-1] = population[best_idx].copy()
        return new_population

    def _crossover(self, parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        if self.crossover_method not in self._crossover_method_cache:
            if self.crossover_method == "pmx":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_parcialmente_mapeado_pmx
            elif self.crossover_method == "ox1":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_ordenado_ox1
            elif self.crossover_method == "cx":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_de_ciclo_cx
            elif self.crossover_method == "kpoint":
                self._crossover_method_cache[self.crossover_method] = (
                    lambda p1, p2: Crossover.crossover_multiplos_pontos_kpoint(p1, p2, k=2)
                )
            elif self.crossover_method == "erx":
                self._crossover_method_cache[self.crossover_method] = (
                    lambda p1, p2: (Crossover.erx_crossover(p1, p2), Crossover.erx_crossover(p2, p1))
                )
            else:
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_parcialmente_mapeado_pmx
        return self._crossover_method_cache[self.crossover_method](parent1, parent2)

    def _mutate(self, route: Route) -> Route:
        if self.mutation_method not in self._mutation_method_cache:
            if self.mutation_method == "swap":
                self._mutation_method_cache[self.mutation_method] = Mutation.mutacao_por_troca
            elif self.mutation_method == "inverse":
                self._mutation_method_cache[self.mutation_method] = Mutation.mutacao_por_inversao
            elif self.mutation_method == "shuffle":
                self._mutation_method_cache[self.mutation_method] = Mutation.mutacao_por_embaralhamento
            else:
                self._mutation_method_cache[self.mutation_method] = Mutation.mutacao_por_troca
        return self._mutation_method_cache[self.mutation_method](route)

    # ---------- Execução de geração ----------
    def _calculate_fitness(self) -> Tuple[List[float], Optional[List]]:
        if self.use_fleet and self.depot is not None and self.fleet is not None:
            results = [
                FitnessFunction.calculate_fitness_with_fleet(ind, self.depot, self.fleet)
                for ind in self.population
            ]
            fitness_scores = [r[0] for r in results]
            for ind, (fit, routes, usage) in zip(self.population, results):
                ind.fitness = fit
                ind.routes = routes
                ind.vehicle_usage = usage
        else:
            results = None
            fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ind) for ind in self.population]
            for ind, fit in zip(self.population, fitness_scores):
                ind.fitness = fit
                if hasattr(ind, "routes"):
                    ind.routes = None
                if hasattr(ind, "vehicle_usage"):
                    ind.vehicle_usage = None
        return fitness_scores, results

    def _update_best(self, fitness_scores: List[float], results: Optional[List]) -> None:
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            old = self.best_fitness
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()
            if self.use_fleet and results:
                best_res = results[best_idx]
                self.best_route.routes = best_res[1]
                self.best_route.vehicle_usage = best_res[2]
            if old == 0 or (old > 0 and (max_fitness - old) / old > 0.1):
                self.logger.info(
                    f"Geração {self.current_generation}: Nova melhor fitness {max_fitness:.4f} (+{max_fitness - old:.4f})"
                )

    def _update_history(self, fitness_scores: List[float]) -> None:
        from numpy import mean
        max_fitness = max(fitness_scores)
        mean_fitness = float(mean(fitness_scores)) if fitness_scores else 0.0
        self.fitness_history.append(max_fitness)
        self.mean_fitness_history.append(mean_fitness)

    def _evolve(self, fitness_scores: List[float]) -> None:
        # Seleção
        self.population = self._select(self.population, fitness_scores)

        # Crossover e Mutação
        new_population: List[Route] = []
        pop_len = len(self.population)
        for i in range(0, pop_len, 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % pop_len]
            child1, child2 = self._crossover(parent1, parent2)
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            new_population.extend([child1, child2])
        self.population = new_population[: self.population_size]

    def run_generation(self) -> Tuple[List[float], Optional[List]]:
        """Executa uma geração completa do AG."""
        if not self.population:
            self.logger.warning("População vazia, inicializando...")
            self.initialize_population()

        fitness_scores, results = self._calculate_fitness()
        self._update_best(fitness_scores, results)
        self._update_history(fitness_scores)
        if self.current_generation % 10 == 0:
            self.logger.info(f"Checkpoint: geração {self.current_generation}")
        self._evolve(fitness_scores)
        self.current_generation += 1
        return fitness_scores, results
