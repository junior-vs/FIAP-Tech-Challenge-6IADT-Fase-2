"""
Configurações centralizadas de layout da interface do usuário.
Este módulo centraliza todas as posições, tamanhos e cores da interface,
tornando fácil modificar o layout sem procurar por valores hardcoded.
"""
import pygame
from typing import Dict, Tuple

class UILayout:
    """Configurações centralizadas para o layout da interface."""
    
    # =============================================================================
    # CONFIGURAÇÕES DA JANELA PRINCIPAL
    # =============================================================================
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 900
    
    # =============================================================================
    # CORES PADRONIZADAS
    # =============================================================================
    COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'blue': (0, 0, 255),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'gray': (128, 128, 128),
        'light_gray': (200, 200, 200),
        'dark_gray': (64, 64, 64),
    }
    
    # =============================================================================
    # LAYOUT DA ÁREA DE CONTROLES (PAINEL ESQUERDO)
    # =============================================================================
    class ControlPanel:
        # Dimensões do painel de controles
        X = 10
        Y = 10
        WIDTH = 350
        HEIGHT = 800
        
        # Margens internas
        MARGIN_LEFT = 20
        MARGIN_TOP = 20
        SPACING_VERTICAL = 10
        
        # Posições Y das seções principais
        TITLE_Y = 20
        MAIN_BUTTONS_Y = 50
        MAP_TYPES_Y = 100
        CITY_COUNT_Y = 130
        ELITISM_Y = 170
        MUTATION_METHODS_Y = 220
        CROSSOVER_METHODS_Y = 270
        PARAMETERS_INFO_Y = 350
        ALGORITHM_INFO_Y = 450
        FITNESS_GRAPH_Y = 600
    
    # =============================================================================
    # CONFIGURAÇÕES DOS BOTÕES
    # =============================================================================
    class Buttons:
        # Tamanhos padrão dos botões
        LARGE_WIDTH = 120
        LARGE_HEIGHT = 30
        MEDIUM_WIDTH = 80
        MEDIUM_HEIGHT = 25
        SMALL_WIDTH = 60
        SMALL_HEIGHT = 25
        TINY_WIDTH = 25
        TINY_HEIGHT = 25
        
        # Espaçamento entre botões
        HORIZONTAL_SPACING = 10
        VERTICAL_SPACING = 5
        
        @staticmethod
        def create_button_positions() -> Dict[str, pygame.Rect]:
            """Cria todas as posições dos botões de forma organizada."""
            cp = UILayout.ControlPanel
            btn = UILayout.Buttons
            
            buttons = {}
            
            # =========================================================================
            # BOTÕES PRINCIPAIS (Generate Map, Reset)
            # =========================================================================
            main_buttons_x = cp.MARGIN_LEFT + 20  # Centralizado no painel
            buttons['generate_map'] = pygame.Rect(
                main_buttons_x, cp.MAIN_BUTTONS_Y, 
                btn.LARGE_WIDTH, btn.LARGE_HEIGHT
            )
            buttons['reset'] = pygame.Rect(
                main_buttons_x + btn.LARGE_WIDTH + btn.HORIZONTAL_SPACING, cp.MAIN_BUTTONS_Y,
                btn.LARGE_WIDTH, btn.LARGE_HEIGHT
            )
            
            # =========================================================================
            # BOTÕES DE TIPO DE MAPA (Random, Circle, Custom)
            # =========================================================================
            map_x = main_buttons_x
            buttons['map_random'] = pygame.Rect(
                map_x, cp.MAP_TYPES_Y, 
                btn.MEDIUM_WIDTH, btn.MEDIUM_HEIGHT
            )
            buttons['map_circle'] = pygame.Rect(
                map_x + btn.MEDIUM_WIDTH + btn.HORIZONTAL_SPACING, cp.MAP_TYPES_Y,
                btn.MEDIUM_WIDTH, btn.MEDIUM_HEIGHT
            )
            buttons['map_custom'] = pygame.Rect(
                map_x + 2 * (btn.MEDIUM_WIDTH + btn.HORIZONTAL_SPACING), cp.MAP_TYPES_Y,
                btn.MEDIUM_WIDTH, btn.MEDIUM_HEIGHT
            )
            
            # =========================================================================
            # CONTROLES DE NÚMERO DE CIDADES (-, display, +)
            # =========================================================================
            city_x = main_buttons_x
            buttons['cities_minus'] = pygame.Rect(
                city_x, cp.CITY_COUNT_Y, 
                btn.TINY_WIDTH, btn.TINY_HEIGHT
            )
            buttons['cities_plus'] = pygame.Rect(
                city_x + 240, cp.CITY_COUNT_Y,  # Posição calculada para ficar no final
                btn.TINY_WIDTH, btn.TINY_HEIGHT
            )
            
            # =========================================================================
            # BOTÃO DE ELITISMO
            # =========================================================================
            buttons['toggle_elitism'] = pygame.Rect(
                main_buttons_x, cp.ELITISM_Y, 
                btn.LARGE_WIDTH, btn.LARGE_HEIGHT
            )
            
            # =========================================================================
            # BOTÕES DE MÉTODOS DE MUTAÇÃO (Swap, Inverse, Shuffle)
            # =========================================================================
            mutation_x = main_buttons_x
            mutation_methods = ['mutation_swap', 'mutation_inverse', 'mutation_shuffle']
            for i, method in enumerate(mutation_methods):
                buttons[method] = pygame.Rect(
                    mutation_x + i * (btn.SMALL_WIDTH + btn.HORIZONTAL_SPACING), 
                    cp.MUTATION_METHODS_Y,
                    btn.SMALL_WIDTH, btn.SMALL_HEIGHT
                )
            
            # =========================================================================
            # BOTÕES DE MÉTODOS DE CROSSOVER (PMX, OX1, CX, K-Pt, ERX)
            # =========================================================================
            crossover_x = main_buttons_x
            crossover_methods = ['crossover_pmx', 'crossover_ox1', 'crossover_cx', 
                               'crossover_kpoint', 'crossover_erx']
            for i, method in enumerate(crossover_methods):
                buttons[method] = pygame.Rect(
                    crossover_x + i * (50 + 5),  # Botões menores para crossover
                    cp.CROSSOVER_METHODS_Y,
                    50, btn.SMALL_HEIGHT
                )
            
            # =========================================================================
            # BOTÕES DE CONTROLE DO ALGORITMO (Run, Stop)
            # =========================================================================
            buttons['run_algorithm'] = pygame.Rect(
                main_buttons_x, cp.CROSSOVER_METHODS_Y + 50, 
                btn.LARGE_WIDTH, btn.LARGE_HEIGHT
            )
            buttons['stop_algorithm'] = pygame.Rect(
                main_buttons_x + btn.LARGE_WIDTH + btn.HORIZONTAL_SPACING, 
                cp.CROSSOVER_METHODS_Y + 50,
                btn.LARGE_WIDTH, btn.LARGE_HEIGHT
            )
            
            return buttons
    
    # =============================================================================
    # LAYOUT DA ÁREA DO MAPA (LADO DIREITO)
    # =============================================================================
    class MapArea:
        X = 370  # Começa após o painel de controles
        Y = 10
        WIDTH = 820  # WINDOW_WIDTH - X - margem
        HEIGHT = 780
        
        # Área onde as cidades podem ser colocadas (com margem interna)
        CITIES_MARGIN = 30
        CITIES_X = X + CITIES_MARGIN
        CITIES_Y = Y + CITIES_MARGIN
        CITIES_WIDTH = WIDTH - 2 * CITIES_MARGIN
        CITIES_HEIGHT = HEIGHT - 2 * CITIES_MARGIN
        
        # Área para geração aleatória de cidades
        RANDOM_MIN_X = CITIES_X
        RANDOM_MAX_X = CITIES_X + CITIES_WIDTH
        RANDOM_MIN_Y = CITIES_Y
        RANDOM_MAX_Y = CITIES_Y + CITIES_HEIGHT
        
        # Centro para geração circular
        CIRCLE_CENTER_X = X + WIDTH // 2
        CIRCLE_CENTER_Y = Y + HEIGHT // 2
        CIRCLE_RADIUS = 200
    
    # =============================================================================
    # LAYOUT DO GRÁFICO DE FITNESS
    # =============================================================================
    class FitnessGraph:
        X = 20  # ControlPanel.MARGIN_LEFT
        Y = 600  # ControlPanel.FITNESS_GRAPH_Y
        WIDTH = 320
        HEIGHT = 200
        
        # Posições da legenda
        LEGEND_Y_OFFSET = 10
        LEGEND_LINE_LENGTH = 20
        LEGEND_TEXT_OFFSET = 5
        LEGEND_SPACING = 100  # Espaço entre itens da legenda
    
    # =============================================================================
    # CONFIGURAÇÕES DE TEXTO E FONTES
    # =============================================================================
    class Text:
        # Tamanhos de fonte
        FONT_SIZE_LARGE = 24
        FONT_SIZE_MEDIUM = 18
        FONT_SIZE_SMALL = 16
        
        # Espaçamentos para texto
        LINE_HEIGHT = 25
        SECTION_SPACING = 30
        
        # Posições específicas para labels
        CITY_COUNT_LABEL_Y = 135  # ControlPanel.CITY_COUNT_Y + 5
        MUTATION_LABEL_Y = 200   # ControlPanel.MUTATION_METHODS_Y - 20
        CROSSOVER_LABEL_Y = 250  # ControlPanel.CROSSOVER_METHODS_Y - 20
    
    # =============================================================================
    # ELEMENTOS ESPECIAIS
    # =============================================================================
    class SpecialElements:
        # Campo de exibição do número de cidades
        CITIES_DISPLAY_X = 70   # ControlPanel.MARGIN_LEFT + 50
        CITIES_DISPLAY_Y = 130  # ControlPanel.CITY_COUNT_Y
        CITIES_DISPLAY_WIDTH = 205
        CITIES_DISPLAY_HEIGHT = 25
        
        # Mensagem para modo customizado
        CUSTOM_MESSAGE_X = 400  # MapArea.X + 30
        CUSTOM_MESSAGE_Y = 400  # MapArea.Y + MapArea.HEIGHT // 2

    @staticmethod
    def get_color(color_name: str) -> Tuple[int, int, int]:
        """Retorna uma cor pelo nome."""
        return UILayout.COLORS.get(color_name, UILayout.COLORS['white'])
    
    @staticmethod
    def create_fonts() -> Dict[str, pygame.font.Font]:
        """Cria as fontes padronizadas."""
        return {
            'large': pygame.font.Font(None, UILayout.Text.FONT_SIZE_LARGE),
            'medium': pygame.font.Font(None, UILayout.Text.FONT_SIZE_MEDIUM),
            'small': pygame.font.Font(None, UILayout.Text.FONT_SIZE_SMALL),
        }