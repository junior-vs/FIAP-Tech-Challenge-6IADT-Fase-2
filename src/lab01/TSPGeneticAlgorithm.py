import pygame
import sys
import numpy as np
import random
from typing import List, Tuple, Optional
import math
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../domain')))
from cidade import Cidade

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
        self.cities: List[Cidade] = []
        self.distance_matrix = None
        self.population = []
        self.population_size = 50
        self.max_generations = 100
        self.mutation_rate_min = 0.01
        self.mutation_rate_max = 0.1
        self.crossover_rate_min = 0.05
        self.crossover_rate_max = 0.8
        self.elitism = True
        self.running_algorithm = False
        self.current_generation = 0
        self.best_chromosome = None
        self.best_fitness = 0
        self.fitness_history = []
        self.mean_fitness_history = []
        
        # Interface
        self.map_type = "random"  # "random", "circle", "custom"
        self.num_cities = 10
        self.buttons = self.create_buttons()
        
    def create_buttons(self):
        return {
            'generate_map': pygame.Rect(50, 50, 120, 30),
            'reset': pygame.Rect(180, 50, 120, 30),
            'map_random': pygame.Rect(50, 100, 80, 25),
            'map_circle': pygame.Rect(140, 100, 80, 25),
            'map_custom': pygame.Rect(230, 100, 80, 25),
            'toggle_elitism': pygame.Rect(50, 150, 120, 30),
            'mutation_rate_min_inc': pygame.Rect(50, 200, 30, 30),
            'mutation_rate_min_dec': pygame.Rect(85, 200, 30, 30),
            'mutation_rate_max_inc': pygame.Rect(130, 200, 30, 30),
            'mutation_rate_max_dec': pygame.Rect(165, 200, 30, 30),
            'crossover_rate_min_inc': pygame.Rect(50, 250, 30, 30),
            'crossover_rate_min_dec': pygame.Rect(85, 250, 30, 30),
            'crossover_rate_max_inc': pygame.Rect(130, 250, 30, 30),
            'crossover_rate_max_dec': pygame.Rect(165, 250, 30, 30),
            'run_algorithm': pygame.Rect(50, 300, 120, 30),
            'stop_algorithm': pygame.Rect(180, 300, 120, 30),
        }
    
    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado"""
        self.cities = []

        if map_type == "random":
            for _ in range(num_cities):
                x = random.randint(400, 900)
                y = random.randint(100, 600)
                self.cities.append(Cidade(x, y))

        elif map_type == "circle":
            center_x, center_y = 650, 350
            radius = 200
            for i in range(num_cities):
                angle = 2 * math.pi * i / num_cities
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.cities.append(Cidade(int(x), int(y)))

        elif map_type == "custom":
            # Modo customizado será implementado no método handle_custom_input
            pass

        if self.cities:
            self.calculate_distance_matrix()
    
    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todas as cidades"""
        n = len(self.cities)
        self.distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = self.cities[i].distancia_pura(self.cities[j])
                    self.distance_matrix[i][j] = distance
    
    def initialize_population(self):
        """Inicializa a população com cromossomos aleatórios"""
        num_cities = len(self.cities)
        self.population = []
        
        for _ in range(self.population_size):
            chromosome = list(range(num_cities))
            random.shuffle(chromosome)
            self.population.append(chromosome)
    
    def calculate_fitness(self, chromosome: List[int]) -> float:
        """Calcula o fitness de um cromossomo (inverso da distância total)"""
        total_distance = 0
        for i in range(len(chromosome)):
            from_city = chromosome[i]
            to_city = chromosome[(i + 1) % len(chromosome)]
            total_distance += self.distance_matrix[from_city][to_city]
        return 1.0 / total_distance if total_distance > 0 else 0
    
    def selection(self, population: List[List[int]], fitness_scores: List[float]) -> List[List[int]]:
        """Seleção por roleta"""
        new_population = []
        total_fitness = sum(fitness_scores)
        
        if total_fitness == 0:
            return population.copy()
        
        probabilities = [f / total_fitness for f in fitness_scores]
        cumulative_prob = np.cumsum(probabilities)
        
        for _ in range(len(population)):
            r = random.random()
            selected_idx = 0
            for i, cum_prob in enumerate(cumulative_prob):
                if r <= cum_prob:
                    selected_idx = i
                    break
            new_population.append(population[selected_idx].copy())
        
        # Elitismo - manter o melhor cromossomo
        if self.elitism and self.best_chromosome:
            best_idx = fitness_scores.index(max(fitness_scores))
            new_population[-1] = population[best_idx].copy()
            
        return new_population
    
    def crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """Crossover de ordem (OX)"""
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))
        
        child1 = [-1] * size
        child2 = [-1] * size
        
        # Copiar segmento do primeiro pai
        child1[start:end] = parent1[start:end]
        child2[start:end] = parent2[start:end]
        
        # Preencher o resto com genes do segundo pai
        def fill_child(child, other_parent):
            pointer = end
            for gene in other_parent[end:] + other_parent[:end]:
                if gene not in child:
                    child[pointer % size] = gene
                    pointer += 1
        
        fill_child(child1, parent2)
        fill_child(child2, parent1)
        
        return child1, child2
    
    def mutate(self, chromosome: List[int], mutation_rate: float) -> List[int]:
        """Mutação por troca de dois genes"""
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(chromosome)), 2)
            chromosome[i], chromosome[j] = chromosome[j], chromosome[i]
        return chromosome
    
    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        if not self.population:
            return
        
        # Calcular fitness de toda a população
        fitness_scores = [self.calculate_fitness(chrom) for chrom in self.population]
        
        # Atualizar melhor cromossomo
        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_chromosome = self.population[best_idx].copy()
        
        # Armazenar histórico
        self.fitness_history.append(max_fitness)
        self.mean_fitness_history.append(np.mean(fitness_scores))
        
        # Seleção
        self.population = self.selection(self.population, fitness_scores)
        
        # Crossover e mutação
        new_population = []
        
        # Taxa de mutação e crossover variáveis
        progress = self.current_generation / self.max_generations
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
        
        self.population = new_population[:self.population_size]
        self.current_generation += 1
    
    def draw_cities(self):
        """Desenha as cidades no mapa"""
        for i, cidade in enumerate(self.cities):
            x, y = cidade.x, cidade.y
            pygame.draw.circle(self.screen, BLUE, (x, y), 8)
            pygame.draw.circle(self.screen, WHITE, (x, y), 6)

            # Desenhar número da cidade
            text = self.small_font.render(str(i), True, BLACK)
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)
    
    def draw_route(self, chromosome: List[int], color: Tuple[int, int, int] = BLACK, width: int = 2):
        """Desenha a rota de um cromossomo"""
        if len(chromosome) < 2:
            return
            
        points = [(self.cities[i].x, self.cities[i].y) for i in chromosome]
        points.append((self.cities[chromosome[0]].x, self.cities[chromosome[0]].y))  # Fechar o ciclo

        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, width)
    
    def draw_interface(self):
        """Desenha a interface do usuário"""
        # Fundo da área de controles
        pygame.draw.rect(self.screen, LIGHT_GRAY, (10, 10, 350, 780))

        # Título
        title = self.font.render("TSP - Genetic Algorithm", True, BLACK)
        self.screen.blit(title, (20, 20))

        # Botões
        button_color = WHITE if not self.running_algorithm else GRAY

        # Botão Generate Map
        pygame.draw.rect(self.screen, button_color, self.buttons['generate_map'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['generate_map'], 2)
        text = self.font.render("Generate Map", True, BLACK)
        self.screen.blit(text, (self.buttons['generate_map'].x + 5, self.buttons['generate_map'].y + 5))

        # Botão Run Algorithm
        run_color = GREEN if not self.running_algorithm else GRAY
        pygame.draw.rect(self.screen, run_color, self.buttons['run_algorithm'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['run_algorithm'], 2)
        text = self.font.render("Run Algorithm", True, BLACK)
        self.screen.blit(text, (self.buttons['run_algorithm'].x + 5, self.buttons['run_algorithm'].y + 5))

        # Botão Stop Algorithm
        stop_color = RED if self.running_algorithm else GRAY
        pygame.draw.rect(self.screen, stop_color, self.buttons['stop_algorithm'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['stop_algorithm'], 2)
        text = self.font.render("Stop", True, BLACK)
        self.screen.blit(text, (self.buttons['stop_algorithm'].x + 40, self.buttons['stop_algorithm'].y + 5))

        # Botão Reset
        pygame.draw.rect(self.screen, WHITE, self.buttons['reset'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['reset'], 2)
        text = self.font.render("Reset", True, BLACK)
        self.screen.blit(text, (self.buttons['reset'].x + 40, self.buttons['reset'].y + 5))

        # Botões de tipo de mapa
        map_types = ['map_random', 'map_circle', 'map_custom']
        map_labels = ['Random', 'Circle', 'Custom']

        for i, (btn_name, label) in enumerate(zip(map_types, map_labels)):
            color = GREEN if self.map_type == label.lower() else WHITE
            pygame.draw.rect(self.screen, color, self.buttons[btn_name])
            pygame.draw.rect(self.screen, BLACK, self.buttons[btn_name], 2)
            text = self.small_font.render(label, True, BLACK)
            self.screen.blit(text, (self.buttons[btn_name].x + 5, self.buttons[btn_name].y + 5))

        # Botão Elitism
        elitism_color = GREEN if self.elitism else RED
        pygame.draw.rect(self.screen, elitism_color, self.buttons['toggle_elitism'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['toggle_elitism'], 2)
        text = self.small_font.render(f"Elitism: {'On' if self.elitism else 'Off'}", True, BLACK)
        self.screen.blit(text, (self.buttons['toggle_elitism'].x + 10, self.buttons['toggle_elitism'].y + 5))

        # Botões Mutation/Crossover
        pygame.draw.rect(self.screen, WHITE, self.buttons['mutation_rate_min_inc'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['mutation_rate_min_inc'], 2)
        text = self.small_font.render("+", True, BLACK)
        self.screen.blit(text, (self.buttons['mutation_rate_min_inc'].x + 7, self.buttons['mutation_rate_min_inc'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['mutation_rate_min_dec'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['mutation_rate_min_dec'], 2)
        text = self.small_font.render("-", True, BLACK)
        self.screen.blit(text, (self.buttons['mutation_rate_min_dec'].x + 7, self.buttons['mutation_rate_min_dec'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['mutation_rate_max_inc'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['mutation_rate_max_inc'], 2)
        text = self.small_font.render("+", True, BLACK)
        self.screen.blit(text, (self.buttons['mutation_rate_max_inc'].x + 7, self.buttons['mutation_rate_max_inc'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['mutation_rate_max_dec'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['mutation_rate_max_dec'], 2)
        text = self.small_font.render("-", True, BLACK)
        self.screen.blit(text, (self.buttons['mutation_rate_max_dec'].x + 7, self.buttons['mutation_rate_max_dec'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['crossover_rate_min_inc'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['crossover_rate_min_inc'], 2)
        text = self.small_font.render("+", True, BLACK)
        self.screen.blit(text, (self.buttons['crossover_rate_min_inc'].x + 7, self.buttons['crossover_rate_min_inc'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['crossover_rate_min_dec'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['crossover_rate_min_dec'], 2)
        text = self.small_font.render("-", True, BLACK)
        self.screen.blit(text, (self.buttons['crossover_rate_min_dec'].x + 7, self.buttons['crossover_rate_min_dec'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['crossover_rate_max_inc'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['crossover_rate_max_inc'], 2)
        text = self.small_font.render("+", True, BLACK)
        self.screen.blit(text, (self.buttons['crossover_rate_max_inc'].x + 7, self.buttons['crossover_rate_max_inc'].y + 5))

        pygame.draw.rect(self.screen, WHITE, self.buttons['crossover_rate_max_dec'])
        pygame.draw.rect(self.screen, BLACK, self.buttons['crossover_rate_max_dec'], 2)
        text = self.small_font.render("-", True, BLACK)
        self.screen.blit(text, (self.buttons['crossover_rate_max_dec'].x + 7, self.buttons['crossover_rate_max_dec'].y + 5))

        # Informações
        y_offset = 650
        info_texts = [
            f"Cities: {len(self.cities)}",
            f"Population: {self.population_size}",
            f"Generation: {self.current_generation}/{self.max_generations}",
            f"Best Distance: {1/self.best_fitness:.2f}" if self.best_fitness > 0 else "Best Distance: N/A"
        ]

        for i, text in enumerate(info_texts):
            rendered = self.font.render(text, True, BLACK)
            self.screen.blit(rendered, (20, y_offset + i * 30))

        # Parâmetros
        y_offset = 500
        param_texts = [
            "Parameters:",
            f"Mutation Rate: {self.mutation_rate_min:.2f} - {self.mutation_rate_max:.2f}",
            f"Crossover Rate: {self.crossover_rate_min:.2f} - {self.crossover_rate_max:.2f}",
            f"Elitism: {'On' if self.elitism else 'Off'}"
        ]

        for i, text in enumerate(param_texts):
            font = self.font if i == 0 else self.small_font
            rendered = font.render(text, True, BLACK)
            self.screen.blit(rendered, (20, y_offset + i * 25))

        # Gráfico de fitness (simplificado)
        if len(self.fitness_history) > 1:
            self.draw_fitness_graph()
    
    def draw_fitness_graph(self):
        """Desenha um gráfico simples do histórico de fitness"""
        graph_rect = pygame.Rect(20, 550, 320, 200)
        pygame.draw.rect(self.screen, WHITE, graph_rect)
        pygame.draw.rect(self.screen, BLACK, graph_rect, 2)
        
        # Título do gráfico
        title = self.font.render("Fitness History", True, BLACK)
        self.screen.blit(title, (graph_rect.x + 10, graph_rect.y - 25))
        
        if len(self.fitness_history) < 2:
            return
        
        # Normalizar dados
        max_fitness = max(self.fitness_history)
        min_fitness = min(self.fitness_history)
        
        if max_fitness == min_fitness:
            return
        
        # Desenhar linhas
        points_max = []
        points_mean = []
        
        for i, (max_f, mean_f) in enumerate(zip(self.fitness_history, self.mean_fitness_history)):
            x = graph_rect.x + (i / len(self.fitness_history)) * graph_rect.width
            y_max = graph_rect.bottom - ((max_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            y_mean = graph_rect.bottom - ((mean_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            
            points_max.append((x, y_max))
            points_mean.append((x, y_mean))
        
        if len(points_max) > 1:
            pygame.draw.lines(self.screen, RED, False, points_max, 2)
        if len(points_mean) > 1:
            pygame.draw.lines(self.screen, GREEN, False, points_mean, 2)
        
        # Legenda
        legend_y = graph_rect.bottom + 10
        pygame.draw.line(self.screen, RED, (graph_rect.x, legend_y), (graph_rect.x + 20, legend_y), 2)
        text = self.small_font.render("Max Fitness", True, BLACK)
        self.screen.blit(text, (graph_rect.x + 25, legend_y - 8))
        
        pygame.draw.line(self.screen, GREEN, (graph_rect.x + 120, legend_y), (graph_rect.x + 140, legend_y), 2)
        text = self.small_font.render("Mean Fitness", True, BLACK)
        self.screen.blit(text, (graph_rect.x + 145, legend_y - 8))
    
    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas"""
        if self.map_type == "custom" and pos[0] > 370:  # Só na área do mapa
            self.cities.append(Cidade(pos[0], pos[1]))
            if len(self.cities) > 1:
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
                    if self.cities:
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
                    self.cities = []

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
                    if self.cities:
                        self.start_algorithm()
                elif event.key == pygame.K_ESCAPE:
                    if self.running_algorithm:
                        self.stop_algorithm()
                    else:
                        return False

        return True
    
    def start_algorithm(self):
        """Inicia o algoritmo genético"""
        if not self.cities:
            return
        
        self.running_algorithm = True
        self.current_generation = 0
        self.best_fitness = 0
        self.best_chromosome = None
        self.fitness_history = []
        self.mean_fitness_history = []
        self.initialize_population()
    
    def stop_algorithm(self):
        """Para o algoritmo genético"""
        self.running_algorithm = False
    
    def reset_algorithm(self):
        """Reseta o algoritmo e limpa os dados"""
        self.running_algorithm = False
        self.cities = []
        self.population = []
        self.current_generation = 0
        self.best_fitness = 0
        self.best_chromosome = None
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
            
            # Desenhar interface
            self.draw_interface()
            
            # Desenhar cidades e rotas
            if self.cities:
                # Desenhar melhor rota
                if self.best_chromosome:
                    self.draw_route(self.best_chromosome, RED, 3)
                
                # Desenhar rota da geração atual
                if self.population and self.running_algorithm:
                    fitness_scores = [self.calculate_fitness(chrom) for chrom in self.population]
                    if fitness_scores:
                        best_idx = fitness_scores.index(max(fitness_scores))
                        current_best = self.population[best_idx]
                        self.draw_route(current_best, BLUE, 2)
                
                self.draw_cities()
            
            # Instruções para modo customizado
            if self.map_type == "custom" and not self.cities:
                instruction = self.font.render("Click on the map to add cities", True, BLACK)
                self.screen.blit(instruction, (400, 400))
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = TSPGeneticAlgorithm()
    app.run()