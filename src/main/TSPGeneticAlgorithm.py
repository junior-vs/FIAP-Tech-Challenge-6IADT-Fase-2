import sys
from typing import List, Tuple
import os
import pygame
import numpy as np

# Configurar paths para imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../domain')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../functions')))

# Imports dos módulos do projeto
from delivery_point import DeliveryPoint
from route import Route
from draw_functions import DrawFunctions
from crossover_function import Crossover
from mutation_function import Mutation
from selection_functions import Selection
from fitness_function import FitnessFunction
from ui_layout import UILayout
from app_logging import get_logger
from product import Product
from population_factory import PopulationFactory

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
    @staticmethod
    def log_performance(func):
        """Decorator para medir e logar o tempo de execução de métodos críticos."""
        import time
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start = time.perf_counter()
            logger.debug(f"[PERF] Iniciando '{func.__name__}'")
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"[PERF] '{func.__name__}' executado em {elapsed:.2f} ms")
            return result
        return wrapper
    
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
        
        # Cache para operações frequentes (performance)
        self._selection_method_cache = {}
        self._crossover_method_cache = {}
        self._mutation_method_cache = {}
        self._fitness_cache = {}
        
        # Factory para população
        self.population_factory = PopulationFactory()
        
        self.logger.info("Aplicação inicializada com sucesso")
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

    # -------------------- GERAÇÃO DE CIDADES --------------------
    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado usando configurações centralizadas."""
        self.logger.info(f"Gerando {num_cities} cidades usando mapa tipo '{map_type}'")
        self.delivery_points = []

        if map_type == "random":
            self.delivery_points = DeliveryPoint.generate_random_points(
                num_cities,
                UILayout.MapArea.RANDOM_MIN_X,
                UILayout.MapArea.RANDOM_MAX_X,
                UILayout.MapArea.RANDOM_MIN_Y,
                UILayout.MapArea.RANDOM_MAX_Y,
                self.priority_percentage
            )

        elif map_type == "circle":
            self.delivery_points = DeliveryPoint.generate_circle_points(
                num_cities,
                UILayout.MapArea.CIRCLE_CENTER_X,
                UILayout.MapArea.CIRCLE_CENTER_Y,
                UILayout.MapArea.CIRCLE_RADIUS,
                self.priority_percentage
            )

        elif map_type == "custom":
            self.logger.info("Modo customizado ativado - aguardando input do usuário")

        if self.delivery_points:
            self.calculate_distance_matrix()
            cx = UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH // 2
            cy = UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT // 2
            self.depot = DeliveryPoint.create_depot(cx, cy)
            self.logger.info(f"Geradas {len(self.delivery_points)} cidades com sucesso")
    
    def initialize_population(self):
        """Inicializa a população usando factory pattern."""
        self.population = self.population_factory.create_initial_population(
            self.delivery_points, self.population_size
        )
    
  #  @log_performance
    def selection(self, population: List[Route], fitness_scores: List[float]) -> List[Route]:
        """Seleção otimizada usando cache para métodos."""
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            self.logger.warning("Total de fitness zero, copiando população.")
            return population.copy()

        # Cache do método de seleção para evitar verificações repetidas
        if self.selection_method not in self._selection_method_cache:
            if self.selection_method == "roulette":
                self._selection_method_cache[self.selection_method] = Selection.roulette
            elif self.selection_method == "tournament":
                self._selection_method_cache[self.selection_method] = lambda pop, scores: Selection.tournament_refined(pop, scores, tournament_size=3)
            elif self.selection_method == "rank":
                self._selection_method_cache[self.selection_method] = Selection.rank
            else:
                self._selection_method_cache[self.selection_method] = Selection.roulette
        
        selection_func = self._selection_method_cache[self.selection_method]
        
        # Gerar nova população
        new_population = [selection_func(population, fitness_scores).copy() 
                         for _ in range(len(population))]

        # Elitismo otimizado
        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
            new_population[-1] = population[best_idx].copy()

        return new_population
    
  #  @log_performance
    def crossover(self, parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        """Crossover otimizado com cache para métodos."""
        # Cache do método de crossover
        if self.crossover_method not in self._crossover_method_cache:
            if self.crossover_method == "pmx":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_parcialmente_mapeado_pmx
            elif self.crossover_method == "ox1":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_ordenado_ox1
            elif self.crossover_method == "cx":
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_de_ciclo_cx
            elif self.crossover_method == "kpoint":
                self._crossover_method_cache[self.crossover_method] = lambda p1, p2: Crossover.crossover_multiplos_pontos_kpoint(p1, p2, k=2)
            elif self.crossover_method == "erx":
                self._crossover_method_cache[self.crossover_method] = lambda p1, p2: (Crossover.erx_crossover(p1, p2), Crossover.erx_crossover(p2, p1))
            else:
                self._crossover_method_cache[self.crossover_method] = Crossover.crossover_parcialmente_mapeado_pmx
        
        return self._crossover_method_cache[self.crossover_method](parent1, parent2)
    
   # @log_performance
    def mutate(self, route: Route) -> Route:
        """Mutação otimizada com cache para métodos."""
        # Cache do método de mutação
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
    
    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    # -------------------- EXECUÇÃO DE UMA GERAÇÃO --------------------
    @log_performance
    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        self.logger.info(f"Executando geração {self.current_generation}")
        if not self.population:
            self.logger.warning("População vazia, inicializando...")
            self.initialize_population()

        # Calcular fitness de forma otimizada
        fitness_scores, results = self._calculate_fitness_optimized()
        
        # Atualizar melhor rota
        self._update_best_route(fitness_scores, results)
        
        # Atualizar histórico
        self._update_fitness_history(fitness_scores)
        
        # Checkpoint periódico
        if self.current_generation % 10 == 0:
            self.logger.info(f"Checkpoint: geração {self.current_generation}")

        # Evoluir população
        self._evolve_population(fitness_scores)
        
        self.current_generation += 1
    
    def _calculate_fitness_optimized(self) -> Tuple[List[float], List]:
        """Calcula fitness de forma otimizada com cache quando possível."""
        if self.use_fleet and self.depot is not None:
            # VRP - usar numpy para operações vectorizadas quando possível
            results = [FitnessFunction.calculate_fitness_with_fleet(ind, self.depot, self.fleet)
                       for ind in self.population]
            fitness_scores = [r[0] for r in results]
            # Atualizar atributos da população em lote
            for ind, (fit, routes, usage) in zip(self.population, results):
                ind.fitness = fit
                ind.routes = routes
                ind.vehicle_usage = usage
        else:
            # TSP simples
            results = None
            fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ind)
                              for ind in self.population]
            # Atualizar atributos em lote
            for ind, fit in zip(self.population, fitness_scores):
                ind.fitness = fit
                if hasattr(ind, "routes"): 
                    ind.routes = None
                if hasattr(ind, "vehicle_usage"): 
                    ind.vehicle_usage = None
        
        return fitness_scores, results
    
    def _update_best_route(self, fitness_scores: List[float], results: List) -> None:
        """Atualiza a melhor rota da geração."""
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            old_fitness = self.best_fitness
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()

            if self.use_fleet and results:
                best_res = results[best_idx]
                self.best_route.routes = best_res[1] 
                self.best_route.vehicle_usage = best_res[2]

            # Log apenas melhorias significativas (>10%)
            if old_fitness == 0 or (old_fitness > 0 and (max_fitness - old_fitness) / old_fitness > 0.1):
                self.logger.info(f"Geração {self.current_generation}: Nova melhor fitness {max_fitness:.4f} (+{max_fitness - old_fitness:.4f})")
    
    def _update_fitness_history(self, fitness_scores: List[float]) -> None:
        """Atualiza o histórico de fitness."""
        max_fitness = max(fitness_scores)
        mean_fitness = np.mean(fitness_scores)
        self.fitness_history.append(max_fitness)
        self.mean_fitness_history.append(mean_fitness)
        self.logger.info(f"Fitness máximo: {max_fitness:.4f} | Fitness médio: {mean_fitness:.4f}")
    
    def _evolve_population(self, fitness_scores: List[float]) -> None:
        """Evolui a população através de seleção, crossover e mutação."""
        # Seleção
        self.population = self.selection(self.population, fitness_scores)

        # Crossover e mutação otimizados
        new_population = []
        pop_len = len(self.population)
        
        for i in range(0, pop_len, 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % pop_len]
            
            child1, child2 = self.crossover(parent1, parent2)
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            new_population.extend([child1, child2])

        self.population = new_population[:self.population_size]
      
    # -------------------- INPUT CUSTOM --------------------
    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas usando área definida no layout."""
        if self.map_type == "custom" and pos[0] > UILayout.MapArea.X:
            if (UILayout.MapArea.CITIES_X <= pos[0] <= UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH and
                UILayout.MapArea.CITIES_Y <= pos[1] <= UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT):
                prod = Product.make_random_product(len(self.delivery_points), self.priority_percentage)
                self.delivery_points.append(DeliveryPoint(pos[0], pos[1], product=prod))
                if len(self.delivery_points) > 1:
                    self.calculate_distance_matrix()
                cx = UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH // 2
                cy = UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT // 2
                self.depot = DeliveryPoint.create_depot(cx, cy)
    
    def handle_events(self):
        """Gerencia eventos do pygame de forma otimizada."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self._handle_mouse_click(pygame.mouse.get_pos()):
                    return False
            elif event.type == pygame.KEYDOWN:
                if not self._handle_keyboard_input(event.key):
                    return False
        return True
    
    def _handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        """Processa cliques do mouse de forma organizada."""
        # Controles principais do algoritmo
        if self._handle_algorithm_controls(pos):
            return True
        
        # Controles de mapa
        if self._handle_map_controls(pos):
            return True
            
        # Controles de métodos
        if self._handle_method_controls(pos):
            return True
        
        # Controles de configuração
        if self._handle_config_controls(pos):
            return True
        
        # Input customizado
        if self.map_type == "custom":
            self.handle_custom_input(pos)
        
        return True
    
    def _handle_algorithm_controls(self, pos: Tuple[int, int]) -> bool:
        """Lida com controles principais do algoritmo."""
        if self.buttons['run_algorithm'].collidepoint(pos) and not self.running_algorithm:
            if self.delivery_points:
                self.start_algorithm()
            return True
        elif self.buttons['stop_algorithm'].collidepoint(pos) and self.running_algorithm:
            self.stop_algorithm()
            return True
        elif self.buttons['reset'].collidepoint(pos):
            self.reset_algorithm()
            return True
        elif self.buttons['generate_map'].collidepoint(pos) and not self.running_algorithm:
            self.generate_cities(self.map_type, self.num_cities)
            return True
        return False
    
    def _handle_map_controls(self, pos: Tuple[int, int]) -> bool:
        """Lida com controles de tipo de mapa."""
        if self.buttons['map_random'].collidepoint(pos):
            self.map_type = "random"
            return True
        elif self.buttons['map_circle'].collidepoint(pos):
            self.map_type = "circle"
            return True
        elif self.buttons['map_custom'].collidepoint(pos):
            self.map_type = "custom"
            self.delivery_points = []
            return True
        return False
    
    def _handle_method_controls(self, pos: Tuple[int, int]) -> bool:
        """Lida com controles de métodos de seleção, crossover e mutação."""
        # Métodos de seleção
        selection_methods = {
            'selection_roulette': 'roulette',
            'selection_tournament': 'tournament', 
            'selection_rank': 'rank'
        }
        for button_key, method in selection_methods.items():
            if button_key in self.buttons and self.buttons[button_key].collidepoint(pos):
                if self.selection_method != method:
                    self.logger.info(f"Método de seleção alterado: {self.selection_method} → {method}")
                    self.selection_method = method
                    self._selection_method_cache.clear()  # Limpar cache
                return True
        
        # Métodos de mutação
        mutation_methods = {
            'mutation_swap': 'swap',
            'mutation_inverse': 'inverse',
            'mutation_shuffle': 'shuffle'
        }
        for button_key, method in mutation_methods.items():
            if self.buttons[button_key].collidepoint(pos):
                if self.mutation_method != method:
                    self.mutation_method = method
                    self._mutation_method_cache.clear()  # Limpar cache
                return True
        
        # Métodos de crossover
        crossover_methods = {
            'crossover_pmx': 'pmx',
            'crossover_ox1': 'ox1',
            'crossover_cx': 'cx',
            'crossover_kpoint': 'kpoint',
            'crossover_erx': 'erx'
        }
        for button_key, method in crossover_methods.items():
            if self.buttons[button_key].collidepoint(pos):
                if self.crossover_method != method:
                    self.crossover_method = method
                    self._crossover_method_cache.clear()  # Limpar cache
                return True
        
        return False
    
    def _handle_config_controls(self, pos: Tuple[int, int]) -> bool:
        """Lida com controles de configuração."""
        # Elitismo
        if self.buttons['toggle_elitism'].collidepoint(pos):
            self.elitism = not self.elitism
            return True
        
        # Controle de número de cidades
        if not self.running_algorithm:
            if self.buttons['cities_minus'].collidepoint(pos) and self.num_cities > 3:
                self.num_cities -= 1
                return True
            elif self.buttons['cities_plus'].collidepoint(pos) and self.num_cities < 50:
                self.num_cities += 1
                return True
        
        # Slider de prioridade
        if self.buttons['priority_slider'].collidepoint(pos):
            rect = self.buttons['priority_slider']
            slider_x = rect.x + 120
            slider_w = rect.width - 130
            rel_x = min(max(pos[0] - slider_x, 0), slider_w)
            pct = int((rel_x / slider_w) * 100)
            self.priority_percentage = pct
            return True
        
        return False
    
    def _handle_keyboard_input(self, key: int) -> bool:
        """Processa entrada do teclado."""
        if key == pygame.K_SPACE and not self.running_algorithm:
            if self.delivery_points:
                self.start_algorithm()
        elif key == pygame.K_ESCAPE:
            if self.running_algorithm:
                self.stop_algorithm()
            else:
                return False
        return True
    
    def start_algorithm(self):
        """Inicia o algoritmo genético de forma otimizada."""
        if not self.delivery_points:
            self.logger.warning("Tentativa de iniciar algoritmo sem pontos de entrega")
            return
        
        # Garantir depósito
        if self.depot is None:
            cx = UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH // 2
            cy = UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT // 2
            self.depot = DeliveryPoint.create_depot(cx, cy)

        self.logger.info(f"Iniciando algoritmo genético com {len(self.delivery_points)} cidades")
        self.logger.info(f"Configurações: população={self.population_size}, gerações={self.max_generations}")
        self.logger.info(f"Métodos: seleção={self.selection_method}, crossover={self.crossover_method}, mutação={self.mutation_method}, elitismo={self.elitism}")
        if self.use_fleet:
            self.logger.info(f"VRP ativado | tipos de veículos: {[ (v.name, v.count, v.autonomy) for v in self.fleet ]}")
        
        # Resetar estado
        self.running_algorithm = True
        self.current_generation = 0
        self.best_fitness = 0
        self.best_route = None
        self.fitness_history = []
        self.mean_fitness_history = []
        
        # Limpar caches para novo algoritmo
        self._clear_all_caches()
        
        self.initialize_population()
    
    def _clear_all_caches(self) -> None:
        """Limpa todos os caches para liberar memória."""
        self._selection_method_cache.clear()
        self._crossover_method_cache.clear()
        self._mutation_method_cache.clear()
        self._fitness_cache.clear()
    
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
        """Loop principal otimizado do programa."""
        self.logger.info("Iniciando loop principal da aplicação")
        running = True

        while running:
            running = self.handle_events()
            
            # Processar algoritmo genético
            self._process_genetic_algorithm()
            
            # Renderizar interface
            self._render_interface()
            
            # Atualizar display
            pygame.display.flip()
            self.clock.tick(60)

        self._cleanup_and_exit()
    
    def _process_genetic_algorithm(self) -> None:
        """Processa uma iteração do algoritmo genético."""
        if self.running_algorithm and self.current_generation < self.max_generations:
            self.run_generation()

            if self.current_generation >= self.max_generations:
                self.logger.info(f"Algoritmo finalizado após {self.max_generations} gerações")
                self.logger.info(f"Melhor fitness final: {self.best_fitness:.4f}")
                self.running_algorithm = False
    
    def _render_interface(self) -> None:
        """Renderiza toda a interface do usuário."""
        # Limpar tela
        self.screen.fill(WHITE)

        # Desenhar área do mapa
        self._draw_map_area()
        
        # Desenhar interface UI
        DrawFunctions.draw_interface(self)

        # Desenhar visualizações de dados
        self._draw_visualizations()
        
        # Desenhar mensagens especiais
        self._draw_special_messages()
    
    def _draw_map_area(self) -> None:
        """Desenha a área do mapa com bordas."""
        map_rect = (UILayout.MapArea.X, UILayout.MapArea.Y, UILayout.MapArea.WIDTH, UILayout.MapArea.HEIGHT)
        pygame.draw.rect(self.screen, WHITE, map_rect)
        pygame.draw.rect(self.screen, BLACK, map_rect, 2)
    
    def _draw_visualizations(self) -> None:
        """Desenha as visualizações principais (cidades, rotas, etc)."""
        if not self.delivery_points:
            return
            
        if self.use_fleet and self.depot is not None:
            self._draw_vrp_visualization()
        else:
            self._draw_tsp_visualization()
    
    def _draw_vrp_visualization(self) -> None:
        """Desenha visualização para VRP (Vehicle Routing Problem)."""
        DrawFunctions.draw_cities(self)
        DrawFunctions.draw_depot(self, self.depot)

        # Desenhar melhor solução
        if self.best_route and hasattr(self.best_route, "routes") and self.best_route.routes:
            DrawFunctions.draw_vrp_solution(self, self.best_route.routes, self.depot)

        # Desenhar solução atual durante execução
        if (self.population and self.running_algorithm and 
            hasattr(self.population[0], 'fitness')):
            current_best = max(self.population, key=lambda ind: getattr(ind, 'fitness', 0))
            if hasattr(current_best, "routes") and current_best.routes:
                DrawFunctions.draw_vrp_solution(self, current_best.routes, self.depot, show_legend=False)
    
    def _draw_tsp_visualization(self) -> None:
        """Desenha visualização para TSP simples."""
        # Desenhar melhor rota
        if self.best_route:
            DrawFunctions.draw_route(self, self.best_route, RED, 3)

        # Desenhar rota atual durante execução
        if self.population and self.running_algorithm:
            fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(chrom) 
                            for chrom in self.population]
            if fitness_scores:
                best_idx = fitness_scores.index(max(fitness_scores))
                current_best = self.population[best_idx]
                DrawFunctions.draw_route(self, current_best, BLUE, 2)

        DrawFunctions.draw_cities(self)
    
    def _draw_special_messages(self) -> None:
        """Desenha mensagens especiais na interface."""
        if (self.map_type == "custom" and not self.delivery_points and 
            hasattr(UILayout, "SpecialElements")):
            instruction = self.font.render("Click on the map to add cities", True, BLACK)
            self.screen.blit(instruction, (UILayout.SpecialElements.CUSTOM_MESSAGE_X, 
                                         UILayout.SpecialElements.CUSTOM_MESSAGE_Y))
    
    def _cleanup_and_exit(self) -> None:
        """Limpa recursos e encerra a aplicação."""
        self.logger.info("Encerrando aplicação")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
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
