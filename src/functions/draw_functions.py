import pygame
from typing import Any, Tuple
from ui_layout import UILayout

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
    # título dentro do card
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
        # dimensões derivadas do próprio card Fitness (nada fixo)
        cp = UILayout.ControlPanel
        x = cp.X + cp.PAD
        w = cp.WIDTH - 2*cp.PAD

        inner_x = x + 8
        inner_y = cp.FITNESS_Y + 36 + 4      # abaixo do título do card
        inner_w = w - 16
        inner_h = cp.FITNESS_H - 36 - 16

        fr = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect(app.screen, WHITE, fr)
        pygame.draw.rect(app.screen, BLACK, fr, 2)

        # sem dados suficientes? só a moldura
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
    def draw_interface(app: Any) -> None:
        cp = UILayout.ControlPanel
        # painel
        panel = pygame.Rect(cp.X, cp.Y, cp.WIDTH, cp.HEIGHT)
        pygame.draw.rect(app.screen, LGRAY, panel, border_radius=8)
        pygame.draw.rect(app.screen, DGRAY, panel, 2, border_radius=8)
        app.screen.blit(app.font.render("TSP - Genetic Algorithm", True, BLACK), (cp.X + cp.PAD, cp.TITLE_Y))

        x = cp.X + cp.PAD
        w = cp.WIDTH - 2*cp.PAD

        # --- Setup ---
        _card(app.screen, x, cp.SETUP_Y, w, cp.SETUP_H, "Setup", app.font)
        # Generate/Reset
        pygame.draw.rect(app.screen, WHITE if not app.running_algorithm else LGRAY, app.buttons['generate_map']); pygame.draw.rect(app.screen, BLACK, app.buttons['generate_map'], 2)
        app.screen.blit(app.font.render("Generate Map", True, BLACK), (app.buttons['generate_map'].x + 8, app.buttons['generate_map'].y + 5))
        pygame.draw.rect(app.screen, WHITE, app.buttons['reset']); pygame.draw.rect(app.screen, BLACK, app.buttons['reset'], 2)
        app.screen.blit(app.font.render("Reset", True, BLACK), (app.buttons['reset'].x + 24, app.buttons['reset'].y + 5))
        # Map types
        for key, label in [('map_random','Random'),('map_circle','Circle'),('map_custom','Custom')]:
            rect = app.buttons[key]
            color = GREEN if app.map_type == label.lower() else WHITE
            pygame.draw.rect(app.screen, color, rect); pygame.draw.rect(app.screen, BLACK, rect, 2)
            app.screen.blit(app.small_font.render(label, True, BLACK), app.small_font.render(label, True, BLACK).get_rect(center=rect.center))
        # Cities - display
        minus_r = app.buttons['cities_minus']; plus_r = app.buttons['cities_plus']
        pygame.draw.rect(app.screen, WHITE if not app.running_algorithm else LGRAY, minus_r); pygame.draw.rect(app.screen, BLACK, minus_r, 2)
        pygame.draw.rect(app.screen, WHITE if not app.running_algorithm else LGRAY, plus_r);  pygame.draw.rect(app.screen, BLACK, plus_r, 2)
        app.screen.blit(app.font.render("-", True, BLACK), app.font.render("-", True, BLACK).get_rect(center=minus_r.center))
        app.screen.blit(app.font.render("+", True, BLACK), app.font.render("+", True, BLACK).get_rect(center=plus_r.center))
        disp_rect = pygame.Rect(minus_r.right + 8, minus_r.y, plus_r.left - (minus_r.right + 16), minus_r.height)
        pygame.draw.rect(app.screen, WHITE, disp_rect, border_radius=4)
        pygame.draw.rect(app.screen, BLACK, disp_rect, 2)
        app.screen.blit(app.small_font.render(f"Cities: {app.num_cities}", True, BLACK), app.small_font.render(f"Cities: {app.num_cities}", True, BLACK).get_rect(center=disp_rect.center))

        # --- Run ---
        _card(app.screen, x, cp.RUN_Y, w, cp.RUN_H, "Run", app.font)

        # largura interna do card (4px de respiro em cada lado)
        inner_x = x + 4
        inner_w = w - 8
        row_y   = cp.RUN_Y + 36  # abaixo do título

        # 2 colunas com gap = 10
        bw = (inner_w - 10) // 2

        b1 = pygame.Rect(inner_x,          row_y, bw, cp.KPI_H)
        b2 = pygame.Rect(inner_x + bw + 10, row_y, bw, cp.KPI_H)
        row_y = b1.bottom + 8
        b3 = pygame.Rect(inner_x,          row_y, bw, cp.KPI_H)
        b4 = pygame.Rect(inner_x + bw + 10, row_y, bw, cp.KPI_H)

        for r, text in [
            (b1, f"Cities: {len(app.delivery_points)}"),
            (b2, f"Population: {app.population_size}"),
            (b3, f"Generation: {app.current_generation}/{app.max_generations}"),
            (b4, f"Best Dist.: {(1/app.best_fitness):.2f}" if getattr(app,'best_fitness',0) else "Best Dist.: N/A"),
        ]:
            pygame.draw.rect(app.screen, LGRAY, r, border_radius=4)
            pygame.draw.rect(app.screen, GRAY,  r, 1, border_radius=4)
            app.screen.blit(app.small_font.render(text, True, BLACK), (r.x + 8, r.y + 4))

        # barra de progresso ocupando toda a largura interna
        pct = (app.current_generation / app.max_generations) if getattr(app, 'max_generations', 0) else 0
        prog = pygame.Rect(inner_x, b3.bottom + 14, inner_w, 10)
        pygame.draw.rect(app.screen, LGRAY, prog, border_radius=4)
        pygame.draw.rect(app.screen, GRAY,  prog, 1, border_radius=4)
        fill = pygame.Rect(prog.x, prog.y, int(pct * prog.width), prog.height)
        pygame.draw.rect(app.screen, GREEN, fill, border_radius=4)

        # --- Operators ---
        _card(app.screen, x, cp.OPERATORS_Y, w, cp.OPERATORS_H, "Operators", app.font)
        # elitism
        r = app.buttons['toggle_elitism']
        pygame.draw.rect(app.screen, GREEN if app.elitism else RED, r); pygame.draw.rect(app.screen, BLACK, r, 2)
        app.screen.blit(app.small_font.render(f"Elitism: {'On' if app.elitism else 'Off'}", True, BLACK), (r.x + 8, r.y + 4))
        # labels
        app.screen.blit(app.small_font.render("Selection:", True, BLACK), (x + 4, cp.OPERATORS_Y + 36 + r.height + 10))
        mut_y = app.buttons['mutation_swap'].y
        app.screen.blit(app.small_font.render("Mutation:", True, BLACK), (x + 4, mut_y - 18))
        # seleção
        for key, lbl, method in [
            ('selection_roulette','Roleta','roulette'),
            ('selection_tournament','Torneio','tournament'),
            ('selection_rank','Ranking','rank')]:
            rect = app.buttons[key]
            color = UILayout.get_color('blue') if app.selection_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect); pygame.draw.rect(app.screen, BLACK, rect, 2)
            app.screen.blit(app.small_font.render(lbl, True, BLACK), app.small_font.render(lbl, True, BLACK).get_rect(center=rect.center))
        # mutação
        for key, lbl, method in [
            ('mutation_swap','Swap','swap'),
            ('mutation_inverse','Inverse','inverse'),
            ('mutation_shuffle','Shuffle','shuffle')]:
            rect = app.buttons[key]
            color = GREEN if app.mutation_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect); pygame.draw.rect(app.screen, BLACK, rect, 2)
            app.screen.blit(app.small_font.render(lbl, True, BLACK), app.small_font.render(lbl, True, BLACK).get_rect(center=rect.center))

        # --- Crossover ---
        _card(app.screen, x, cp.CROSSOVER_Y, w, cp.CROSSOVER_H, "Crossover", app.font)
        for key, lbl, method in [
            ('crossover_pmx','PMX','pmx'),
            ('crossover_ox1','OX1','ox1'),
            ('crossover_cx','CX','cx'),
            ('crossover_kpoint','K-Pt','kpoint'),
            ('crossover_erx','ERX','erx')]:
            rect = app.buttons[key]
            color = YELL if app.crossover_method == method else WHITE
            pygame.draw.rect(app.screen, color, rect); pygame.draw.rect(app.screen, BLACK, rect, 2)
            app.screen.blit(app.small_font.render(lbl, True, BLACK), app.small_font.render(lbl, True, BLACK).get_rect(center=rect.center))
        # Run/Stop
        rc = app.buttons['run_algorithm']
        rs = app.buttons['stop_algorithm']
        pygame.draw.rect(app.screen, GREEN if not app.running_algorithm else LGRAY, rc); pygame.draw.rect(app.screen, BLACK, rc, 2)
        pygame.draw.rect(app.screen, RED   if app.running_algorithm else LGRAY, rs); pygame.draw.rect(app.screen, BLACK, rs, 2)
        app.screen.blit(app.font.render("Run",  True, BLACK), (rc.x + 44, rc.y + 5))
        app.screen.blit(app.font.render("Stop", True, BLACK), (rs.x + 22, rs.y + 5))

        # --- Fitness ---
        _card(app.screen, x, cp.FITNESS_Y, w, cp.FITNESS_H, "Fitness History", app.font)
        # área do gráfico já é calculada em UILayout.FitnessGraph; só desenhar depois
        DrawFunctions.draw_fitness_graph(app)

    # -------------------- Rotas/Cidades (compat) --------------------
    @staticmethod
    def draw_cities(app: Any) -> None:
        for i, c in enumerate(app.delivery_points):
            pygame.draw.circle(app.screen, BLUE, (c.x, c.y), 7)
            pygame.draw.circle(app.screen, WHITE, (c.x, c.y), 5)
            t = app.small_font.render(str(i), True, BLACK)
            app.screen.blit(t, t.get_rect(center=(c.x, c.y)))

    @staticmethod
    def draw_route(app: Any, chromosome: Any, color: Tuple[int,int,int]=BLACK, width: int = 2) -> None:
        if not chromosome: return
        if hasattr(chromosome, 'delivery_points'):
            pts = list(chromosome.delivery_points)
        elif isinstance(chromosome, list) and chromosome and isinstance(chromosome[0], int):
            pts = [app.delivery_points[i] for i in chromosome]
        elif isinstance(chromosome, list):
            pts = chromosome
        else:
            return
        if len(pts) < 2: return
        points = [(p.x, p.y) for p in pts] + [(pts[0].x, pts[0].y)]
        pygame.draw.lines(app.screen, color, False, points, width)

    @staticmethod
    def draw(app: Any) -> None:
        DrawFunctions._draw_map_board(app)
        DrawFunctions.draw_interface(app)
