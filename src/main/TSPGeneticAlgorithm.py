import sys
from typing import List, Tuple, Optional
import pygame
from src.functions.genetic_engine import GeneticEngine
from src.domain.delivery_point import DeliveryPoint
from src.functions.draw_functions import DrawFunctions
from src.functions.fitness_function import FitnessFunction
from src.functions.ui_layout import UILayout
from src.functions.app_logging import get_logger
from src.domain.product import Product
from src.domain.vehicle import VehicleType, default_fleet


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
        
        # Engine do Algoritmo Genético (separa lógica do GA da UI)
        self.engine = GeneticEngine(
            population_size=self.population_size,
            selection_method=self.selection_method,
            crossover_method=self.crossover_method,
            mutation_method=self.mutation_method,
            elitism=self.elitism,
            use_fleet=self.use_fleet,
        )
        # Manter caches locais para compatibilidade com UI (limpeza via botões)
        self._selection_method_cache = {}
        self._crossover_method_cache = {}
        self._mutation_method_cache = {}
        self._fitness_cache = {}
        
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
            # Atualizar contexto do engine
            self.engine.set_delivery_points(self.delivery_points)
            self.engine.set_vrp_context(self.depot, self.fleet)
    
    def initialize_population(self):
        """Inicializa a população via GeneticEngine."""
        # Garantir que engine está com parâmetros atualizados
        # Atualizar contexto do engine e inicializar população
        self.engine.population_size = self.population_size
        self.engine.selection_method = self.selection_method
        self.engine.crossover_method = self.crossover_method
        self.engine.mutation_method = self.mutation_method
        self.engine.elitism = self.elitism
        self.engine.use_fleet = self.use_fleet
        self.engine.current_generation = 0
        self.engine.best_fitness = 0.0
        self.engine.best_route = None
        self.engine.fitness_history = []
        self.engine.mean_fitness_history = []
        self.engine.set_delivery_points(self.delivery_points)
        self.engine.set_vrp_context(self.depot, self.fleet)
        self.engine.clear_caches()
        self.engine.initialize_population()
        self.population = self.engine.population
    
    
    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    # -------------------- EXECUÇÃO DE UMA GERAÇÃO --------------------
    @log_performance
    def run_generation(self):
        """Executa uma geração do algoritmo genético via GeneticEngine."""
        self.logger.info(f"Executando geração {self.engine.current_generation}")
        fitness_scores, results = self.engine.run_generation()
        # Espelhar estado para UI
        self.population = self.engine.population
        self.best_route = self.engine.best_route
        self.best_fitness = self.engine.best_fitness
        self.fitness_history = self.engine.fitness_history
        self.mean_fitness_history = self.engine.mean_fitness_history
        self.current_generation = self.engine.current_generation
        return fitness_scores, results
    
      
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
                # Clique do mouse não controla ciclo de vida; apenas executa ações da UI
                self._handle_mouse_click(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                if not self._handle_keyboard_input(event.key):
                    return False
        return True
    
    def _handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """Processa cliques do mouse de forma organizada."""
        # Controles principais do algoritmo
        if self._handle_algorithm_controls(pos):
            return
        
        # Controles de mapa
        if self._handle_map_controls(pos):
            return
            
        # Controles de métodos
        if self._handle_method_controls(pos):
            return
        
        # Controles de configuração
        if self._handle_config_controls(pos):
            return
        
        # Input customizado
        if self.map_type == "custom":
            self.handle_custom_input(pos)
        
    
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
    
    def _handle_option_group(self, button_map: dict, attr_name: str, cache_attr: str, pos: Tuple[int, int], log_label: Optional[str] = None) -> bool:
        """Manipula um grupo de botões que definem uma opção única (reduz complexidade)."""
        for button_key, value in button_map.items():
            if button_key in self.buttons and self.buttons[button_key].collidepoint(pos):
                current = getattr(self, attr_name)
                if current != value:
                    if log_label:
                        self.logger.info(f"{log_label} alterado: {current} → {value}")
                    setattr(self, attr_name, value)
                    getattr(self, cache_attr).clear()
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
        if self._handle_option_group(selection_methods, 'selection_method', '_selection_method_cache', pos, 'Método de seleção'):
            return True
        
        # Métodos de mutação
        mutation_methods = {
            'mutation_swap': 'swap',
            'mutation_inverse': 'inverse',
            'mutation_shuffle': 'shuffle'
        }
        if self._handle_option_group(mutation_methods, 'mutation_method', '_mutation_method_cache', pos, 'Método de mutação'):
            return True
        
        # Métodos de crossover
        crossover_methods = {
            'crossover_pmx': 'pmx',
            'crossover_ox1': 'ox1',
            'crossover_cx': 'cx',
            'crossover_kpoint': 'kpoint',
            'crossover_erx': 'erx'
        }
        if self._handle_option_group(crossover_methods, 'crossover_method', '_crossover_method_cache', pos, 'Método de crossover'):
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
        
        # Atualizar contexto do engine e inicializar população
        self.engine.population_size = self.population_size
        self.engine.selection_method = self.selection_method
        self.engine.crossover_method = self.crossover_method
        self.engine.mutation_method = self.mutation_method
        self.engine.elitism = self.elitism
        self.engine.use_fleet = self.use_fleet
        self.engine.current_generation = 0
        self.engine.best_fitness = 0.0
        self.engine.best_route = None
        self.engine.fitness_history = []
        self.engine.mean_fitness_history = []
        self.engine.set_delivery_points(self.delivery_points)
        self.engine.set_vrp_context(self.depot, self.fleet)
        self.engine.clear_caches()
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
