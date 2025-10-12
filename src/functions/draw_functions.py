import pygame
from typing import Any, Tuple, List, Dict
from src.functions.ui_layout import UILayout

WHITE = UILayout.get_color('white')
BLACK = UILayout.get_color('black')
BLUE  = UILayout.get_color('blue')
RED   = UILayout.get_color('red')
GREEN = UILayout.get_color('green')
GRAY  = UILayout.get_color('gray')
LGRAY = UILayout.get_color('light_gray')
DGRAY = UILayout.get_color('dark_gray')
YELL  = UILayout.get_color('yellow')


def _card(screen, x, y, w, h, title, font):
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, WHITE, r, border_radius=6)
    pygame.draw.rect(screen, DGRAY, r, 2, border_radius=6)
    screen.blit(font.render(title, True, BLACK), (x + 10, y + 6))
    pygame.draw.line(screen, LGRAY, (x + 8, y + 30), (x + w - 8, y + 30), 1)
    return r


class DrawFunctions:
    """
    Classe responsável por toda a renderização da interface gráfica do algoritmo genético TSP/VRP.
    
    Esta classe implementa o padrão Single Responsibility Principle (SRP) com métodos modulares
    que separam claramente a lógica de negócio da apresentação visual.
    
    Características principais:
    - Interface modular dividida em seções independentes
    - Renderização eficiente usando Pygame
    - Suporte completo a TSP e VRP com múltiplas rotas
    - Visualização de prioridades e estatísticas em tempo real
    
    Dependências:
    - pygame: Para renderização gráfica
    - UILayout: Para configurações centralizadas de layout e cores
    """

    # -------------------- MAPA À DIREITA --------------------
    @staticmethod
    def _draw_map_board(app: Any) -> None:
        ma = UILayout.MapArea
        board = pygame.Rect(ma.X, ma.Y, ma.WIDTH, ma.HEIGHT)
        inner = pygame.Rect(ma.CITIES_X, ma.CITIES_Y, ma.CITIES_WIDTH, ma.CITIES_HEIGHT)
        pygame.draw.rect(app.screen, WHITE, board, border_radius=6)
        pygame.draw.rect(app.screen, DGRAY, board, 2, border_radius=6)
        step = 40
        for x in range(inner.left, inner.right, step):
            pygame.draw.line(app.screen, LGRAY, (x, inner.top), (x, inner.bottom), 1)
        for y in range(inner.top, inner.bottom, step):
            pygame.draw.line(app.screen, LGRAY, (inner.left, y), (inner.right, y), 1)
        pygame.draw.rect(app.screen, GRAY, inner, 1)

    # -------------------- GRÁFICO --------------------
    @staticmethod
    def draw_fitness_graph(app: Any) -> None:
        """
        Renderiza gráfico de evolução do fitness ao longo das gerações.
        
        O gráfico exibe duas linhas:
        - Vermelha: Melhor fitness de cada geração (máximo)
        - Verde: Fitness médio da população
        
        Características:
        - Escala automática baseada nos valores min/max
        - Tratamento robusto de casos extremos (dados insuficientes, valores iguais)
        - Renderização eficiente com pygame.draw.lines
        
        Args:
            app: Instância da aplicação contendo fitness_history e mean_fitness_history
        """
        cp = UILayout.ControlPanel
        x = cp.X + cp.PAD
        w = cp.WIDTH - 2*cp.PAD

        # Calcula área interna do gráfico (descontando bordas e título)
        inner_x = x + 8
        inner_y = cp.FITNESS_Y + 36 + 4
        inner_w = w - 16
        inner_h = cp.FITNESS_H - 36 - 16

        # Desenha fundo do gráfico
        fr = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect(app.screen, WHITE, fr)
        pygame.draw.rect(app.screen, BLACK, fr, 2)

        # Validações de pré-condições
        if not hasattr(app, 'fitness_history') or len(app.fitness_history) < 2:
            return
        if not hasattr(app, 'mean_fitness_history'):
            app.mean_fitness_history = []

        # Sincroniza arrays para mesmo tamanho
        n = min(len(app.fitness_history), len(app.mean_fitness_history))
        if n < 2:
            return

        # Calcula escala baseada em min/max de ambas as séries
        vals = list(app.fitness_history[:n]) + list(app.mean_fitness_history[:n])
        vmin, vmax = min(vals), max(vals)
        if vmax == vmin:  # Evita divisão por zero
            return

        # Converte dados para coordenadas de tela
        pts_max, pts_mean = [], []
        for i in range(n):
            # Distribui pontos uniformemente no eixo X
            x_pt = fr.x + (i / max(1, n - 1)) * (fr.width - 12) + 6
            
            # Mapeia valores para coordenadas Y (invertido pois tela tem origem no topo)
            y1 = fr.bottom - 6 - ((app.fitness_history[i]    - vmin) / (vmax - vmin)) * (fr.height - 12)
            y2 = fr.bottom - 6 - ((app.mean_fitness_history[i]- vmin) / (vmax - vmin)) * (fr.height - 12)
            
            pts_max.append((x_pt, y1))
            pts_mean.append((x_pt, y2))

        # Renderiza as linhas do gráfico
        pygame.draw.lines(app.screen, RED,   False, pts_max, 2)   # Melhor fitness
        pygame.draw.lines(app.screen, GREEN, False, pts_mean, 2)  # Fitness médio

    # -------------------- LATERAL ESQUERDA --------------------
    @staticmethod
    def draw_priority_slider(app):
        """
        Renderiza controle deslizante para ajuste de prioridade de produtos.
        
        O slider permite configurar percentual de prioridade que influencia:
        - A geração de produtos com prioridade nos pontos de entrega
        - A visualização destacada dos pontos prioritários
        - O cálculo de fitness considerando prioridades
        
        Componentes visuais:
        - Barra horizontal cinza como trilho
        - Handle circular azul/branco como indicador
        - Label textual mostrando percentual atual
        
        Args:
            app: Instância da aplicação contendo priority_percentage e buttons
        """
        rect = app.buttons['priority_slider']
        
        # Calcula posições do slider (trilho horizontal)
        slider_x = rect.x + 120  # Offset para label
        slider_w = rect.width - 130  # Largura disponível para trilho
        slider_y = rect.y + rect.height // 2  # Centro vertical
        
        # Desenha trilho do slider
        pygame.draw.line(app.screen, GRAY, (slider_x, slider_y), (slider_x + slider_w, slider_y), 4)
        
        # Calcula posição do handle baseada no percentual (0-100%)
        pct = max(0, min(100, int(app.priority_percentage)))  # Clamp entre 0-100
        handle_x = slider_x + int((pct / 100) * slider_w)
        
        # Desenha handle como círculo duplo (azul com centro branco)
        pygame.draw.circle(app.screen, BLUE, (handle_x, slider_y), 10)   # Círculo externo
        pygame.draw.circle(app.screen, WHITE, (handle_x, slider_y), 7)   # Círculo interno
        
        # Renderiza label com valor atual
        label = app.small_font.render(f"Priority %: {pct}", True, BLACK)
        app.screen.blit(label, (rect.x + 8, rect.y + 4))

    @staticmethod
    def _draw_setup_section(app: Any, x: int, w: int) -> None:
        """Desenha a seção de configuração (Setup)."""
        cp = UILayout.ControlPanel
        _card(app.screen, x, cp.SETUP_Y, w, cp.SETUP_H, "Setup", app.font)
        
        # Botões Generate Map e Reset
        gen_color = WHITE if not app.running_algorithm else LGRAY
        pygame.draw.rect(app.screen, gen_color, app.buttons['generate_map'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['generate_map'], 2)
        app.screen.blit(app.font.render("Generate Map", True, BLACK), 
                       (app.buttons['generate_map'].x + 8, app.buttons['generate_map'].y + 5))
        
        pygame.draw.rect(app.screen, WHITE, app.buttons['reset'])
        pygame.draw.rect(app.screen, BLACK, app.buttons['reset'], 2)
        app.screen.blit(app.font.render("Reset", True, BLACK), 
                       (app.buttons['reset'].x + 24, app.buttons['reset'].y + 5))
        
        # Botões de tipo de mapa
        for key, label in [('map_random','Random'),('map_circle','Circle'),('map_custom','Custom')]:
            rect = app.buttons[key]
            color = GREEN if app.map_type == label.lower() else WHITE
            pygame.draw.rect(app.screen, color, rect)
            pygame.draw.rect(app.screen, BLACK, rect, 2)
            text_surface = app.small_font.render(label, True, BLACK)
            app.screen.blit(text_surface, text_surface.get_rect(center=rect.center))
        
        # Controles de número de cidades
        minus_r = app.buttons['cities_minus']
        plus_r = app.buttons['cities_plus']
        cities_color = WHITE if not app.running_algorithm else LGRAY
        
        pygame.draw.rect(app.screen, cities_color, minus_r)
        pygame.draw.rect(app.screen, BLACK, minus_r, 2)
        pygame.draw.rect(app.screen, cities_color, plus_r)
        pygame.draw.rect(app.screen, BLACK, plus_r, 2)
        
        minus_text = app.font.render("-", True, BLACK)
        plus_text = app.font.render("+", True, BLACK)
        app.screen.blit(minus_text, minus_text.get_rect(center=minus_r.center))
        app.screen.blit(plus_text, plus_text.get_rect(center=plus_r.center))
        
        # Display do número de cidades
        disp_rect = pygame.Rect(minus_r.right + 8, minus_r.y, 
                               plus_r.left - (minus_r.right + 16), minus_r.height)
        pygame.draw.rect(app.screen, WHITE, disp_rect, border_radius=4)
        pygame.draw.rect(app.screen, BLACK, disp_rect, 2)
        
        cities_text = app.small_font.render(f"Cities: {app.num_cities}", True, BLACK)
        app.screen.blit(cities_text, cities_text.get_rect(center=disp_rect.center))

    @staticmethod
    def _draw_run_section(app: Any, x: int, w: int) -> None:
        """
        Desenha a seção de execução (Run) com KPIs e barra de progresso.
        
        Esta seção exibe informações em tempo real sobre o estado da execução:
        - Grid 2x2 de KPIs principais
        - Barra de progresso visual das gerações
        - Dados atualizados dinamicamente durante execução
        
        KPIs exibidos:
        1. Número de cidades carregadas
        2. Tamanho da população configurada  
        3. Geração atual / Total de gerações
        4. Melhor distância encontrada (inverso do fitness)
        
        Args:
            app: Instância da aplicação contendo estado atual da execução
            x: Posição X inicial da seção
            w: Largura disponível para a seção
        """
        cp = UILayout.ControlPanel
        _card(app.screen, x, cp.RUN_Y, w, cp.RUN_H, "Run", app.font)
        
        inner_x = x + 4
        inner_w = w - 8
        row_y = cp.RUN_Y + 36
        bw = (inner_w - 10) // 2  # Largura de cada box (2 colunas com gap)

        # Define grid 2x2 para os KPIs
        kpi_rects = [
            pygame.Rect(inner_x, row_y, bw, cp.KPI_H),                           # Top-left
            pygame.Rect(inner_x + bw + 10, row_y, bw, cp.KPI_H),               # Top-right
            pygame.Rect(inner_x, row_y + cp.KPI_H + 8, bw, cp.KPI_H),          # Bottom-left
            pygame.Rect(inner_x + bw + 10, row_y + cp.KPI_H + 8, bw, cp.KPI_H) # Bottom-right
        ]
        
        # Prepara textos dos KPIs com dados atuais
        kpi_texts = [
            f"Cities: {len(app.delivery_points)}",
            f"Population: {app.population_size}",
            f"Generation: {app.current_generation}/{app.max_generations}",
            # Converte fitness (1/distância) de volta para distância
            f"Best Dist.: {(1/app.best_fitness):.2f}" if getattr(app,'best_fitness',0) else "Best Dist.: N/A"
        ]
        
        # Renderiza cada KPI em seu respectivo box
        for rect, text in zip(kpi_rects, kpi_texts):
            pygame.draw.rect(app.screen, LGRAY, rect, border_radius=4)  # Fundo claro
            pygame.draw.rect(app.screen, GRAY, rect, 1, border_radius=4)  # Borda
            app.screen.blit(app.small_font.render(text, True, BLACK), (rect.x + 8, rect.y + 4))

        # Barra de progresso das gerações
        pct = (app.current_generation / app.max_generations) if getattr(app, 'max_generations', 0) else 0
        prog_rect = pygame.Rect(inner_x, kpi_rects[2].bottom + 14, inner_w, 10)
        
        # Fundo da barra
        pygame.draw.rect(app.screen, LGRAY, prog_rect, border_radius=4)
        pygame.draw.rect(app.screen, GRAY, prog_rect, 1, border_radius=4)
        
        # Preenchimento proporcional ao progresso
        fill_rect = pygame.Rect(prog_rect.x, prog_rect.y, int(pct * prog_rect.width), prog_rect.height)
        pygame.draw.rect(app.screen, GREEN, fill_rect, border_radius=4)

    @staticmethod
    def _draw_operators_section(app: Any, x: int, w: int) -> None:
        """Desenha a seção de operadores (Operators)."""
        cp = UILayout.ControlPanel
        _card(app.screen, x, cp.OPERATORS_Y, w, cp.OPERATORS_H, "Operators", app.font)
        
        # Toggle Elitismo
        elitism_rect = app.buttons['toggle_elitism']
        elitism_color = GREEN if app.elitism else RED
        pygame.draw.rect(app.screen, elitism_color, elitism_rect)
        pygame.draw.rect(app.screen, BLACK, elitism_rect, 2)
        elitism_text = f"Elitism: {'On' if app.elitism else 'Off'}"
        app.screen.blit(app.small_font.render(elitism_text, True, BLACK), 
                       (elitism_rect.x + 8, elitism_rect.y + 4))
        
        # Labels de seção
        app.screen.blit(app.small_font.render("Selection:", True, BLACK), 
                       (x + 4, cp.OPERATORS_Y + 36 + elitism_rect.height + 10))
        mut_y = app.buttons['mutation_swap'].y
        app.screen.blit(app.small_font.render("Mutation:", True, BLACK), (x + 4, mut_y - 18))
        
        # Botões de seleção
        selection_buttons = [
            ('selection_roulette','Roleta','roulette'),
            ('selection_tournament','Torneio','tournament'),
            ('selection_rank','Ranking','rank')
        ]
        for key, label, method in selection_buttons:
            rect = app.buttons[key]
            color = UILayout.get_color('blue') if app.selection_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect)
            pygame.draw.rect(app.screen, BLACK, rect, 2)
            text_surface = app.small_font.render(label, True, BLACK)
            app.screen.blit(text_surface, text_surface.get_rect(center=rect.center))
        
        # Botões de mutação
        mutation_buttons = [
            ('mutation_swap','Swap','swap'),
            ('mutation_inverse','Inverse','inverse'),
            ('mutation_shuffle','Shuffle','shuffle')
        ]
        for key, label, method in mutation_buttons:
            rect = app.buttons[key]
            color = GREEN if app.mutation_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect)
            pygame.draw.rect(app.screen, BLACK, rect, 2)
            text_surface = app.small_font.render(label, True, BLACK)
            app.screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    @staticmethod
    def _draw_crossover_section(app: Any, x: int, w: int) -> None:
        """Desenha a seção de crossover e botões de controle."""
        cp = UILayout.ControlPanel
        _card(app.screen, x, cp.CROSSOVER_Y, w, cp.CROSSOVER_H, "Crossover", app.font)
        
        # Botões de crossover
        crossover_buttons = [
            ('crossover_pmx','PMX','pmx'),
            ('crossover_ox1','OX1','ox1'),
            ('crossover_cx','CX','cx'),
            ('crossover_kpoint','K-Pt','kpoint'),
            ('crossover_erx','ERX','erx')
        ]
        for key, label, method in crossover_buttons:
            rect = app.buttons[key]
            color = YELL if app.crossover_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect)
            pygame.draw.rect(app.screen, BLACK, rect, 2)
            text_surface = app.small_font.render(label, True, BLACK)
            app.screen.blit(text_surface, text_surface.get_rect(center=rect.center))
        
        # Botões Run/Stop
        run_rect = app.buttons['run_algorithm']
        stop_rect = app.buttons['stop_algorithm']
        
        run_color = GREEN if not app.running_algorithm else LGRAY
        stop_color = RED if app.running_algorithm else LGRAY
        
        pygame.draw.rect(app.screen, run_color, run_rect)
        pygame.draw.rect(app.screen, BLACK, run_rect, 2)
        pygame.draw.rect(app.screen, stop_color, stop_rect)
        pygame.draw.rect(app.screen, BLACK, stop_rect, 2)
        
        app.screen.blit(app.font.render("Run", True, BLACK), (run_rect.x + 44, run_rect.y + 5))
        app.screen.blit(app.font.render("Stop", True, BLACK), (stop_rect.x + 22, stop_rect.y + 5))

    @staticmethod
    def draw_interface(app: Any) -> None:
        """Desenha toda a interface do usuário de forma modular."""
        cp = UILayout.ControlPanel
        
        # Painel principal
        panel = pygame.Rect(cp.X, cp.Y, cp.WIDTH, cp.HEIGHT)
        pygame.draw.rect(app.screen, LGRAY, panel, border_radius=8)
        pygame.draw.rect(app.screen, DGRAY, panel, 2, border_radius=8)
        app.screen.blit(app.font.render("TSP - Genetic Algorithm", True, BLACK), 
                       (cp.X + cp.PAD, cp.TITLE_Y))

        x = cp.X + cp.PAD
        w = cp.WIDTH - 2 * cp.PAD

        # Seções modulares
        DrawFunctions._draw_setup_section(app, x, w)
        
        # Priority Slider (card separado)
        priority_card_y = cp.SETUP_Y + cp.SETUP_H + 12
        priority_card_h = cp.PRIORITY_H
        _card(app.screen, x, priority_card_y, w, priority_card_h, "Priority", app.font)
        DrawFunctions.draw_priority_slider(app)

        # Linha adicional: controles de Max Vehicles
        # Label
        label_rect = app.buttons.get('max_vehicles_label')
        if label_rect:
            label_text = app.small_font.render("Max Vehicles:", True, BLACK)
            app.screen.blit(label_text, (label_rect.x + 4, label_rect.y + 4))

        # Botões - / + e display do valor atual
        minus_r = app.buttons.get('max_vehicles_minus')
        plus_r  = app.buttons.get('max_vehicles_plus')
        disp_r  = app.buttons.get('max_vehicles_display')
        if minus_r and plus_r and disp_r:
            # Desenhar botões
            btn_color = WHITE if not app.running_algorithm else LGRAY
            pygame.draw.rect(app.screen, btn_color, minus_r, border_radius=4)
            pygame.draw.rect(app.screen, BLACK, minus_r, 2, border_radius=4)
            pygame.draw.rect(app.screen, btn_color, plus_r, border_radius=4)
            pygame.draw.rect(app.screen, BLACK, plus_r, 2, border_radius=4)

            minus_text = app.font.render("-", True, BLACK)
            plus_text = app.font.render("+", True, BLACK)
            app.screen.blit(minus_text, minus_text.get_rect(center=minus_r.center))
            app.screen.blit(plus_text, plus_text.get_rect(center=plus_r.center))

            # Display do valor atual (None => "∞")
            pygame.draw.rect(app.screen, WHITE, disp_r, border_radius=4)
            pygame.draw.rect(app.screen, BLACK, disp_r, 2, border_radius=4)
            mv_val = getattr(app, 'max_vehicles_total', None)
            mv_text = "∞" if mv_val in (None, 0) else str(int(mv_val))
            mv_surf = app.small_font.render(mv_text, True, BLACK)
            app.screen.blit(mv_surf, mv_surf.get_rect(center=disp_r.center))
        
        DrawFunctions._draw_run_section(app, x, w)
        DrawFunctions._draw_operators_section(app, x, w)
        DrawFunctions._draw_crossover_section(app, x, w)
        
        # Fitness (card + gráfico)
        _card(app.screen, x, cp.FITNESS_Y, w, cp.FITNESS_H, "Fitness History", app.font)
        DrawFunctions.draw_fitness_graph(app)

    @staticmethod
    def _get_city_style(city) -> Tuple[Tuple[int, int, int], int, bool]:
        """
        Determina o estilo visual baseado na prioridade do produto.
        
        Returns:
            Tupla com (cor_externa, raio_externo, mostrar_prioridade)
        """
        priority = getattr(getattr(city, "product", None), "priority", 0)
        
        if priority and priority > 0:
            # Cores baseadas na prioridade
            if priority >= 0.8:
                return ((255, 215, 0), 10, True)  # Ouro para alta prioridade
            else:
                return ((255, 255, 153), 10, True)  # Amarelo claro para prioridade média
        else:
            return (BLUE, 7, False)  # Azul padrão para sem prioridade

    @staticmethod
    def _draw_city_point(app: Any, city, index: int, style: Tuple[Tuple[int, int, int], int, bool]) -> None:
        """Desenha um ponto de cidade com o estilo especificado."""
        outer_color, outer_radius, show_priority = style
        
        # Círculos concêntricos
        if show_priority:
            pygame.draw.circle(app.screen, outer_color, (city.x, city.y), outer_radius)
            pygame.draw.circle(app.screen, BLUE, (city.x, city.y), 7)
            pygame.draw.circle(app.screen, WHITE, (city.x, city.y), 5)
        else:
            pygame.draw.circle(app.screen, outer_color, (city.x, city.y), outer_radius)
            pygame.draw.circle(app.screen, WHITE, (city.x, city.y), 5)
        
        # Número do índice
        index_text = app.small_font.render(str(index), True, BLACK)
        app.screen.blit(index_text, index_text.get_rect(center=(city.x, city.y)))
        
        # Valor da prioridade (se aplicável)
        if show_priority:
            priority = getattr(getattr(city, "product", None), "priority", 0)
            priority_text = app.small_font.render(f"{priority:.2f}", True, BLACK)
            app.screen.blit(priority_text, (city.x + 12, city.y - 8))

    @staticmethod
    def draw_cities(app: Any) -> None:
        """Desenha todas as cidades com destaque para prioridades."""
        for i, city in enumerate(app.delivery_points):
            style = DrawFunctions._get_city_style(city)
            DrawFunctions._draw_city_point(app, city, i, style)

    @staticmethod
    def _normalize_route_points(app: Any, chromosome: Any) -> List[Any]:
        """
        Normaliza diferentes tipos de input de rota para uma lista de pontos.
        
        Returns:
            Lista de pontos de entrega normalizados
        """
        if not chromosome:
            return []
            
        if hasattr(chromosome, 'delivery_points'):
            return list(chromosome.delivery_points)
        elif isinstance(chromosome, list) and chromosome and isinstance(chromosome[0], int):
            return [app.delivery_points[i] for i in chromosome]
        elif isinstance(chromosome, list):
            return chromosome
        else:
            return []

    @staticmethod
    def _draw_route_lines(app: Any, points: List[Any], color: Tuple[int, int, int], width: int) -> None:
        """Desenha as linhas da rota conectando os pontos."""
        if len(points) < 2:
            return
            
        # Converte pontos para coordenadas e fecha o loop
        coordinates = [(p.x, p.y) for p in points] + [(points[0].x, points[0].y)]
        pygame.draw.lines(app.screen, color, False, coordinates, width)

    @staticmethod
    def draw_route(app: Any, chromosome: Any, color: Tuple[int, int, int] = BLACK, width: int = 2) -> None:
        """Desenha uma rota conectando os pontos especificados."""
        points = DrawFunctions._normalize_route_points(app, chromosome)
        DrawFunctions._draw_route_lines(app, points, color, width)

    # -------------------- VRP (múltiplas rotas) --------------------
    @staticmethod
    def _palette() -> List[Tuple[int, int, int]]:
        """
        Retorna paleta de cores distintas para diferenciação visual de rotas.
        
        A paleta foi cuidadosamente selecionada para:
        - Máximo contraste visual entre cores adjacentes
        - Boa visibilidade sobre fundo claro
        - Distinção clara mesmo para daltonismo comum
        - Consistência com convenções de visualização científica
        
        Cores baseadas na paleta "tab10" do matplotlib, reconhecida
        por sua eficácia em visualizações científicas.
        
        Returns:
            Lista de 10 tuplas RGB representando cores distintas
            
        Note:
            Para mais de 10 rotas, as cores são reutilizadas ciclicamente
            usando operador módulo (%) no índice da rota.
        """
        return [
            (31, 119, 180),   # Azul
            (255, 127, 14),   # Laranja  
            (44, 160, 44),    # Verde
            (214, 39, 40),    # Vermelho
            (148, 103, 189),  # Roxo
            (140, 86, 75),    # Marrom
            (227, 119, 194),  # Rosa
            (127, 127, 127),  # Cinza
            (188, 189, 34),   # Verde-oliva
            (23, 190, 207),   # Ciano
        ]

    @staticmethod
    def draw_depot(app: Any, deposito) -> None:
        if deposito is None:
            return
        pygame.draw.rect(app.screen, BLACK, pygame.Rect(deposito.x - 6, deposito.y - 6, 12, 12))
        pygame.draw.rect(app.screen, YELL,  pygame.Rect(deposito.x - 4, deposito.y - 4, 8, 8))

    @staticmethod
    def _route_distance(app: Any, r: Any, deposito: Any) -> float:
        """
        Calcula distância total de uma rota incluindo retorno ao depósito.
        
        A função suporta dois tipos de objetos de rota:
        1. Rotas com método próprio de cálculo (distancia_roundtrip)
        2. Rotas genéricas com lista de pontos de entrega
        
        Para rotas genéricas, calcula:
        - Distância do depósito ao primeiro ponto
        - Distâncias entre pontos consecutivos  
        - Distância do último ponto de volta ao depósito
        
        Utiliza distância euclidiana: sqrt((x2-x1)² + (y2-y1)²)
        
        Args:
            app: Instância da aplicação (não utilizada atualmente)
            r: Objeto de rota contendo delivery_points ou método distancia_roundtrip
            deposito: Ponto do depósito (origem/destino)
            
        Returns:
            Distância total da rota como float, ou 0.0 se rota vazia
        """
        # Método preferencial: usa cálculo próprio da rota se disponível
        if hasattr(r, "distancia_roundtrip"):
            return r.distancia_roundtrip(deposito)
            
        # Fallback: calcula manualmente usando pontos de entrega
        seq = getattr(r, "delivery_points", None) or []
        if not seq:
            return 0.0
            
        d = 0.0
        
        # Depósito → primeiro ponto
        d += ((deposito.x - seq[0].x)**2 + (deposito.y - seq[0].y)**2) ** 0.5
        
        # Pontos consecutivos
        for i in range(len(seq) - 1):
            d += ((seq[i].x - seq[i+1].x)**2 + (seq[i].y - seq[i+1].y)**2) ** 0.5
            
        # Último ponto → depósito
        d += ((seq[-1].x - deposito.x)**2 + (seq[-1].y - deposito.y)**2) ** 0.5
        
        return d

    @staticmethod
    def _fleet_cost_map(app: Any) -> Dict[str, float]:
        m: Dict[str, float] = {}
        for v in getattr(app, "fleet", None) or []:
            name = getattr(v, "name", None)
            cpk  = getattr(v, "cost_per_km", None)
            if name is not None and cpk is not None:
                m[str(name)] = float(cpk)
        return m

    @staticmethod
    def _calculate_route_statistics(app: Any, routes: List[Any], deposito: Any, usage: Dict[str, int] = None) -> Tuple[float, float, Dict[str, int], str]:
        """
        Calcula estatísticas de rotas.
        
        Returns:
            Tupla com (total_dist, total_cost, use_dict, usage_text)
        """
        total_dist = 0.0
        total_cost = 0.0
        cost_map: Dict[str, float] = DrawFunctions._fleet_cost_map(app)
        use: Dict[str, int] = {}

        for r in routes:
            dist = DrawFunctions._route_distance(app, r, deposito)
            total_dist += dist
            vname = getattr(r, "vehicle_type", None)
            if vname:
                use[vname] = use.get(vname, 0) + 1
                if vname in cost_map:
                    total_cost += dist * cost_map[vname]

        if usage:
            use = dict(usage)

        usage_txt = ", ".join(f"{k}×{v}" for k, v in use.items()) if use else "—"
        return total_dist, total_cost, use, usage_txt

    @staticmethod
    def _calculate_summary_box_layout(left: int = None, top: int = None, width: int = None) -> pygame.Rect:
        """Calcula posição e dimensões do box de resumo."""
        ma = UILayout.MapArea
        PAD = 8
        x0 = left if left is not None else (ma.CITIES_X + PAD)
        y0 = top if top is not None else (ma.CITIES_Y + PAD + 110)
        min_w = 240
        w = max(width if width is not None else min_w, min_w)

        line_h = 20
        h = PAD + 3 * line_h + PAD

        y0 = min(y0, ma.CITIES_Y + ma.CITIES_HEIGHT - h - PAD)
        return pygame.Rect(x0, y0, w, h)

    @staticmethod
    def _render_summary_box_content(app: Any, rect: pygame.Rect, routes: List[Any], 
                                  stats: Tuple[float, float, Dict[str, int], str]) -> None:
        """Renderiza o conteúdo do box de resumo."""
        total_dist, total_cost, _, usage_txt = stats
        PAD = 8
        line_h = 20

        # Box de fundo
        pygame.draw.rect(app.screen, WHITE, rect, border_radius=6)
        pygame.draw.rect(app.screen, DGRAY, rect, 1, border_radius=6)

        # Linhas de texto
        line1 = app.small_font.render(f"Rotas: {len(routes)}", True, BLACK)
        line2 = app.small_font.render(
            f"Custo total: {total_cost:.1f}" if total_cost > 0 else f"Distância total: {total_dist:.1f}",
            True, BLACK
        )
        line3 = app.small_font.render(f"Uso por tipo: {usage_txt}", True, BLACK)

        # Renderização
        app.screen.blit(line1, (rect.x + PAD, rect.y + PAD))
        app.screen.blit(line2, (rect.x + PAD, rect.y + PAD + line_h))
        app.screen.blit(line3, (rect.x + PAD, rect.y + PAD + 2 * line_h))

    @staticmethod
    def draw_vrp_summary(
        app: Any,
        routes: List[Any],
        deposito: Any,
        usage: Dict[str, int] = None,
        left: int = None,
        top: int = None,
        width: int = None,
    ) -> None:
        """Box com Rotas / Custo total / Uso por tipo, alinhado ao que for passado."""
        if not routes:
            return

        stats = DrawFunctions._calculate_route_statistics(app, routes, deposito, usage)
        rect = DrawFunctions._calculate_summary_box_layout(left, top, width)
        DrawFunctions._render_summary_box_content(app, rect, routes, stats)


    @staticmethod
    def _draw_delivery_points(app: Any) -> None:
        """Desenha os pontos de entrega como círculos numerados."""
        for i, delivery_point in enumerate(app.delivery_points):
            pygame.draw.circle(app.screen, BLUE, (delivery_point.x, delivery_point.y), 6)
            pygame.draw.circle(app.screen, WHITE, (delivery_point.x, delivery_point.y), 4)
            
            point_label = app.small_font.render(str(i), True, BLACK)
            label_rect = point_label.get_rect(center=(delivery_point.x, delivery_point.y))
            app.screen.blit(point_label, label_rect)

    @staticmethod
    def _draw_route_lines(app: Any, routes: List[Any], depot: Any) -> List[Tuple[str, float, Tuple[int, int, int]]]:
        """
        Desenha as linhas das rotas VRP e coleta dados para a legenda.
        
        Para cada rota:
        1. Atribui uma cor única da paleta disponível
        2. Constrói sequência completa: depósito → pontos → depósito
        3. Renderiza linha contínua com a cor da rota
        4. Calcula distância total da rota
        5. Coleta dados para construção da legenda
        
        A função utiliza cores rotativas da paleta, garantindo que rotas sejam
        visualmente distintas mesmo com muitas rotas simultâneas.
        
        Args:
            app: Instância da aplicação com screen para renderização
            routes: Lista de objetos de rota contendo delivery_points
            depot: Ponto do depósito (origem/destino de todas as rotas)
            
        Returns:
            Lista de tuplas (nome_veiculo, distancia, cor) para construção da legenda
        """
        color_palette = DrawFunctions._palette()
        legend_data = []
        
        for route_index, route in enumerate(routes):
            # Atribui cor baseada no índice (rotativo na paleta)
            route_color = color_palette[route_index % len(color_palette)]
            delivery_sequence = getattr(route, "delivery_points", [])
            
            if not delivery_sequence:  # Pula rotas vazias
                continue
                
            # Constrói sequência completa incluindo retorno ao depósito
            # Formato: [depot] + [ponto1, ponto2, ...] + [depot]
            route_points = (
                [(depot.x, depot.y)] + 
                [(point.x, point.y) for point in delivery_sequence] + 
                [(depot.x, depot.y)]
            )
            
            # Renderiza linha contínua da rota com espessura 3px
            pygame.draw.lines(app.screen, route_color, False, route_points, 3)
            
            # Coleta metadados para a legenda
            vehicle_name = getattr(route, "vehicle_type", "Vehicle")
            route_distance = DrawFunctions._route_distance(app, route, depot)
            legend_data.append((vehicle_name, route_distance, route_color))
            
        return legend_data

    @staticmethod
    def _draw_route_legend(
        app: Any, 
        legend_data: List[Tuple[str, float, Tuple[int, int, int]]], 
        position: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Desenha legenda das rotas VRP com cores, nomes de veículos e distâncias.
        
        A legenda é renderizada como um box com fundo branco contendo:
        - Uma linha por rota com cor correspondente
        - Nome do tipo de veículo
        - Distância total da rota formatada
        
        Layout da legenda:
        - Padding interno de 8px
        - Altura de linha de 18px
        - Largura mínima de 200px (ajustada ao conteúdo)
        - Bordas arredondadas para consistência visual
        
        Args:
            app: Instância da aplicação contendo fonts para renderização
            legend_data: Lista de tuplas (nome_veiculo, distancia, cor)
            position: Tupla (x, y) da posição superior-esquerda da legenda
            
        Returns:
            Tupla (largura, altura) da legenda renderizada para posicionamento de outros elementos
        """
        if not legend_data:  # Sem dados = sem legenda
            return (0, 0)
            
        left_x, top_y = position
        padding = 8
        line_height = 18
        
        # Calcula largura necessária baseada no texto mais longo
        max_text_width = max(
            app.small_font.size(f"{name} — {distance:.1f}")[0] 
            for name, distance, _ in legend_data
        )
        # Largura = texto + linha colorida (18px) + espaço (6px) + padding
        legend_width = max(200, max_text_width + 26 + 2 * padding)
        legend_height = padding + len(legend_data) * line_height + padding
        
        # Desenha fundo da legenda com bordas arredondadas
        legend_rect = pygame.Rect(left_x, top_y, legend_width, legend_height)
        pygame.draw.rect(app.screen, WHITE, legend_rect, border_radius=6)   # Fundo branco
        pygame.draw.rect(app.screen, DGRAY, legend_rect, 1, border_radius=6)  # Borda cinza
        
        # Renderiza cada item da legenda
        for index, (vehicle_name, distance, color) in enumerate(legend_data):
            item_y = top_y + padding + index * line_height
            
            # Linha colorida representando a rota (18px de largura, 4px de espessura)
            line_start = (left_x + padding, item_y + 9)        # Centro vertical da linha
            line_end = (left_x + padding + 18, item_y + 9)
            pygame.draw.line(app.screen, color, line_start, line_end, 4)
            
            # Texto: "Tipo_Veiculo — Distancia"
            item_text = app.small_font.render(f"{vehicle_name} — {distance:.1f}", True, BLACK)
            app.screen.blit(item_text, (left_x + padding + 24, item_y))  # 24px = linha + espaço
            
    @staticmethod
    def _draw_route_legend_fixed_width(
        app: Any, 
        legend_data: List[Tuple[str, float, Tuple[int, int, int]]], 
        position: Tuple[int, int],
        fixed_width: int
    ) -> Tuple[int, int]:
        """
        Desenha legenda das rotas VRP com largura fixa especificada.
        
        Versão da legenda que aceita largura fixa, adequada para integrar 
        ao painel de controle abaixo do gráfico de fitness.
        
        Args:
            app: Instância da aplicação contendo fonts para renderização
            legend_data: Lista de tuplas (nome_veiculo, distancia, cor)
            position: Tupla (x, y) da posição superior-esquerda da legenda
            fixed_width: Largura fixa da legenda em pixels
            
        Returns:
            Tupla (largura_usada, altura) da legenda renderizada
        """
        if not legend_data:  # Sem dados = sem legenda
            return (0, 0)
            
        left_x, top_y = position
        padding = 8
        line_height = 18
        
        # Usa largura fixa fornecida
        legend_width = fixed_width
        legend_height = padding + len(legend_data) * line_height + padding
        
        # Desenha fundo da legenda com bordas arredondadas
        legend_rect = pygame.Rect(left_x, top_y, legend_width, legend_height)
        pygame.draw.rect(app.screen, WHITE, legend_rect, border_radius=6)   # Fundo branco
        pygame.draw.rect(app.screen, DGRAY, legend_rect, 1, border_radius=6)  # Borda cinza
        
        # Título da legenda
        title_text = app.small_font.render("Route Legend", True, BLACK)
        app.screen.blit(title_text, (left_x + padding, top_y + padding))
        
        # Linha separadora
        sep_y = top_y + padding + 16
        pygame.draw.line(app.screen, LGRAY, 
                        (left_x + padding, sep_y), 
                        (left_x + legend_width - padding, sep_y), 1)
        
        # Renderiza cada item da legenda (começando após o título)
        for index, (vehicle_name, distance, color) in enumerate(legend_data):
            item_y = sep_y + 6 + index * line_height
            
            # Linha colorida representando a rota (18px de largura, 4px de espessura)
            line_start = (left_x + padding, item_y + 9)        # Centro vertical da linha
            line_end = (left_x + padding + 18, item_y + 9)
            pygame.draw.line(app.screen, color, line_start, line_end, 4)
            
            # Texto: "Tipo_Veiculo — Distancia" (truncado se necessário)
            text_content = f"{vehicle_name} — {distance:.1f}"
            max_text_width = legend_width - 32 - 2 * padding  # Espaço disponível para texto
            
            # Renderiza texto, truncando se necessário
            item_text = app.small_font.render(text_content, True, BLACK)
            if item_text.get_width() > max_text_width:
                # Trunca o nome do veículo se necessário
                truncated = f"{vehicle_name[:8]}... — {distance:.1f}"
                item_text = app.small_font.render(truncated, True, BLACK)
            
            app.screen.blit(item_text, (left_x + padding + 24, item_y))  # 24px = linha + espaço
            
        # Ajusta altura para incluir título e separador
        total_height = padding + 16 + 6 + len(legend_data) * line_height + padding
        return (legend_width, total_height)

    @staticmethod
    def _draw_vrp_routes_panel(
        app: Any,
        routes: List[Any],
        deposito: Any,
        legend_data: List[Tuple[str, float, Tuple[int, int, int]]],
        left: int,
        top: int,
        width: int,
        usage: Dict[str, int] | None = None,
    ) -> int:
        """
        Desenha um único card combinando o resumo VRP e a legenda de rotas.

        O card segue o padrão visual dos demais (título + linha separadora) e contém:
        - Resumo (Rotas, Custo/Distância total, Uso por tipo)
        - Itens de legenda com cores das rotas e distância por veículo

        Args:
            app: Instância da aplicação
            routes: Lista de rotas
            deposito: Ponto do depósito
            legend_data: Lista de tuplas (vehicle_name, distance, color)
            left, top, width: Posição e largura do card
            usage: Uso por tipo de veículo (opcional, sobrescreve cálculo)

        Returns:
            Altura total utilizada pelo card (para layout subsequente, se necessário)
        """
        PAD = 8
        line_h = 18

        # Estatísticas consolidadas (permite injetar usage externo)
        total_dist, total_cost, _use, usage_txt = DrawFunctions._calculate_route_statistics(
            app, routes, deposito, usage
        )

        # Altura do conteúdo: 3 linhas de resumo + espaço + linhas de legenda + padding
        summary_lines = 3
        legend_lines = len(legend_data)
        # Se houver muitas rotas, quebrar a legenda em duas colunas e contar linhas por coluna
        if legend_lines > 5:
            legend_rows = (legend_lines + 1) // 2
        else:
            legend_rows = legend_lines
        content_h = PAD + summary_lines * line_h + 8 + legend_rows * line_h + PAD
        card_h = 36 + content_h  # 36px reservados ao título/linha do card

        # Desenha o card padrão
        _card(app.screen, left, top, width, card_h, "Routes", app.font)

        # Área de conteúdo inicia após o título
        cy = top + 36

        # Linhas do resumo
        line1 = app.small_font.render(f"Rotas: {len(routes)}", True, BLACK)
        line2 = app.small_font.render(
            f"Custo total: {total_cost:.1f}" if total_cost > 0 else f"Distância total: {total_dist:.1f}",
            True, BLACK,
        )
        line3 = app.small_font.render(f"Uso por tipo: {usage_txt}", True, BLACK)

        app.screen.blit(line1, (left + PAD, cy + PAD))
        app.screen.blit(line2, (left + PAD, cy + PAD + line_h))
        app.screen.blit(line3, (left + PAD, cy + PAD + 2 * line_h))

        # Posição inicial dos itens da legenda (após um pequeno espaçamento)
        legend_top = cy + PAD + 3 * line_h + 8
        if legend_lines <= 5:
            # Uma coluna
            ly = legend_top
            for vehicle_name, distance, color in legend_data:
                line_start = (left + PAD, ly + 9)
                line_end = (left + PAD + 18, ly + 9)
                pygame.draw.line(app.screen, color, line_start, line_end, 4)

                text = app.small_font.render(f"{vehicle_name} — {distance:.1f}", True, BLACK)
                app.screen.blit(text, (left + PAD + 24, ly))
                ly += line_h
        else:
            # Duas colunas de largura igual
            total_inner_w = width - 2 * PAD
            col_w = (total_inner_w - PAD) // 2  # espaço de PAD entre colunas
            left_col_x = left + PAD
            right_col_x = left + PAD + col_w + PAD
            rows = (legend_lines + 1) // 2

            # Função auxiliar para desenhar um item em uma coluna específica
            def draw_legend_item(col_x: int, y: int, name: str, dist: float, col_color: Tuple[int, int, int]) -> None:
                # Linha colorida
                line_start = (col_x, y + 9)
                line_end = (col_x + 18, y + 9)
                pygame.draw.line(app.screen, col_color, line_start, line_end, 4)
                # Texto com possível truncamento para caber na coluna
                text_content = f"{name} — {dist:.1f}"
                max_text_width = col_w - 24  # 24px após a linha colorida
                rendered = app.small_font.render(text_content, True, BLACK)
                if rendered.get_width() > max_text_width:
                    # Trunca o nome mantendo o sufixo com distância
                    trimmed_name = name
                    # Heurística simples de truncamento
                    while len(trimmed_name) > 0 and app.small_font.render(f"{trimmed_name}… — {dist:.1f}", True, BLACK).get_width() > max_text_width:
                        trimmed_name = trimmed_name[:-1]
                    text_content = f"{trimmed_name}… — {dist:.1f}"
                    rendered = app.small_font.render(text_content, True, BLACK)
                app.screen.blit(rendered, (col_x + 24, y))

            for row in range(rows):
                y = legend_top + row * line_h
                # Esquerda
                idx_left = row
                name_l, dist_l, color_l = legend_data[idx_left]
                draw_legend_item(left_col_x, y, name_l, dist_l, color_l)
                # Direita (se houver)
                idx_right = row + rows
                if idx_right < legend_lines:
                    name_r, dist_r, color_r = legend_data[idx_right]
                    draw_legend_item(right_col_x, y, name_r, dist_r, color_r)

        return card_h

    @staticmethod
    def draw_routes_vrp(app: Any, routes: List[Any], deposito: Any, show_legend: bool = True) -> None:
        """
        Renderiza solução completa do VRP com múltiplas rotas, legenda e resumo estatístico.
        
        Este é o método principal para visualização de soluções VRP, coordenando
        a renderização de todos os componentes visuais necessários:
        
        Sequência de renderização:
        1. Pontos de entrega (círculos numerados)
        2. Linhas das rotas (cores distintas por veículo)
        3. Depósito (quadrado amarelo destacado)
        4. Legenda (opcional) - posicionada abaixo do gráfico de fitness
        5. Resumo estatístico (opcional) - abaixo da legenda
        
        A renderização segue uma ordem específica para garantir que elementos
        importantes (depósito, legenda) apareçam adequadamente organizados.
        
        Args:
            app: Instância da aplicação com screen, delivery_points e fonts
            routes: Lista de objetos Route contendo delivery_points e vehicle_type
            deposito: Objeto Point representando o depósito central
            show_legend: Se deve renderizar legenda e resumo (padrão: True)
        """
        if not routes:  # Sem rotas = sem renderização
            return
            
        # 1. Renderiza pontos de entrega como base da visualização
        DrawFunctions._draw_delivery_points(app)
        
        # 2. Desenha rotas e coleta dados para legenda
        # Retorna lista de (nome_veiculo, distancia, cor) para cada rota
        legend_data = DrawFunctions._draw_route_lines(app, routes, deposito)
        
        # 3. Desenha depósito sobre as rotas para destacá-lo
        DrawFunctions.draw_depot(app, deposito)
        
        # 4. Renderiza painel combinado (Resumo + Legenda) se solicitado
        if show_legend and legend_data:
            cp = UILayout.ControlPanel
            left = cp.X + cp.PAD
            top = cp.FITNESS_Y + cp.FITNESS_H + 12
            width = cp.WIDTH - 2 * cp.PAD

            usage = getattr(getattr(app, "best_route", None), "vehicle_usage", None)
            DrawFunctions._draw_vrp_routes_panel(
                app=app,
                routes=routes,
                deposito=deposito,
                legend_data=legend_data,
                left=left,
                top=top,
                width=width,
                usage=usage,
            )


    @staticmethod
    def draw_vrp_solution(app: Any, routes: List[Any], deposito: Any, show_legend: bool = True) -> None:
        DrawFunctions.draw_routes_vrp(app, routes, deposito, show_legend)

    # -------------------- Shell principal --------------------
    @staticmethod
    def draw(app: Any) -> None:
        """
        Método shell principal que coordena a renderização completa da interface.
        
        Este é o ponto de entrada para toda a renderização da aplicação,
        chamado a cada frame do loop principal do pygame.
        
        Ordem de renderização:
        1. Área do mapa (fundo, grade, bordas)
        2. Interface de controle (painel esquerdo completo)
        
        A ordem é importante para garantir que elementos da interface
        apareçam sobre o fundo do mapa, mantendo a hierarquia visual adequada.
        
        Args:
            app: Instância principal da aplicação contendo:
                - screen: Surface do pygame para renderização
                - Todos os estados e configurações necessários
        """
        DrawFunctions._draw_map_board(app)  # Renderiza área do mapa primeiro (fundo)
        DrawFunctions.draw_interface(app)   # Renderiza interface por cima
