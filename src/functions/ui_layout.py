"""
Layout centralizado para a UI do TSP (cards fixos, sem sobreposição).
"""

import pygame
from typing import Dict, Tuple

# Tamanho da janela (não use UILayout dentro das classes aninhadas!)
WIN_W = 1280
WIN_H = 860

class UILayout:
    WINDOW_WIDTH  = WIN_W
    WINDOW_HEIGHT = WIN_H

    COLORS = {
        'white':      (250, 250, 250),
        'black':      ( 25,  25,  25),
        'gray':       (140, 140, 140),
        'light_gray': (225, 225, 225),
        'dark_gray':  ( 60,  60,  60),
        'green':      (  0, 170,  85),
        'red':        (210,  50,  50),
        'blue':       ( 56, 132, 255),
        'yellow':     (235, 185,   0),
    }

    @staticmethod
    def get_color(name: str) -> Tuple[int, int, int]:
        return UILayout.COLORS.get(name, UILayout.COLORS['white'])

    class ControlPanel:
        X, Y = 12, 12
        WIDTH  = 360
        HEIGHT = WIN_H - 24

        PAD = 16
        TITLE_Y = Y + 8

        # Cards (Y e alturas fixas — cabem confortavelmente)
        # título interno ocupa ~30px; conteúdo vem depois disso
        SETUP_Y      = Y + 48
        SETUP_H      = 150

        RUN_Y        = SETUP_Y + SETUP_H + 12
        RUN_H        = 120

        OPERATORS_Y  = RUN_Y + RUN_H + 12
        OPERATORS_H  = 170

        CROSSOVER_Y  = OPERATORS_Y + OPERATORS_H + 12
        CROSSOVER_H  = 120

        FITNESS_Y    = CROSSOVER_Y + CROSSOVER_H + 12
        FITNESS_H    = 170

        # para textos e badges
        KPI_H = 24

    class Buttons:
        LARGE_W, LARGE_H = 150, 32
        MED_W,   MED_H   = 110, 28
        SMALL_W, SMALL_H = 110, 26
        TINY_W,  TINY_H  = 28,  26
        GAP_X,   GAP_Y   = 8,   8

        @staticmethod
        def create_button_positions() -> Dict[str, pygame.Rect]:
            cp = UILayout.ControlPanel
            b  = UILayout.Buttons

            # área interna do card
            x0 = cp.X + cp.PAD + 4          # 4px de respiro à esquerda
            w  = cp.WIDTH - 2*cp.PAD        # largura útil do card
            w_inner = w - 8                 # +4px de respiro à direita (total 4+4)

            btns: Dict[str, pygame.Rect] = {}

            # ---------- SETUP ----------
            y = cp.SETUP_Y + 36

            # generate + reset (cabem folgados)
            btns['generate_map'] = pygame.Rect(x0, y, b.LARGE_W, b.LARGE_H)
            btns['reset']        = pygame.Rect(x0 + b.LARGE_W + 10, y, b.MED_W, b.LARGE_H)
            y += b.LARGE_H + b.GAP_Y

            # 3 colunas distribuídas na largura *interna*
            cols3_w = (w_inner - 2*b.GAP_X) // 3
            btns['map_random'] = pygame.Rect(x0, y, cols3_w, b.SMALL_H)
            btns['map_circle'] = pygame.Rect(x0 + cols3_w + b.GAP_X, y, cols3_w, b.SMALL_H)
            btns['map_custom'] = pygame.Rect(x0 + 2*(cols3_w + b.GAP_X), y, cols3_w, b.SMALL_H)
            y += b.SMALL_H + b.GAP_Y

            # cidades: '-' [display] '+'
            btns['cities_minus'] = pygame.Rect(x0, y, b.TINY_W, b.TINY_H)
            btns['cities_plus']  = pygame.Rect(x0 + w_inner - b.TINY_W, y, b.TINY_W, b.TINY_H)

            # ---------- OPERATORS ----------
            y = cp.OPERATORS_Y + 36
            btns['toggle_elitism'] = pygame.Rect(x0, y, 130, b.SMALL_H)
            y += b.SMALL_H + 10

            # Selection (3 colunas)
            y_sel = y + 18
            btns['selection_roulette']   = pygame.Rect(x0, y_sel, cols3_w, b.SMALL_H)
            btns['selection_tournament'] = pygame.Rect(x0 + cols3_w + b.GAP_X, y_sel, cols3_w, b.SMALL_H)
            btns['selection_rank']       = pygame.Rect(x0 + 2*(cols3_w + b.GAP_X), y_sel, cols3_w, b.SMALL_H)

            # Mutation (3 colunas) — encolhe 4px por botão para garantir que caibam
            y_mut = y_sel + b.SMALL_H + 24    # já com respiro p/ o label
            cols3_w_mut = max(80, cols3_w - 4)  # <- ajuste fino de largura

            start_x = x0
            btns['mutation_swap']    = pygame.Rect(start_x, y_mut, cols3_w_mut, b.SMALL_H)
            start_x += cols3_w_mut + b.GAP_X
            btns['mutation_inverse'] = pygame.Rect(start_x, y_mut, cols3_w_mut, b.SMALL_H)
            start_x += cols3_w_mut + b.GAP_X
            btns['mutation_shuffle'] = pygame.Rect(start_x, y_mut, cols3_w_mut, b.SMALL_H)

            # ---------- CROSSOVER ----------
            y = cp.CROSSOVER_Y + 36
            # 5 colunas distribuídas dentro do w_inner
            cols5_w = (w_inner - 4*b.GAP_X) // 5
            names = ['crossover_pmx','crossover_ox1','crossover_cx','crossover_kpoint','crossover_erx']
            for i, key in enumerate(names):
                btns[key] = pygame.Rect(x0 + i*(cols5_w + b.GAP_X), y, cols5_w, b.SMALL_H)
            y += b.SMALL_H + 10

            # Run/Stop
            btns['run_algorithm']  = pygame.Rect(x0, y, b.LARGE_W, b.LARGE_H)
            btns['stop_algorithm'] = pygame.Rect(x0 + b.LARGE_W + 10, y, b.MED_W, b.LARGE_H)

            return btns


    class MapArea:
        X = 12 + 360 + 12
        Y = 12
        WIDTH  = WIN_W - X - 12
        HEIGHT = WIN_H - 24

        PAD = 24
        CITIES_X = X + PAD
        CITIES_Y = Y + PAD
        CITIES_WIDTH  = WIDTH  - 2*PAD
        CITIES_HEIGHT = HEIGHT - 2*PAD

        RANDOM_MIN_X = CITIES_X
        RANDOM_MAX_X = CITIES_X + CITIES_WIDTH
        RANDOM_MIN_Y = CITIES_Y
        RANDOM_MAX_Y = CITIES_Y + CITIES_HEIGHT

        CIRCLE_CENTER_X = X + WIDTH // 2
        CIRCLE_CENTER_Y = Y + HEIGHT // 2
        CIRCLE_RADIUS   = 220

    class FitnessGraph:
    # Posição e tamanho do retângulo do gráfico dentro do card "Fitness History".
    # Valores pré-calculados (evitam referenciar ControlPanel aqui).
    # Cálculo usado:
    #   X = 12 (cp.X) + 16 (cp.PAD) + 8  = 36
    #   Y = FITNESS_Y + 36 (título do card) + 4
    #     = (668) + 40 = 708
    #   WIDTH  = 360 (cp.WIDTH) - 2*16 (2*cp.PAD) - 16 = 312
    #   HEIGHT = 230 (FITNESS_H) - 36 (título) - 16 (margens) = 178
        # X e Y permanecem iguais
        X = 36
        Y = 708
        # largura idem; altura diminui 30 px (200 - 36 - 16 = 148)
        WIDTH  = 312
        HEIGHT = 148

    class Text:
        FONT_L = 24
        FONT_M = 18
        FONT_S = 15
        LINE_H = 24

    @staticmethod
    def create_fonts():
        return {
            'large':  pygame.font.Font(None, UILayout.Text.FONT_L),
            'medium': pygame.font.Font(None, UILayout.Text.FONT_M),
            'small':  pygame.font.Font(None, UILayout.Text.FONT_S),
        }
