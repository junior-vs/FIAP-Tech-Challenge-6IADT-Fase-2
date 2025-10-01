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

        # Interface - usar layout centralizado
        self.ui_layout = UILayout()
        self.map_type = "random"  # "random", "circle", "custom"
        self.num_cities = 10
        self.buttons = UILayout.Buttons.create_button_positions()
        
        self.logger.info("Aplicação inicializada com sucesso")
    def _make_random_product(self, idx: int) -> Product:
        """Gera um produto válido aleatório respeitando as restrições.

        - Cada lado <= 100 cm; soma <= 200 cm; peso <= 10000 g.
        """
        # Nome simples baseado no índice
        name = f"Produto-{idx}"
        # Peso entre 100 g e 10000 g
        weight = random.randint(100, 10_000)
        # Gerar dimensões: escolha dois lados aleatórios e derive o terceiro para respeitar soma
        for _ in range(100):
            a = random.uniform(5.0, 100.0)
            b = random.uniform(5.0, 100.0)
            max_c = min(100.0, 200.0 - (a + b))
            if max_c > 5.0:
                c = random.uniform(5.0, max_c)
                # aleatorizar a ordem (C, L, A)
                dims = [a, b, c]
                random.shuffle(dims)
                try:
                    return Product(name=name, weight=weight,
                                   length=dims[0], width=dims[1], height=dims[2])
                except ValueError:
                    continue
        # fallback seguro: dimensões fixas válidas
        return Product(name=name, weight=min(weight, 10_000), length=100, width=50, height=50)
        
    
    
    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado usando configurações centralizadas."""
        self.logger.info(f"Gerando {num_cities} cidades usando mapa tipo '{map_type}'")
        self.delivery_points = []

        if map_type == "random":
            # Usar área definida no layout centralizado
            for i in range(num_cities):
                x = random.randint(UILayout.MapArea.RANDOM_MIN_X, UILayout.MapArea.RANDOM_MAX_X)
                y = random.randint(UILayout.MapArea.RANDOM_MIN_Y, UILayout.MapArea.RANDOM_MAX_Y)
                prod = self._make_random_product(i)
                self.delivery_points.append(DeliveryPoint(x, y, product=prod))

        elif map_type == "circle":
            # Usar configurações centralizadas para círculo
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
            # Modo customizado será implementado no método handle_custom_input
            self.logger.info("Modo customizado ativado - aguardando input do usuário")

        if self.delivery_points:
            self.calculate_distance_matrix()
            self.logger.info(f"Geradas {len(self.delivery_points)} cidades com sucesso")
    
    def initialize_population(self):
        """Inicializa a população com cromossomos aleatórios"""
        self.population = []

        # Create population as shuffled Route instances
        base = list(self.delivery_points)
        for _ in range(self.population_size):
            shuffled = base[:]
            random.shuffle(shuffled)
            self.population.append(Route(shuffled))
    
    def selection(self, population: List[Route], fitness_scores: List[float]) -> List[Route]:
        """Seleção usando métodos do selection_functions.py com suporte a diferentes algoritmos e elitismo."""
        # Verificação de segurança para evitar erros
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return population.copy()

        # Selecionar método de seleção baseado na configuração
        new_population = []
        for _ in range(len(population)):
            if self.selection_method == "roulette":
                chosen = Selection.roulette(population, fitness_scores)
            elif self.selection_method == "tournament":
                # Usar tamanho de torneio padrão de 3
                chosen = Selection.tournament(population, fitness_scores, tournament_size=3)
            elif self.selection_method == "rank":
                chosen = Selection.rank(population, fitness_scores)
            else:
                # Fallback para roleta
                chosen = Selection.roulette(population, fitness_scores)
            
            new_population.append(chosen.copy())

        # Aplicar elitismo - preservar o melhor indivíduo da geração atual
        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
            # Substitui o último indivíduo da nova população pelo melhor da atual
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
            # ERX retorna um filho, então criamos dois chamando duas vezes
            child1 = Crossover.erx_crossover(parent1, parent2)
            child2 = Crossover.erx_crossover(parent2, parent1)
            return child1, child2
        else:
            # Fallback para PMX
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
            # Fallback para swap
            return Mutation.mutacao_por_troca(route)
    

    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        # Delega o cálculo para DeliveryPoint
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        if not self.population:
            self.initialize_population()

        # Calcular fitness de toda a população (population is List[Route])
        fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ind) for ind in self.population]

        # Atualizar melhor rota
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            old_fitness = self.best_fitness
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()
            
            # Log melhoria significativa
            if old_fitness == 0 or (max_fitness - old_fitness) / old_fitness > 0.1:
                self.logger.info(f"Geração {self.current_generation}: Nova melhor fitness {max_fitness:.4f} (+{max_fitness - old_fitness:.4f})")

        # Armazenar histórico
        self.fitness_history.append(max_fitness)
        mean_fitness = np.mean(fitness_scores)
        self.mean_fitness_history.append(mean_fitness)

        # Log progresso a cada 10 gerações
        if self.current_generation % 10 == 0:
            self.logger.debug(f"Geração {self.current_generation}: Fitness média={mean_fitness:.4f}, Melhor={max_fitness:.4f}")

        # Seleção (returns List[Route])
        self.population = self.selection(self.population, fitness_scores)

        # Crossover e mutação
        new_population = []

        for i in range(0, len(self.population), 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % len(self.population)]

            # Sempre aplicar crossover - usuário escolhe apenas o método
            child1, child2 = self.crossover(parent1, parent2)

            child1 = self.mutate(child1)
            child2 = self.mutate(child2)

            new_population.extend([child1, child2])

        # Trim to population size and advance generation
        self.population = new_population[:self.population_size]
        self.current_generation += 1
      
    
    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas usando área definida no layout."""
        if self.map_type == "custom" and pos[0] > UILayout.MapArea.X:
            # Garantir que o clique está dentro da área válida
            if (UILayout.MapArea.CITIES_X <= pos[0] <= UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH and
                UILayout.MapArea.CITIES_Y <= pos[1] <= UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT):
                prod = self._make_random_product(len(self.delivery_points))
                self.delivery_points.append(DeliveryPoint(pos[0], pos[1], product=prod))
                if len(self.delivery_points) > 1:
                    self.calculate_distance_matrix()
    
    def handle_events(self):
        """Gerencia eventos do pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # Verificar cliques nos botões
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

                # Botão Elitism
                elif self.buttons['toggle_elitism'].collidepoint(pos):
                    self.elitism = not self.elitism

                # Botões de método de seleção
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

                # Controles de número de cidades
                elif self.buttons['cities_minus'].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities > 3:  # Mínimo de 3 cidades
                        self.num_cities -= 1

                elif self.buttons['cities_plus'].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities < 50:  # Máximo de 50 cidades
                        self.num_cities += 1

                # Botões de método de mutação
                elif self.buttons['mutation_swap'].collidepoint(pos):
                    self.mutation_method = "swap"
                elif self.buttons['mutation_inverse'].collidepoint(pos):
                    self.mutation_method = "inverse"
                elif self.buttons['mutation_shuffle'].collidepoint(pos):
                    self.mutation_method = "shuffle"

                # Botões de método de crossover
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

                # Modo customizado - adicionar cidade
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
        
        self.logger.info(f"Iniciando algoritmo genético com {len(self.delivery_points)} cidades")
        self.logger.info(f"Configurações: população={self.population_size}, gerações={self.max_generations}")
        self.logger.info(f"Métodos: seleção={self.selection_method}, crossover={self.crossover_method}, mutação={self.mutation_method}, elitismo={self.elitism}")
        
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
    
    def run(self):
        """Loop principal do programa"""
        self.logger.info("Iniciando loop principal da aplicação")
        running = True
        
        while running:
            running = self.handle_events()
            
            # Executar uma geração se o algoritmo estiver rodando
            if self.running_algorithm and self.current_generation < self.max_generations:
                self.run_generation()
                
                # Parar se atingiu o limite de gerações
                if self.current_generation >= self.max_generations:
                    self.logger.info(f"Algoritmo finalizado após {self.max_generations} gerações")
                    self.logger.info(f"Melhor fitness final: {self.best_fitness:.4f}")
                    self.running_algorithm = False
            
            # Desenhar tudo
            self.screen.fill(WHITE)
            
            # Área do mapa usando configurações centralizadas
            map_rect = (UILayout.MapArea.X, UILayout.MapArea.Y, UILayout.MapArea.WIDTH, UILayout.MapArea.HEIGHT)
            pygame.draw.rect(self.screen, WHITE, map_rect)
            pygame.draw.rect(self.screen, BLACK, map_rect, 2)
            
            # Desenhar interface via DrawFunctions
            DrawFunctions.draw_interface(self)
            
            # Desenhar cidades e rotas
            if self.delivery_points:
                # Desenhar melhor rota
                if self.best_route:
                    DrawFunctions.draw_route(self, self.best_route, RED, 3)

                # Desenhar rota da geração atual
                if self.population and self.running_algorithm:
                    fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(chrom) for chrom in self.population]
                    if fitness_scores:
                        best_idx = fitness_scores.index(max(fitness_scores))
                        current_best = self.population[best_idx]
                        DrawFunctions.draw_route(self, current_best, BLUE, 2)

                DrawFunctions.draw_cities(self)

            # Instruções para modo customizado usando posição centralizada
            if self.map_type == "custom" and not self.delivery_points:
                instruction = self.font.render("Click on the map to add cities", True, BLACK)
                self.screen.blit(instruction, (UILayout.SpecialElements.CUSTOM_MESSAGE_X, 
                                             UILayout.SpecialElements.CUSTOM_MESSAGE_Y))
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        self.logger.info("Encerrando aplicação")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Configurar sistema de logging usando módulo centralizado
    configurar_logging()
    
    # Criar logger para o módulo principal
    logger = get_logger(__name__)
    
    try:
        # Criar e executar aplicação
        logger.info("=== Início da Aplicação TSP Genetic Algorithm ===")
        app = TSPGeneticAlgorithm()
        app.run()
        
    except Exception as e:
        logger.critical(f"Erro crítico na aplicação: {e}", exc_info=True)
        raise
    finally:
        logger.info("=== Fim da Aplicação ===")