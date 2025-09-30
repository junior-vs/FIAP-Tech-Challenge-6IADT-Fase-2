import pygame
from typing import Any, Dict, Tuple

# constantes de cor locais (compatíveis com o arquivo principal)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)


class DrawFunctions:
    """Coleção de funções de desenho / UI para o TSP pygame app."""

    @staticmethod
    def create_buttons() -> Dict[str, pygame.Rect]:
        return {
            'generate_map': pygame.Rect(50, 50, 120, 30),
            'reset': pygame.Rect(180, 50, 120, 30),
            'map_random': pygame.Rect(50, 100, 80, 25),
            'map_circle': pygame.Rect(140, 100, 80, 25),
            'map_custom': pygame.Rect(230, 100, 80, 25),
            'toggle_elitism': pygame.Rect(50, 150, 120, 30),
            # Botões para métodos de mutação
            'mutation_swap': pygame.Rect(50, 200, 60, 25),
            'mutation_inverse': pygame.Rect(115, 200, 60, 25),
            'mutation_shuffle': pygame.Rect(180, 200, 60, 25),
            # Botões para métodos de crossover
            'crossover_pmx': pygame.Rect(50, 250, 50, 25),
            'crossover_ox1': pygame.Rect(105, 250, 50, 25),
            'crossover_cx': pygame.Rect(160, 250, 50, 25),
            'crossover_kpoint': pygame.Rect(215, 250, 50, 25),
            'crossover_erx': pygame.Rect(270, 250, 50, 25),
            'run_algorithm': pygame.Rect(50, 300, 120, 30),
            'stop_algorithm': pygame.Rect(180, 300, 120, 30),
        }

    @staticmethod
    def draw_cities(app: Any) -> None:
        """Desenha pontos de entrega (usa atributos do app)."""
        for i, cidade in enumerate(app.delivery_points):
            x, y = cidade.x, cidade.y
            pygame.draw.circle(app.screen, BLUE, (x, y), 8)
            pygame.draw.circle(app.screen, WHITE, (x, y), 6)
            text = app.small_font.render(str(i), True, BLACK)
            text_rect = text.get_rect(center=(x, y))
            app.screen.blit(text, text_rect)

    @staticmethod
    def draw_route(app: Any, chromosome: Any, color: Tuple[int, int, int] = BLACK, width: int = 2) -> None:
        """Desenha uma rota.

        Aceita três formatos para `chromosome` para compatibilidade:
        - Route object (tem atributo `delivery_points`)
        - lista de índices (List[int]) referenciando `app.delivery_points`
        - lista de DeliveryPoint-like objects (tem .x, .y)
        """
        if not chromosome:
            return

        # Normalize to a list of delivery-point-like objects
        pts = None

        # Route-like (duck typing)
        if hasattr(chromosome, 'delivery_points'):
            pts = list(chromosome.delivery_points)
        # list of indices
        elif isinstance(chromosome, list) and chromosome and isinstance(chromosome[0], int):
            pts = [app.delivery_points[i] for i in chromosome]
        # list of delivery-point-like objects
        elif isinstance(chromosome, list):
            pts = list(chromosome)
        else:
            return

        if len(pts) < 2:
            return

        points = [(p.x, p.y) for p in pts]
        # close the loop
        points.append((pts[0].x, pts[0].y))
        if len(points) > 1:
            pygame.draw.lines(app.screen, color, False, points, width)

    @staticmethod
    def draw_fitness_graph(app: Any) -> None:
        """Desenha um gráfico simples do histórico de fitness (usa app.fitness_history)."""
        graph_rect = pygame.Rect(20, 550, 320, 200)
        pygame.draw.rect(app.screen, WHITE, graph_rect)
        pygame.draw.rect(app.screen, BLACK, graph_rect, 2)
        title = app.font.render("Fitness History", True, BLACK)
        app.screen.blit(title, (graph_rect.x + 10, graph_rect.y - 25))
        if len(app.fitness_history) < 2:
            return
        max_fitness = max(app.fitness_history)
        min_fitness = min(app.fitness_history)
        if max_fitness == min_fitness:
            return
        points_max = []
        points_mean = []
        for i, (max_f, mean_f) in enumerate(zip(app.fitness_history, app.mean_fitness_history)):
            x = graph_rect.x + (i / max(1, len(app.fitness_history)-1)) * graph_rect.width
            y_max = graph_rect.bottom - ((max_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            y_mean = graph_rect.bottom - ((mean_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            points_max.append((x, y_max))
            points_mean.append((x, y_mean))
        if len(points_max) > 1:
            pygame.draw.lines(app.screen, RED, False, points_max, 2)
        if len(points_mean) > 1:
            pygame.draw.lines(app.screen, GREEN, False, points_mean, 2)
        legend_y = graph_rect.bottom + 10
        pygame.draw.line(app.screen, RED, (graph_rect.x, legend_y), (graph_rect.x + 20, legend_y), 2)
        text = app.small_font.render("Max Fitness", True, BLACK)
        app.screen.blit(text, (graph_rect.x + 25, legend_y - 8))
        pygame.draw.line(app.screen, GREEN, (graph_rect.x + 120, legend_y), (graph_rect.x + 140, legend_y), 2)
        text = app.small_font.render("Mean Fitness", True, BLACK)
        app.screen.blit(text, (graph_rect.x + 145, legend_y - 8))

    @staticmethod
    def draw_interface(app: Any) -> None:
        """Desenha a interface do usuário (controles, botões, parâmetros)."""
        # fundo controles
        pygame.draw.rect(app.screen, LIGHT_GRAY, (10, 10, 350, 780))
        title = app.font.render("TSP - Genetic Algorithm", True, BLACK)
        app.screen.blit(title, (20, 20))
        button_color = WHITE if not app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, button_color, app.buttons['generate_map'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['generate_map'], 2)
        text = app.font.render("Generate Map", True, BLACK)
        app.screen.blit(text, (app.buttons['generate_map'].x + 5, app.buttons['generate_map'].y + 5))
        run_color = GREEN if not app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, run_color, app.buttons['run_algorithm'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['run_algorithm'], 2)
        text = app.font.render("Run Algorithm", True, BLACK)
        app.screen.blit(text, (app.buttons['run_algorithm'].x + 5, app.buttons['run_algorithm'].y + 5))
        stop_color = RED if app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, stop_color, app.buttons['stop_algorithm'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['stop_algorithm'], 2)
        text = app.font.render("Stop", True, BLACK)
        app.screen.blit(text, (app.buttons['stop_algorithm'].x + 40, app.buttons['stop_algorithm'].y + 5))
        pygame.draw.rect(app.screen, WHITE, app.buttons['reset'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['reset'], 2)
        text = app.font.render("Reset", True, BLACK)
        app.screen.blit(text, (app.buttons['reset'].x + 40, app.buttons['reset'].y + 5))
        map_types = ['map_random', 'map_circle', 'map_custom']
        map_labels = ['Random', 'Circle', 'Custom']
        for i, (btn_name, label) in enumerate(zip(map_types, map_labels)):
            color = GREEN if app.map_type == label.lower() else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            app.screen.blit(text, (app.buttons[btn_name].x + 5, app.buttons[btn_name].y + 5))
        elitism_color = GREEN if app.elitism else RED
        pygame.draw.rect(app.screen, elitism_color, app.buttons['toggle_elitism'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['toggle_elitism'], 2)
        text = app.small_font.render(f"Elitism: {'On' if app.elitism else 'Off'}", True, BLACK)
        app.screen.blit(text, (app.buttons['toggle_elitism'].x + 10, app.buttons['toggle_elitism'].y + 5))
        
        # Botões de método de mutação
        mutation_methods = [
            ('mutation_swap', 'Swap', 'swap'),
            ('mutation_inverse', 'Inverse', 'inverse'),
            ('mutation_shuffle', 'Shuffle', 'shuffle')
        ]

        # Label para métodos de mutação
        mutation_label = app.small_font.render("Mutation Method:", True, BLACK)
        app.screen.blit(mutation_label, (50, 180))

        for btn_name, label, method in mutation_methods:
            color = GREEN if app.mutation_method == method else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            text_rect = text.get_rect(center=app.buttons[btn_name].center)
            app.screen.blit(text, text_rect)
        
        # Botões de método de crossover
        crossover_methods = [
            ('crossover_pmx', 'PMX', 'pmx'),
            ('crossover_ox1', 'OX1', 'ox1'),
            ('crossover_cx', 'CX', 'cx'),
            ('crossover_kpoint', 'K-Pt', 'kpoint'),
            ('crossover_erx', 'ERX', 'erx')
        ]

        # Label para métodos de crossover
        crossover_label = app.small_font.render("Crossover Method:", True, BLACK)
        app.screen.blit(crossover_label, (50, 230))

        for btn_name, label, method in crossover_methods:
            color = GREEN if app.crossover_method == method else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            text_rect = text.get_rect(center=app.buttons[btn_name].center)
            app.screen.blit(text, text_rect)
        # info texts
        y_offset = 650
        info_texts = [
            f"Cities: {len(app.delivery_points)}",
            f"Population: {app.population_size}",
            f"Generation: {app.current_generation}/{app.max_generations}",
            f"Best Distance: {1/app.best_fitness:.2f}" if app.best_fitness > 0 else "Best Distance: N/A"
        ]
        for i, text in enumerate(info_texts):
            rendered = app.font.render(text, True, BLACK)
            app.screen.blit(rendered, (20, y_offset + i * 30))
        # parameters
        y_offset = 500
        param_texts = [
            "Parameters:",
            f"Mutation Method: {app.mutation_method.upper()}",
            f"Crossover Method: {app.crossover_method.upper()}",
            f"Elitism: {'On' if app.elitism else 'Off'}"
        ]
        for i, text in enumerate(param_texts):
            font = app.font if i == 0 else app.small_font
            rendered = font.render(text, True, BLACK)
            app.screen.blit(rendered, (20, y_offset + i * 25))
        # fitness graph
        if len(app.fitness_history) > 1:
            DrawFunctions.draw_fitness_graph(app)
