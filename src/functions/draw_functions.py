import pygame
from typing import Any, Tuple
from ui_layout import UILayout

# Usar cores centralizadas
WHITE = UILayout.get_color('white')
BLACK = UILayout.get_color('black')
BLUE = UILayout.get_color('blue')
RED = UILayout.get_color('red')
GREEN = UILayout.get_color('green')
GRAY = UILayout.get_color('gray')
LIGHT_GRAY = UILayout.get_color('light_gray')


class DrawFunctions:
    """Coleção de funções de desenho / UI para o TSP pygame app."""

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
        """Desenha um gráfico simples do histórico de fitness usando configurações centralizadas."""
        # Define a área do gráfico usando configurações centralizadas
        graph_rect = pygame.Rect(UILayout.FitnessGraph.X, UILayout.FitnessGraph.Y, 
                                UILayout.FitnessGraph.WIDTH, UILayout.FitnessGraph.HEIGHT)
        
        # Desenha o fundo branco do gráfico para contraste
        pygame.draw.rect(app.screen, WHITE, graph_rect)
        # Desenha a borda preta do gráfico para definição visual
        pygame.draw.rect(app.screen, BLACK, graph_rect, 2)
        
        # Renderiza e posiciona o título do gráfico acima da área
        title = app.font.render("Fitness History", True, BLACK)
        app.screen.blit(title, (graph_rect.x + 10, graph_rect.y - 25))
        
        # Verifica se temos dados suficientes para desenhar o gráfico (mínimo 2 pontos)
        if not hasattr(app, 'fitness_history') or len(app.fitness_history) < 2:
            return
        
        # Verifica se existe o atributo mean_fitness_history, se não, inicializa como lista vazia
        # Isso previne erros caso o atributo não tenha sido criado no app principal
        if not hasattr(app, 'mean_fitness_history'):
            app.mean_fitness_history = []
        
        # Garante que ambas as listas tenham dados suficientes para plotar
        # Usa o menor tamanho entre as duas listas para evitar index out of range
        min_length = min(len(app.fitness_history), len(app.mean_fitness_history))
        if min_length < 2:
            return
        
        # Calcula os valores máximo e mínimo para normalização do gráfico
        # Considera tanto fitness máximo quanto médio para uma escala consistente
        all_values = list(app.fitness_history[:min_length]) + list(app.mean_fitness_history[:min_length])
        max_fitness = max(all_values)
        min_fitness = min(all_values)
        
        # Se todos os valores são iguais, não há variação para plotar
        if max_fitness == min_fitness:
            return
        
        # Listas para armazenar os pontos calculados do gráfico
        points_max = []   # Pontos para a linha do fitness máximo (melhor da geração)
        points_mean = []  # Pontos para a linha do fitness médio (média da população)
        
        # Gera os pontos para plotagem convertendo dados em coordenadas de tela
        for i in range(min_length):
            max_f = app.fitness_history[i]     # Fitness máximo da geração i
            mean_f = app.mean_fitness_history[i]  # Fitness médio da geração i
            
            # Calcula a posição X baseada no índice da geração (distribui uniformemente)
            # Evita divisão por zero usando max(1, min_length - 1)
            x = graph_rect.x + (i / max(1, min_length - 1)) * graph_rect.width
            
            # Calcula a posição Y para o fitness máximo (normalizada entre min e max)
            # Inverte Y porque em pygame (0,0) é no canto superior esquerdo
            y_max = graph_rect.bottom - ((max_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            
            # Calcula a posição Y para o fitness médio (normalizada entre min e max)
            y_mean = graph_rect.bottom - ((mean_f - min_fitness) / (max_fitness - min_fitness)) * graph_rect.height
            
            # Adiciona os pontos calculados às listas de coordenadas
            points_max.append((x, y_max))
            points_mean.append((x, y_mean))
        
        # Desenha a linha do fitness máximo em vermelho (mostra evolução do melhor indivíduo)
        if len(points_max) > 1:
            pygame.draw.lines(app.screen, RED, False, points_max, 2)
        
        # Desenha a linha do fitness médio em verde (mostra evolução da população)
        if len(points_mean) > 1:
            pygame.draw.lines(app.screen, GREEN, False, points_mean, 2)
        
        # Desenha a legenda abaixo do gráfico usando configurações centralizadas
        legend_y = graph_rect.bottom + UILayout.FitnessGraph.LEGEND_Y_OFFSET
        
        # Linha vermelha da legenda para fitness máximo
        pygame.draw.line(app.screen, RED, 
                        (graph_rect.x, legend_y), 
                        (graph_rect.x + UILayout.FitnessGraph.LEGEND_LINE_LENGTH, legend_y), 2)
        text = app.small_font.render("Max Fitness", True, BLACK)
        app.screen.blit(text, (graph_rect.x + UILayout.FitnessGraph.LEGEND_LINE_LENGTH + 
                              UILayout.FitnessGraph.LEGEND_TEXT_OFFSET, legend_y - 8))
        
        # Linha verde da legenda para fitness médio
        pygame.draw.line(app.screen, GREEN, 
                        (graph_rect.x + UILayout.FitnessGraph.LEGEND_SPACING, legend_y), 
                        (graph_rect.x + UILayout.FitnessGraph.LEGEND_SPACING + 
                         UILayout.FitnessGraph.LEGEND_LINE_LENGTH, legend_y), 2)
        text = app.small_font.render("Mean Fitness", True, BLACK)
        app.screen.blit(text, (graph_rect.x + UILayout.FitnessGraph.LEGEND_SPACING + 
                              UILayout.FitnessGraph.LEGEND_LINE_LENGTH + 
                              UILayout.FitnessGraph.LEGEND_TEXT_OFFSET, legend_y - 8))

    @staticmethod
    def draw_interface(app: Any) -> None:
        """Desenha a interface do usuário completa com controles, botões e informações.
        
        Este método é o ponto de entrada principal para desenhar toda a interface lateral.
        Divide o desenho em seções lógicas para melhor organização.
        """
        # Desenha o fundo da área de controles
        DrawFunctions._draw_background_and_title(app)
        
        # Desenha todos os botões principais de controle
        DrawFunctions._draw_main_control_buttons(app)
        
        # Desenha os botões de seleção de tipo de mapa
        DrawFunctions._draw_map_type_buttons(app)
        
        # Desenha os controles de número de cidades
        DrawFunctions._draw_city_count_controls(app)
        
        # Desenha o botão de toggle do elitismo
        DrawFunctions._draw_elitism_button(app)
        
        # Desenha os botões de seleção de método de seleção
        DrawFunctions._draw_selection_method_buttons(app)
        
        # Desenha os botões de seleção de método de mutação
        DrawFunctions._draw_mutation_method_buttons(app)
        
        # Desenha os botões de seleção de método de crossover
        DrawFunctions._draw_crossover_method_buttons(app)
        
        # Desenha as informações de parâmetros atuais
        DrawFunctions._draw_parameters_info(app)
        
        # Desenha as informações do algoritmo em tempo real
        DrawFunctions._draw_algorithm_info(app)
        
        # Desenha o gráfico de fitness se houver dados
        if hasattr(app, 'fitness_history') and len(app.fitness_history) > 1:
            DrawFunctions.draw_fitness_graph(app)

    @staticmethod
    def _draw_background_and_title(app: Any) -> None:
        """Desenha o fundo da área de controles e o título principal."""
        # Desenha o fundo cinza claro para a área de controles usando configurações centralizadas
        control_rect = (UILayout.ControlPanel.X, UILayout.ControlPanel.Y, 
                       UILayout.ControlPanel.WIDTH, UILayout.ControlPanel.HEIGHT)
        pygame.draw.rect(app.screen, LIGHT_GRAY, control_rect)
        
        # Renderiza e posiciona o título principal da aplicação
        title = app.font.render("TSP - Genetic Algorithm", True, BLACK)
        app.screen.blit(title, (UILayout.ControlPanel.MARGIN_LEFT, UILayout.ControlPanel.TITLE_Y))

    @staticmethod
    def _draw_main_control_buttons(app: Any) -> None:
        """Desenha os botões principais de controle (Generate, Run, Stop, Reset)."""
        # Botão Generate Map - desabilitado durante execução do algoritmo
        button_color = WHITE if not app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, button_color, app.buttons['generate_map'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['generate_map'], 2)
        text = app.font.render("Generate Map", True, BLACK)
        app.screen.blit(text, (app.buttons['generate_map'].x + 5, app.buttons['generate_map'].y + 5))
        
        # Botão Run Algorithm - verde quando disponível, cinza quando executando
        run_color = GREEN if not app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, run_color, app.buttons['run_algorithm'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['run_algorithm'], 2)
        text = app.font.render("Run Algorithm", True, BLACK)
        app.screen.blit(text, (app.buttons['run_algorithm'].x + 5, app.buttons['run_algorithm'].y + 5))
        
        # Botão Stop Algorithm - vermelho quando executando, cinza quando parado
        stop_color = RED if app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, stop_color, app.buttons['stop_algorithm'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['stop_algorithm'], 2)
        text = app.font.render("Stop", True, BLACK)
        app.screen.blit(text, (app.buttons['stop_algorithm'].x + 40, app.buttons['stop_algorithm'].y + 5))
        
        # Botão Reset - sempre disponível
        pygame.draw.rect(app.screen, WHITE, app.buttons['reset'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['reset'], 2)
        text = app.font.render("Reset", True, BLACK)
        app.screen.blit(text, (app.buttons['reset'].x + 40, app.buttons['reset'].y + 5))

    @staticmethod
    def _draw_map_type_buttons(app: Any) -> None:
        """Desenha os botões de seleção do tipo de mapa (Random, Circle, Custom)."""
        map_types = ['map_random', 'map_circle', 'map_custom']
        map_labels = ['Random', 'Circle', 'Custom']
        
        # Itera pelos tipos de mapa e desenha cada botão
        for btn_name, label in zip(map_types, map_labels):
            # Destaca o tipo de mapa atualmente selecionado em verde
            color = GREEN if app.map_type == label.lower() else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            app.screen.blit(text, (app.buttons[btn_name].x + 5, app.buttons[btn_name].y + 5))

    @staticmethod
    def _draw_city_count_controls(app: Any) -> None:
        """Desenha os controles para alterar o número de cidades."""
        # Label explicativo usando configurações centralizadas
       # cities_label = app.small_font.render("Number of Cities:", True, BLACK)
       # app.screen.blit(cities_label, (UILayout.ControlPanel.MARGIN_LEFT + 30, UILayout.Text.CITY_COUNT_LABEL_Y))
        
        # Botão de diminuir (-) - só funciona se não estiver executando algoritmo
        button_color = WHITE if not app.running_algorithm else GRAY
        pygame.draw.rect(app.screen, button_color, app.buttons['cities_minus'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['cities_minus'], 2)
        minus_text = app.font.render("-", True, BLACK)
        minus_rect = minus_text.get_rect(center=app.buttons['cities_minus'].center)
        app.screen.blit(minus_text, minus_rect)
        
        # Campo de exibição do número atual de cidades usando configurações centralizadas
        cities_display = pygame.Rect(UILayout.SpecialElements.CITIES_DISPLAY_X, 
                                    UILayout.SpecialElements.CITIES_DISPLAY_Y,
                                    UILayout.SpecialElements.CITIES_DISPLAY_WIDTH, 
                                    UILayout.SpecialElements.CITIES_DISPLAY_HEIGHT)
        pygame.draw.rect(app.screen, WHITE, cities_display)
        pygame.draw.rect(app.screen, BLACK, cities_display, 2)
        cities_text = app.font.render(f"Cities: {app.num_cities}", True, BLACK)
        cities_text_rect = cities_text.get_rect(center=cities_display.center)
        app.screen.blit(cities_text, cities_text_rect)
        
        # Botão de aumentar (+) - só funciona se não estiver executando algoritmo
        pygame.draw.rect(app.screen, button_color, app.buttons['cities_plus'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['cities_plus'], 2)
        plus_text = app.font.render("+", True, BLACK)
        plus_rect = plus_text.get_rect(center=app.buttons['cities_plus'].center)
        app.screen.blit(plus_text, plus_rect)

    @staticmethod
    def _draw_elitism_button(app: Any) -> None:
        """Desenha o botão de toggle do elitismo."""
        # Verde se elitismo está ativado, vermelho se desativado
        elitism_color = GREEN if app.elitism else RED
        pygame.draw.rect(app.screen, elitism_color, app.buttons['toggle_elitism'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['toggle_elitism'], 2)
        text = app.small_font.render(f"Elitism: {'On' if app.elitism else 'Off'}", True, BLACK)
        app.screen.blit(text, (app.buttons['toggle_elitism'].x + 10, app.buttons['toggle_elitism'].y + 5))

    @staticmethod
    def _draw_selection_method_buttons(app: Any) -> None:
        """Desenha os botões de seleção de método de seleção."""
        # Define os métodos de seleção disponíveis
        selection_methods = [
            ('selection_roulette', 'Roleta', 'roulette'),
            ('selection_tournament', 'Torneio', 'tournament'),
            ('selection_rank', 'Ranking', 'rank')
        ]

        # Label explicativo usando configurações centralizadas
        selection_label = app.small_font.render("Selection Method:", True, BLACK)
        app.screen.blit(selection_label, (UILayout.ControlPanel.MARGIN_LEFT + 30, UILayout.Text.SELECTION_LABEL_Y))

        # Desenha cada botão de método de seleção
        for btn_name, label, method in selection_methods:
            if btn_name in app.buttons:
                button_rect = app.buttons[btn_name]
                # Destaca o método atualmente selecionado em azul
                color = BLUE if app.selection_method == method else WHITE
                pygame.draw.rect(app.screen, color, button_rect)
                pygame.draw.rect(app.screen, BLACK, button_rect, 2)
                text = app.small_font.render(label, True, BLACK)
                text_rect = text.get_rect(center=button_rect.center)
                app.screen.blit(text, text_rect)

    @staticmethod
    def _draw_mutation_method_buttons(app: Any) -> None:
        """Desenha os botões de seleção do método de mutação."""
        # Define os métodos de mutação disponíveis
        mutation_methods = [
            ('mutation_swap', 'Swap', 'swap'),
            ('mutation_inverse', 'Inverse', 'inverse'),
            ('mutation_shuffle', 'Shuffle', 'shuffle')
        ]

        # Label explicativo usando configurações centralizadas
        mutation_label = app.small_font.render("Mutation Method:", True, BLACK)
        app.screen.blit(mutation_label, (UILayout.ControlPanel.MARGIN_LEFT + 30, UILayout.Text.MUTATION_LABEL_Y))

        # Desenha cada botão de método de mutação
        for btn_name, label, method in mutation_methods:
            # Destaca o método atualmente selecionado em verde
            color = GREEN if app.mutation_method == method else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            text_rect = text.get_rect(center=app.buttons[btn_name].center)
            app.screen.blit(text, text_rect)

    @staticmethod
    def _draw_crossover_method_buttons(app: Any) -> None:
        """Desenha os botões de seleção do método de crossover."""
        # Define os métodos de crossover disponíveis
        crossover_methods = [
            ('crossover_pmx', 'PMX', 'pmx'),
            ('crossover_ox1', 'OX1', 'ox1'),
            ('crossover_cx', 'CX', 'cx'),
            ('crossover_kpoint', 'K-Pt', 'kpoint'),
            ('crossover_erx', 'ERX', 'erx')
        ]

        # Label explicativo usando configurações centralizadas
        crossover_label = app.small_font.render("Crossover Method:", True, BLACK)
        app.screen.blit(crossover_label, (UILayout.ControlPanel.MARGIN_LEFT + 30, UILayout.Text.CROSSOVER_LABEL_Y))

        # Desenha cada botão de método de crossover
        for btn_name, label, method in crossover_methods:
            # Destaca o método atualmente selecionado em verde
            color = GREEN if app.crossover_method == method else WHITE
            pygame.draw.rect(app.screen, color, app.buttons[btn_name])
            pygame.draw.rect(app.screen, BLACK, app.buttons[btn_name], 2)
            text = app.small_font.render(label, True, BLACK)
            text_rect = text.get_rect(center=app.buttons[btn_name].center)
            app.screen.blit(text, text_rect)

    @staticmethod
    def _draw_parameters_info(app: Any) -> None:
        """Desenha as informações dos parâmetros atuais do algoritmo."""
        y_offset = UILayout.ControlPanel.PARAMETERS_INFO_Y
        
        # Lista de textos dos parâmetros para exibir
        param_texts = [
            "Parameters:",
            f"Mutation Method: {app.mutation_method.upper()}",
            f"Crossover Method: {app.crossover_method.upper()}",
            f"Elitism: {'On' if app.elitism else 'Off'}"
        ]
        
        # Desenha cada linha de parâmetro
        for i, text in enumerate(param_texts):
            # Usa fonte maior para o título, fonte menor para os parâmetros
            font = app.font if i == 0 else app.small_font
            rendered = font.render(text, True, BLACK)
            app.screen.blit(rendered, (UILayout.ControlPanel.MARGIN_LEFT, y_offset + i * UILayout.Text.LINE_HEIGHT))

    @staticmethod
    def _draw_algorithm_info(app: Any) -> None:
        """Desenha as informações em tempo real do algoritmo (cidades, geração, fitness)."""
        y_offset = UILayout.ControlPanel.ALGORITHM_INFO_Y
        
        # Lista de informações do estado atual do algoritmo
        info_texts = [
            f"Cities: {len(app.delivery_points)}",
            f"Population: {app.population_size}",
            f"Generation: {app.current_generation}/{app.max_generations}",
            # Calcula distância a partir do fitness (fitness = 1/distância)
            f"Best Distance: {1/app.best_fitness:.2f}" if app.best_fitness > 0 else "Best Distance: N/A"
        ]
        
        # Desenha cada linha de informação
        for i, text in enumerate(info_texts):
            rendered = app.font.render(text, True, BLACK)
            app.screen.blit(rendered, (UILayout.ControlPanel.MARGIN_LEFT, y_offset + i * UILayout.Text.SECTION_SPACING))
