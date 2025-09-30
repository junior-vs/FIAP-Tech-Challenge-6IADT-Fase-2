import sys
from typing import List, Tuple
import random
import math
import os
import pygame
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../domain')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../functions')))
from delivery_point import DeliveryPoint
from draw_functions import DrawFunctions
from route import Route
from crossover_function import Crossover
from mutation_function import Mutation
from selection_functions import Selection
from fitness_function import FitnessFunction

# Inicializar pygame
pygame.init()


# Constantes
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)


class TSPGeneticAlgorithm:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TSP - Genetic Algorithm Approach")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        # Variáveis do algoritmo
        self.delivery_points: List[DeliveryPoint] = []
        self.distance_matrix = None
        self.population = []  # will hold List[Route] after initialization
        self.population_size = 50
        self.max_generations = 100
        self.mutation_rate_min = 0.01
        self.mutation_rate_max = 0.1
        self.crossover_rate_min = 0.05
        self.crossover_rate_max = 0.8
        self.elitism = True
        self.running_algorithm = False
        self.current_generation = 0
        self.best_route = None
        self.best_fitness = 0
        self.fitness_history = []
        self.mean_fitness_history = []

        # Interface
        self.map_type = "random"  # "random", "circle", "custom"
        self.num_cities = 10
        self.buttons = DrawFunctions.create_buttons()
        
    
    
    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado"""
        self.delivery_points = []

        if map_type == "random":
            for _ in range(num_cities):
                x = random.randint(400, 900)
                y = random.randint(100, 600)
                self.delivery_points.append(DeliveryPoint(x, y))

        elif map_type == "circle":
            center_x, center_y = 650, 350
            radius = 200
            for i in range(num_cities):
                angle = 2 * math.pi * i / num_cities
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.delivery_points.append(DeliveryPoint(int(x), int(y)))

        elif map_type == "custom":
            # Modo customizado será implementado no método handle_custom_input
            pass

        if self.delivery_points:
            self.calculate_distance_matrix()
    

    
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
        """Seleção por roleta (retorna nova população de Route).

        Falls back to using Selection.roulette for clarity.
        """
        # If all fitness scores are zero, return a shallow copy
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return population.copy()

        # Use Selection.roulette which expects aptitudes list
        new_population = []
        for _ in range(len(population)):
            chosen = Selection.roulette(population, fitness_scores)
            new_population.append(chosen.copy())

        # Elitismo - manter o melhor cromossomo
        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
            new_population[-1] = population[best_idx].copy()

        return new_population
    
    def crossover(self, parent1: Route, parent2: Route) -> Tuple[Route, Route]:
        """Wrapper that uses the domain Crossover implementations.

        By default uses OX1 that returns two children.
        """
        # Use the two-child ordered crossover implementation
        child1, child2 = Crossover.crossover_parcialmente_mapeado_pmx(parent1, parent2)
        #child1 = Crossover.erx_crossover(parent1, parent2)
        #child2 = Crossover.erx_crossover(parent2, parent1)
        return child1, child2
    
    def mutate(self, route: Route, mutation_rate: float) -> Route:
        """Apply a mutation operator from Mutation module to a Route."""
        if random.random() < mutation_rate:
            # choose one mutation style at random to diversify
            choice = random.choice(["swap", "inverse", "shuffle"])
            if choice == "swap":
                return Mutation.mutacao_por_troca(route)
            if choice == "inverse":
                return Mutation.mutacao_por_inversao(route)
            return Mutation.mutacao_por_embaralhamento(route)
        return route.copy()
    

    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        # Delega o cálculo para DeliveryPoint
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        if not self.population:
            self.initialize_population()

        # Calcular fitness de toda a população (population is List[Route])
        fitness_scores = [FitnessFunction.calculate_fitness(ind) for ind in self.population]

        # Atualizar melhor cromossomo
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()

        # Armazenar histórico
        self.fitness_history.append(max_fitness)
        self.mean_fitness_history.append(np.mean(fitness_scores))

        # Seleção (returns List[Route])
        self.population = self.selection(self.population, fitness_scores)

        # Crossover e mutação
        new_population = []

        # Taxa de mutação e crossover variáveis
        progress = self.current_generation / max(1, self.max_generations)
        current_mutation_rate = self.mutation_rate_max - (self.mutation_rate_max - self.mutation_rate_min) * progress
        current_crossover_rate = self.crossover_rate_max - (self.crossover_rate_max - self.crossover_rate_min) * progress

        for i in range(0, len(self.population), 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % len(self.population)]

            if random.random() < current_crossover_rate:
                child1, child2 = self.crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            child1 = self.mutate(child1, current_mutation_rate)
            child2 = self.mutate(child2, current_mutation_rate)

            new_population.extend([child1, child2])

        # Trim to population size and advance generation
        self.population = new_population[:self.population_size]
        self.current_generation += 1
    
    
    
    
    
    
   
    
    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas (usa lógica reduzida)."""
        if self.map_type == "custom" and pos[0] > 370:
            self.delivery_points.append(DeliveryPoint(pos[0], pos[1]))
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

                # Botões Mutation/Crossover
                elif self.buttons['mutation_rate_min_inc'].collidepoint(pos):
                    self.mutation_rate_min = min(self.mutation_rate_min + 0.01, 1.0)
                elif self.buttons['mutation_rate_min_dec'].collidepoint(pos):
                    self.mutation_rate_min = max(self.mutation_rate_min - 0.01, 0.0)
                elif self.buttons['mutation_rate_max_inc'].collidepoint(pos):
                    self.mutation_rate_max = min(self.mutation_rate_max + 0.01, 1.0)
                elif self.buttons['mutation_rate_max_dec'].collidepoint(pos):
                    self.mutation_rate_max = max(self.mutation_rate_max - 0.01, 0.0)
                elif self.buttons['crossover_rate_min_inc'].collidepoint(pos):
                    self.crossover_rate_min = min(self.crossover_rate_min + 0.01, 1.0)
                elif self.buttons['crossover_rate_min_dec'].collidepoint(pos):
                    self.crossover_rate_min = max(self.crossover_rate_min - 0.01, 0.0)
                elif self.buttons['crossover_rate_max_inc'].collidepoint(pos):
                    self.crossover_rate_max = min(self.crossover_rate_max + 0.01, 1.0)
                elif self.buttons['crossover_rate_max_dec'].collidepoint(pos):
                    self.crossover_rate_max = max(self.crossover_rate_max - 0.01, 0.0)

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
            return
        
        self.running_algorithm = True
        self.current_generation = 0
        self.best_fitness = 0
        self.best_route = None
        self.fitness_history = []
        self.mean_fitness_history = []
        self.initialize_population()
    
    def stop_algorithm(self):
        """Para o algoritmo genético"""
        self.running_algorithm = False
    
    def reset_algorithm(self):
        """Reseta o algoritmo e limpa os dados"""
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
        running = True
        
        while running:
            running = self.handle_events()
            
            # Executar uma geração se o algoritmo estiver rodando
            if self.running_algorithm and self.current_generation < self.max_generations:
                self.run_generation()
                
                # Parar se atingiu o limite de gerações
                if self.current_generation >= self.max_generations:
                    self.running_algorithm = False
            
            # Desenhar tudo
            self.screen.fill(WHITE)
            
            # Área do mapa
            pygame.draw.rect(self.screen, WHITE, (370, 10, 820, 780))
            pygame.draw.rect(self.screen, BLACK, (370, 10, 820, 780), 2)
            
            # Desenhar interface via DrawFunctions
            DrawFunctions.draw_interface(self)
            
            # Desenhar cidades e rotas
            if self.delivery_points:
                # Desenhar melhor rota
                if self.best_route:
                    DrawFunctions.draw_route(self, self.best_route, RED, 3)

                # Desenhar rota da geração atual
                if self.population and self.running_algorithm:
                    fitness_scores = [FitnessFunction.calculate_fitness(chrom) for chrom in self.population]
                    if fitness_scores:
                        best_idx = fitness_scores.index(max(fitness_scores))
                        current_best = self.population[best_idx]
                        DrawFunctions.draw_route(self, current_best, BLUE, 2)

                DrawFunctions.draw_cities(self)

            # Instruções para modo customizado
            if self.map_type == "custom" and not self.delivery_points:
                instruction = self.font.render("Click on the map to add cities", True, BLACK)
                self.screen.blit(instruction, (400, 400))
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = TSPGeneticAlgorithm()
    app.run()