import sys
from typing import List, Tuple
import random
import math
import os
import pygame
import numpy as np
import logging

# Configurar paths para imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../domain')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../functions')))

# Imports dos módulos do projeto
from delivery_point import DeliveryPoint
from draw_functions import DrawFunctions
from route import Route
from crossover_function import Crossover
from mutation_function import Mutation
from selection_functions import Selection
from fitness_function import FitnessFunction
from ui_layout import UILayout
from app_logging import configurar_logging, get_logger
from product import Product

try:
    from vehicle import VehicleType, default_fleet 
except Exception:
    class VehicleType:
        def __init__(self, name: str, count: int, autonomy: float, cost_per_km: float = 1.0):
            self.name = name
            self.count = int(count)
            self.autonomy = float(autonomy)
            self.cost_per_km = float(cost_per_km)
    def default_fleet():
        return [
            VehicleType("Moto", 5, 80.0, 1.0),
            VehicleType("Van",  2, 250.0, 1.4)
        ]

# Inicializar pygame
pygame.init()

# Usar configurações centralizadas do layout
WINDOW_WIDTH = UILayout.WINDOW_WIDTH
WINDOW_HEIGHT = UILayout.WINDOW_HEIGHT

# Importar cores do layout centralizado
WHITE = UILayout.get_color('white')
BLACK = UILayout.get_color('black')
BLUE = UILayout.get_color('blue')
RED = UILayout.get_color('red')
GREEN = UILayout.get_color('green')
GRAY = UILayout.get_color('gray')
LIGHT_GRAY = UILayout.get_color('light_gray')


class TSPGeneticAlgorithm:
    def __init__(self):
        # Configurar logger para esta classe
        self.logger = get_logger(__name__)
        self.logger.info("Inicializando aplicação TSP Genetic Algorithm")
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TSP - Genetic Algorithm Approach")
        self.clock = pygame.time.Clock()
        
        # Usar fontes centralizadas
        fonts = UILayout.create_fonts()
        self.font = fonts['large']
        self.small_font = fonts['medium']
        
        # Variáveis do algoritmo
        self.delivery_points: List[DeliveryPoint] = []
        self.distance_matrix = None
        self.population = []  # will hold List[Route] after initialization
        self.population_size = 50
        self.max_generations = 100
        self.mutation_method = "swap"  # Default method: swap
        self.crossover_method = "pmx"  # Default method: PMX
        self.selection_method = "roulette"  # Default method: roulette
        self.elitism = True
        self.running_algorithm = False
        self.current_generation = 0
        self.best_route = None
        self.best_fitness = 0
        self.fitness_history = []
        self.mean_fitness_history = []
        self.priority_percentage = 20  # valor default, pode ser alterado via interface

        # --- VRP (múltipla frota) ---
        self.use_fleet = True
        self.fleet: List[VehicleType] = default_fleet()
        self.depot: DeliveryPoint = None 

        # Interface - usar layout centralizado
        self.ui_layout = UILayout()
        self.map_type = "random"  # "random", "circle", "custom"
        self.num_cities = 10
        self.buttons = UILayout.Buttons.create_button_positions()
        
        self.logger.info("Aplicação inicializada com sucesso")

    def _make_random_product(self, idx: int) -> Product:
        """Gera um produto válido aleatório respeitando as restrições e a procentagem de prioridade.

        - Cada lado <= 100 cm; soma <= 200 cm; peso <= 10000 g.
        """
        name = f"Produto-{idx}"
        weight = random.randint(100, 10_000)
        # Usa a porcentagem definida na interface
        if random.random() < (self.priority_percentage / 100):
            priority = round(random.uniform(0.1, 1.0), 2)
        else:
            priority = 0.0
        for _ in range(100):
            a = random.uniform(5.0, 100.0)
            b = random.uniform(5.0, 100.0)
            max_c = min(100.0, 200.0 - (a + b))
            if max_c > 5.0:
                c = random.uniform(5.0, max_c)
                dims = [a, b, c]
                random.shuffle(dims)
                try:
                    return Product(name=name, 
                                   weight=weight,
                                   length=dims[0], 
                                   width=dims[1], 
                                   height=dims[2], 
                                   priority=priority)
                except ValueError:
                    continue
        return Product(name=name, weight=min(weight, 10_000), length=100, width=50, height=50, priority=priority)

    # -------------------- DEPÓSITO --------------------
    def _compute_depot(self) -> DeliveryPoint:
        """Define o depósito no centro da área do mapa."""
        cx = UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH // 2
        cy = UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT // 2
        return DeliveryPoint(cx, cy, product=None)

    # -------------------- GERAÇÃO DE CIDADES --------------------
    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado usando configurações centralizadas."""
        self.logger.info(f"Gerando {num_cities} cidades usando mapa tipo '{map_type}'")
        self.delivery_points = []

        if map_type == "random":
            for i in range(num_cities):
                x = random.randint(UILayout.MapArea.RANDOM_MIN_X, UILayout.MapArea.RANDOM_MAX_X)
                y = random.randint(UILayout.MapArea.RANDOM_MIN_Y, UILayout.MapArea.RANDOM_MAX_Y)
                prod = self._make_random_product(i)
                self.delivery_points.append(DeliveryPoint(x, y, product=prod))

        elif map_type == "circle":
            center_x = UILayout.MapArea.CIRCLE_CENTER_X
            center_y = UILayout.MapArea.CIRCLE_CENTER_Y
            radius = UILayout.MapArea.CIRCLE_RADIUS
            for i in range(num_cities):
                angle = 2 * math.pi * i / num_cities
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                prod = self._make_random_product(i)
                self.delivery_points.append(DeliveryPoint(int(x), int(y), product=prod))

        elif map_type == "custom":
            self.logger.info("Modo customizado ativado - aguardando input do usuário")

        if self.delivery_points:
            self.calculate_distance_matrix()
            self.depot = self._compute_depot()
            self.logger.info(f"Geradas {len(self.delivery_points)} cidades com sucesso")
    
    def initialize_population(self):
        """Inicializa a população com cromossomos aleatórios"""
        self.population = []

        base = list(self.delivery_points)
        for _ in range(self.population_size):
            shuffled = base[:]
            random.shuffle(shuffled)
            self.population.append(Route(shuffled))
    
    def selection(self, population: List[Route], fitness_scores: List[float]) -> List[Route]:
        """Seleção usando métodos do selection_functions.py com suporte a diferentes algoritmos e elitismo."""
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return population.copy()

        new_population = []
        for _ in range(len(population)):
            if self.selection_method == "roulette":
                chosen = Selection.roulette(population, fitness_scores)
            elif self.selection_method == "tournament":
                chosen = Selection.tournament(population, fitness_scores, tournament_size=3)
            elif self.selection_method == "rank":
                chosen = Selection.rank(population, fitness_scores)
            else:
                chosen = Selection.roulette(population, fitness_scores)
            new_population.append(chosen.copy())

        # Elitismo
        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
            new_population[-1] = population[best_idx].copy()

        return new_population
    
    def crossover(self, parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        """Wrapper que usa as implementações de Crossover baseado no método selecionado."""
        if self.crossover_method == "pmx":
            return Crossover.crossover_parcialmente_mapeado_pmx(parent1, parent2)
        elif self.crossover_method == "ox1":
            return Crossover.crossover_ordenado_ox1(parent1, parent2)
        elif self.crossover_method == "cx":
            return Crossover.crossover_de_ciclo_cx(parent1, parent2)
        elif self.crossover_method == "kpoint":
            return Crossover.crossover_multiplos_pontos_kpoint(parent1, parent2, k=2)
        elif self.crossover_method == "erx":
            child1 = Crossover.erx_crossover(parent1, parent2)
            child2 = Crossover.erx_crossover(parent2, parent1)
            return child1, child2
        else:
            return Crossover.crossover_parcialmente_mapeado_pmx(parent1, parent2)
    
    def mutate(self, route: Route) -> Route:
        """Apply a mutation operator from Mutation module to a Route based on selected method."""
        if self.mutation_method == "swap":
            return Mutation.mutacao_por_troca(route)
        elif self.mutation_method == "inverse":
            return Mutation.mutacao_por_inversao(route)
        elif self.mutation_method == "shuffle":
            return Mutation.mutacao_por_embaralhamento(route)
        else:
            return Mutation.mutacao_por_troca(route)
    
    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    # -------------------- EXECUÇÃO DE UMA GERAÇÃO --------------------
    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        if not self.population:
            self.initialize_population()

        # ---- cálculo de fitness ----
        if self.use_fleet and self.depot is not None:
            # VRP
            results = [FitnessFunction.calculate_fitness_with_fleet(ind, self.depot, self.fleet)
                       for ind in self.population]
            fitness_scores = [r[0] for r in results]

            for ind, (fit, routes, usage) in zip(self.population, results):
                ind.fitness = fit
                ind.routes = routes
                ind.vehicle_usage = usage

        else:
            fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ind)
                              for ind in self.population]
            for ind, fit in zip(self.population, fitness_scores):
                ind.fitness = fit
                if hasattr(ind, "routes"): ind.routes = None
                if hasattr(ind, "vehicle_usage"): ind.vehicle_usage = None

        # Atualizar melhor rota
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            old_fitness = self.best_fitness
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()

            if self.use_fleet:
                best_res = results[best_idx]
                self.best_route.routes = best_res[1] 
                self.best_route.vehicle_usage = best_res[2]

            if old_fitness == 0 or (old_fitness > 0 and (max_fitness - old_fitness) / old_fitness > 0.1):
                self.logger.info(f"Geração {self.current_generation}: Nova melhor fitness {max_fitness:.4f} (+{max_fitness - old_fitness:.4f})")

        # Histórico
        self.fitness_history.append(max_fitness)
        mean_fitness = np.mean(fitness_scores)
        self.mean_fitness_history.append(mean_fitness)

        if self.current_generation % 10 == 0:
            self.logger.debug(f"Geração {self.current_generation}: Fitness média={mean_fitness:.4f}, Melhor={max_fitness:.4f}")

        # Seleção
        self.population = self.selection(self.population, fitness_scores)

        # Crossover e mutação
        new_population = []
        for i in range(0, len(self.population), 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % len(self.population)]
            child1, child2 = self.crossover(parent1, parent2)
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            new_population.extend([child1, child2])

        self.population = new_population[:self.population_size]
        self.current_generation += 1
      
    # -------------------- INPUT CUSTOM --------------------
    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas usando área definida no layout."""
        if self.map_type == "custom" and pos[0] > UILayout.MapArea.X:
            if (UILayout.MapArea.CITIES_X <= pos[0] <= UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH and
                UILayout.MapArea.CITIES_Y <= pos[1] <= UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT):
                prod = self._make_random_product(len(self.delivery_points))
                self.delivery_points.append(DeliveryPoint(pos[0], pos[1], product=prod))
                if len(self.delivery_points) > 1:
                    self.calculate_distance_matrix()
                self.depot = self._compute_depot()
    
    def handle_events(self):
        """Gerencia eventos do pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if self.buttons['generate_map'].collidepoint(pos) and not self.running_algorithm:
                    self.generate_cities(self.map_type, self.num_cities)

                elif self.buttons['run_algorithm'].collidepoint(pos) and not self.running_algorithm:
                    if self.delivery_points:
                        self.start_algorithm()

                elif self.buttons['stop_algorithm'].collidepoint(pos) and self.running_algorithm:
                    self.stop_algorithm()

                elif self.buttons['reset'].collidepoint(pos):
                    self.reset_algorithm()

                elif self.buttons['map_random'].collidepoint(pos):
                    self.map_type = "random"

                elif self.buttons['map_circle'].collidepoint(pos):
                    self.map_type = "circle"

                elif self.buttons['map_custom'].collidepoint(pos):
                    self.map_type = "custom"
                    self.delivery_points = []

                elif self.buttons['toggle_elitism'].collidepoint(pos):
                    self.elitism = not self.elitism

                elif 'selection_roulette' in self.buttons and \
                     self.buttons['selection_roulette'].collidepoint(pos):
                    if self.selection_method != "roulette":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → roulette")
                        self.selection_method = "roulette"
                elif 'selection_tournament' in self.buttons and \
                     self.buttons['selection_tournament'].collidepoint(pos):
                    if self.selection_method != "tournament":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → tournament")
                        self.selection_method = "tournament"
                elif 'selection_rank' in self.buttons and \
                     self.buttons['selection_rank'].collidepoint(pos):
                    if self.selection_method != "rank":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → rank")
                        self.selection_method = "rank"

                elif self.buttons['cities_minus'].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities > 3:
                        self.num_cities -= 1

                elif self.buttons['cities_plus'].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities < 50:
                        self.num_cities += 1

                elif self.buttons['mutation_swap'].collidepoint(pos):
                    self.mutation_method = "swap"
                elif self.buttons['mutation_inverse'].collidepoint(pos):
                    self.mutation_method = "inverse"
                elif self.buttons['mutation_shuffle'].collidepoint(pos):
                    self.mutation_method = "shuffle"

                elif self.buttons['crossover_pmx'].collidepoint(pos):
                    self.crossover_method = "pmx"
                elif self.buttons['crossover_ox1'].collidepoint(pos):
                    self.crossover_method = "ox1"
                elif self.buttons['crossover_cx'].collidepoint(pos):
                    self.crossover_method = "cx"
                elif self.buttons['crossover_kpoint'].collidepoint(pos):
                    self.crossover_method = "kpoint"
                elif self.buttons['crossover_erx'].collidepoint(pos):
                    self.crossover_method = "erx"

                # Slider de prioridade
                if self.buttons['priority_slider'].collidepoint(pos):
                    rect = self.buttons['priority_slider']
                    slider_x = rect.x + 120
                    slider_w = rect.width - 130
                    rel_x = min(max(pos[0] - slider_x, 0), slider_w)
                    pct = int((rel_x / slider_w) * 100)
                    self.priority_percentage = pct

                elif self.map_type == "custom":
                    self.handle_custom_input(pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.running_algorithm:
                    if self.delivery_points:
                        self.start_algorithm()
                elif event.key == pygame.K_ESCAPE:
                    if self.running_algorithm:
                        self.stop_algorithm()
                    else:
                        return False

        return True
    
    def start_algorithm(self):
        """Inicia o algoritmo genético"""
        if not self.delivery_points:
            self.logger.warning("Tentativa de iniciar algoritmo sem pontos de entrega")
            return
        
        # garante depósito
        if self.depot is None:
            self.depot = self._compute_depot()

        self.logger.info(f"Iniciando algoritmo genético com {len(self.delivery_points)} cidades")
        self.logger.info(f"Configurações: população={self.population_size}, gerações={self.max_generations}")
        self.logger.info(f"Métodos: seleção={self.selection_method}, crossover={self.crossover_method}, mutação={self.mutation_method}, elitismo={self.elitism}")
        if self.use_fleet:
            self.logger.info(f"VRP ativado | tipos de veículos: {[ (v.name, v.count, v.autonomy) for v in self.fleet ]}")
        
        self.running_algorithm = True
        self.current_generation = 0
        self.best_fitness = 0
        self.best_route = None
        self.fitness_history = []
        self.mean_fitness_history = []
        self.initialize_population()
    
    def stop_algorithm(self):
        """Para o algoritmo genético"""
        self.logger.info(f"Algoritmo interrompido na geração {self.current_generation}")
        if self.best_fitness > 0:
            self.logger.info(f"Melhor fitness alcançado: {self.best_fitness:.4f}")
        self.running_algorithm = False
    
    def reset_algorithm(self):
        """Reseta o algoritmo e limpa os dados"""
        self.logger.info("Resetando algoritmo e limpando dados")
        self.running_algorithm = False
        self.delivery_points = []
        self.population = []
        self.current_generation = 0
        self.best_fitness = 0
        self.best_route = None
        self.fitness_history = []
        self.mean_fitness_history = []
        self.depot = None
    
    def run(self):
        """Loop principal do programa"""
        self.logger.info("Iniciando loop principal da aplicação")
        running = True

        while running:
            running = self.handle_events()

            if self.running_algorithm and self.current_generation < self.max_generations:
                self.run_generation()

                if self.current_generation >= self.max_generations:
                    self.logger.info(f"Algoritmo finalizado após {self.max_generations} gerações")
                    self.logger.info(f"Melhor fitness final: {self.best_fitness:.4f}")
                    self.running_algorithm = False

            self.screen.fill(WHITE)

            # Área do mapa usando configurações centralizadas
            map_rect = (UILayout.MapArea.X, UILayout.MapArea.Y, UILayout.MapArea.WIDTH, UILayout.MapArea.HEIGHT)
            pygame.draw.rect(self.screen, WHITE, map_rect)
            pygame.draw.rect(self.screen, BLACK, map_rect, 2)

            # Desenhar interface via DrawFunctions
            DrawFunctions.draw_interface(self)

            # ---------------- Desenhar cidades/rotas ----------------
            if self.delivery_points:
                if self.use_fleet and self.depot is not None:
                    DrawFunctions.draw_cities(self)
                    DrawFunctions.draw_depot(self, self.depot)

                    if self.best_route and hasattr(self.best_route, "routes") and self.best_route.routes:
                        DrawFunctions.draw_vrp_solution(self, self.best_route.routes, self.depot)

                    if self.population and self.running_algorithm and hasattr(self.population[0], 'fitness'):
                        current_best = max(self.population, key=lambda ind: getattr(ind, 'fitness', 0))
                        if hasattr(current_best, "routes") and current_best.routes:
                            DrawFunctions.draw_vrp_solution(self, current_best.routes, self.depot, show_legend=False)

                else:
                    if self.best_route:
                        DrawFunctions.draw_route(self, self.best_route, RED, 3)

                    if self.population and self.running_algorithm:
                        fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(chrom) for chrom in self.population]
                        if fitness_scores:
                            best_idx = fitness_scores.index(max(fitness_scores))
                            current_best = self.population[best_idx]
                            DrawFunctions.draw_route(self, current_best, BLUE, 2)

                    DrawFunctions.draw_cities(self)

            if self.map_type == "custom" and not self.delivery_points and hasattr(UILayout, "SpecialElements"):
                instruction = self.font.render("Click on the map to add cities", True, BLACK)
                self.screen.blit(instruction, (UILayout.SpecialElements.CUSTOM_MESSAGE_X, 
                                               UILayout.SpecialElements.CUSTOM_MESSAGE_Y))

            pygame.display.flip()
            self.clock.tick(60)

        self.logger.info("Encerrando aplicação")
        pygame.quit()
        sys.exit()



if __name__ == "__main__":
    # Configurar sistema de logging usando módulo centralizado
    configurar_logging()
    
    # Criar logger para o módulo principal
    logger = get_logger(__name__)
    
    try:
        logger.info("=== Início da Aplicação TSP Genetic Algorithm ===")
        app = TSPGeneticAlgorithm()
        app.run()
        
    except Exception as e:
        logger.critical(f"Erro crítico na aplicação: {e}", exc_info=True)
        raise
    finally:
        logger.info("=== Fim da Aplicação ===")
