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
    """UI determinística (sem sobreposições)."""

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
        cp = UILayout.ControlPanel
        x = cp.X + cp.PAD
        w = cp.WIDTH - 2*cp.PAD

        inner_x = x + 8
        inner_y = cp.FITNESS_Y + 36 + 4
        inner_w = w - 16
        inner_h = cp.FITNESS_H - 36 - 16

        fr = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect(app.screen, WHITE, fr)
        pygame.draw.rect(app.screen, BLACK, fr, 2)

        if not hasattr(app, 'fitness_history') or len(app.fitness_history) < 2:
            return
        if not hasattr(app, 'mean_fitness_history'):
            app.mean_fitness_history = []

        n = min(len(app.fitness_history), len(app.mean_fitness_history))
        if n < 2:
            return

        vals = list(app.fitness_history[:n]) + list(app.mean_fitness_history[:n])
        vmin, vmax = min(vals), max(vals)
        if vmax == vmin:
            return

        pts_max, pts_mean = [], []
        for i in range(n):
            x_pt = fr.x + (i / max(1, n - 1)) * (fr.width - 12) + 6
            y1 = fr.bottom - 6 - ((app.fitness_history[i]    - vmin) / (vmax - vmin)) * (fr.height - 12)
            y2 = fr.bottom - 6 - ((app.mean_fitness_history[i]- vmin) / (vmax - vmin)) * (fr.height - 12)
            pts_max.append((x_pt, y1))
            pts_mean.append((x_pt, y2))

        pygame.draw.lines(app.screen, RED,   False, pts_max, 2)
        pygame.draw.lines(app.screen, GREEN, False, pts_mean, 2)

    # -------------------- LATERAL ESQUERDA --------------------
    @staticmethod
    def draw_priority_slider(app):
        rect = app.buttons['priority_slider']
        # Slider bar
        slider_x = rect.x + 120
        slider_w = rect.width - 130
        slider_y = rect.y + rect.height // 2
        pygame.draw.line(app.screen, GRAY, (slider_x, slider_y), (slider_x + slider_w, slider_y), 4)
        # Handle
        pct = max(0, min(100, int(app.priority_percentage)))
        handle_x = slider_x + int((pct / 100) * slider_w)
        pygame.draw.circle(app.screen, BLUE, (handle_x, slider_y), 10)
        pygame.draw.circle(app.screen, WHITE, (handle_x, slider_y), 7)
        # Label
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
        """Desenha a seção de execução (Run) com KPIs e barra de progresso."""
        cp = UILayout.ControlPanel
        _card(app.screen, x, cp.RUN_Y, w, cp.RUN_H, "Run", app.font)
        
        inner_x = x + 4
        inner_w = w - 8
        row_y = cp.RUN_Y + 36
        bw = (inner_w - 10) // 2

        # KPIs em grid 2x2
        kpi_rects = [
            pygame.Rect(inner_x, row_y, bw, cp.KPI_H),
            pygame.Rect(inner_x + bw + 10, row_y, bw, cp.KPI_H),
            pygame.Rect(inner_x, row_y + cp.KPI_H + 8, bw, cp.KPI_H),
            pygame.Rect(inner_x + bw + 10, row_y + cp.KPI_H + 8, bw, cp.KPI_H)
        ]
        
        kpi_texts = [
            f"Cities: {len(app.delivery_points)}",
            f"Population: {app.population_size}",
            f"Generation: {app.current_generation}/{app.max_generations}",
            f"Best Dist.: {(1/app.best_fitness):.2f}" if getattr(app,'best_fitness',0) else "Best Dist.: N/A"
        ]
        
        for rect, text in zip(kpi_rects, kpi_texts):
            pygame.draw.rect(app.screen, LGRAY, rect, border_radius=4)
            pygame.draw.rect(app.screen, GRAY, rect, 1, border_radius=4)
            app.screen.blit(app.small_font.render(text, True, BLACK), (rect.x + 8, rect.y + 4))

        # Barra de progresso
        pct = (app.current_generation / app.max_generations) if getattr(app, 'max_generations', 0) else 0
        prog_rect = pygame.Rect(inner_x, kpi_rects[2].bottom + 14, inner_w, 10)
        pygame.draw.rect(app.screen, LGRAY, prog_rect, border_radius=4)
        pygame.draw.rect(app.screen, GRAY, prog_rect, 1, border_radius=4)
        
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
        priority_card_h = 56
        _card(app.screen, x, priority_card_y, w, priority_card_h, "Priority", app.font)
        DrawFunctions.draw_priority_slider(app)
        
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
        return [
            (31, 119, 180),
            (255, 127, 14),
            (44, 160, 44),
            (214, 39, 40),
            (148, 103, 189),
            (140, 86, 75),
            (227, 119, 194),
            (127, 127, 127),
            (188, 189, 34),
            (23, 190, 207),
        ]

    @staticmethod
    def draw_depot(app: Any, deposito) -> None:
        if deposito is None:
            return
        pygame.draw.rect(app.screen, BLACK, pygame.Rect(deposito.x - 6, deposito.y - 6, 12, 12))
        pygame.draw.rect(app.screen, YELL,  pygame.Rect(deposito.x - 4, deposito.y - 4, 8, 8))

    @staticmethod
    def _route_distance(app: Any, r: Any, deposito: Any) -> float:
        if hasattr(r, "distancia_roundtrip"):
            return r.distancia_roundtrip(deposito)
        seq = getattr(r, "delivery_points", None) or []
        if not seq:
            return 0.0
        d = 0.0
        d += ((deposito.x - seq[0].x)**2 + (deposito.y - seq[0].y)**2) ** 0.5
        for i in range(len(seq) - 1):
            d += ((seq[i].x - seq[i+1].x)**2 + (seq[i].y - seq[i+1].y)**2) ** 0.5
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
        Desenha as linhas das rotas e retorna dados para a legenda.
        
        Returns:
            Lista de tuplas com (nome_veiculo, distancia, cor) para cada rota
        """
        color_palette = DrawFunctions._palette()
        legend_data = []
        
        for route_index, route in enumerate(routes):
            route_color = color_palette[route_index % len(color_palette)]
            delivery_sequence = getattr(route, "delivery_points", [])
            
            if not delivery_sequence:
                continue
                
            # Criar sequência completa: depot -> pontos -> depot
            route_points = (
                [(depot.x, depot.y)] + 
                [(point.x, point.y) for point in delivery_sequence] + 
                [(depot.x, depot.y)]
            )
            
            pygame.draw.lines(app.screen, route_color, False, route_points, 3)
            
            # Coletar dados para legenda
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
        Desenha a legenda das rotas.
        
        Returns:
            Tupla com (largura, altura) da legenda desenhada
        """
        if not legend_data:
            return (0, 0)
            
        left_x, top_y = position
        padding = 8
        line_height = 18
        
        # Calcular dimensões necessárias
        max_text_width = max(
            app.small_font.size(f"{name} — {distance:.1f}")[0] 
            for name, distance, _ in legend_data
        )
        legend_width = max(200, max_text_width + 26 + 2 * padding)
        legend_height = padding + len(legend_data) * line_height + padding
        
        # Desenhar fundo da legenda
        legend_rect = pygame.Rect(left_x, top_y, legend_width, legend_height)
        pygame.draw.rect(app.screen, WHITE, legend_rect, border_radius=6)
        pygame.draw.rect(app.screen, DGRAY, legend_rect, 1, border_radius=6)
        
        # Desenhar cada item da legenda
        for index, (vehicle_name, distance, color) in enumerate(legend_data):
            item_y = top_y + padding + index * line_height
            
            # Linha colorida
            line_start = (left_x + padding, item_y + 9)
            line_end = (left_x + padding + 18, item_y + 9)
            pygame.draw.line(app.screen, color, line_start, line_end, 4)
            
            # Texto do item
            item_text = app.small_font.render(f"{vehicle_name} — {distance:.1f}", True, BLACK)
            app.screen.blit(item_text, (left_x + padding + 24, item_y))
            
        return (legend_width, legend_height)

    @staticmethod
    def draw_routes_vrp(app: Any, routes: List[Any], deposito: Any, show_legend: bool = True) -> None:
        """
        Desenha a solução completa do VRP com rotas, legenda e resumo.
        
        Args:
            app: Instância da aplicação com screen e delivery_points
            routes: Lista de rotas a serem desenhadas
            deposito: Ponto do depósito
            show_legend: Se deve mostrar a legenda das rotas
        """
        if not routes:
            return
            
        # 1. Desenhar pontos de entrega
        DrawFunctions._draw_delivery_points(app)
        
        # 2. Desenhar linhas das rotas e coletar dados da legenda
        legend_data = DrawFunctions._draw_route_lines(app, routes, deposito)
        
        # 3. Desenhar depósito
        DrawFunctions.draw_depot(app, deposito)
        
        # 4. Desenhar legenda e resumo se solicitado
        if show_legend and legend_data:
            map_area = UILayout.MapArea
            legend_position = (
                map_area.CITIES_X + 8,
                map_area.CITIES_Y + 8
            )
            
            legend_width, legend_height = DrawFunctions._draw_route_legend(
                app, legend_data, legend_position
            )
            
            # 5. Desenhar resumo abaixo da legenda
            usage = getattr(getattr(app, "best_route", None), "vehicle_usage", None)
            summary_position = (
                legend_position[0],
                legend_position[1] + legend_height + 12
            )
            
            DrawFunctions.draw_vrp_summary(
                app, routes, deposito,
                usage=usage,
                left=summary_position[0],
                top=summary_position[1],
                width=legend_width
            )


    @staticmethod
    def draw_vrp_solution(app: Any, routes: List[Any], deposito: Any, show_legend: bool = True) -> None:
        DrawFunctions.draw_routes_vrp(app, routes, deposito, show_legend)

    # -------------------- Shell principal --------------------
    @staticmethod
    def draw(app: Any) -> None:
        DrawFunctions._draw_map_board(app)
        DrawFunctions.draw_interface(app)
