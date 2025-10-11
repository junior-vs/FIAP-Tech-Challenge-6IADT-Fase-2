# src/main/TSPGeneticAlgorithm.py
import sys
from typing import List, Tuple
import random
import math
import os
import pygame
import numpy as np
from datetime import datetime
import json
import re

# Configurar paths para imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # adiciona 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../domain")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../functions")))

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
from llm.report_generator import LLMServices

# Inicializar pygame
pygame.init()

# Usar configurações centralizadas do layout
WINDOW_WIDTH = UILayout.WINDOW_WIDTH
WINDOW_HEIGHT = UILayout.WINDOW_HEIGHT

# Importar cores do layout centralizado
WHITE = UILayout.get_color("white")
BLACK = UILayout.get_color("black")
BLUE = UILayout.get_color("blue")
RED = UILayout.get_color("red")
GREEN = UILayout.get_color("green")
GRAY = UILayout.get_color("gray")
LIGHT_GRAY = UILayout.get_color("light_gray")


# =========================
# Helpers de Normalização LLM
# =========================
def _extract_json_block(md: str):
    """
    Extrai o primeiro bloco JSON de um Markdown no formato ```json ... ``` .
    Se não achar, tenta detectar JSON 'nu'.
    """
    if not isinstance(md, str):
        return None
    # bloco ```json ... ```
    m = re.search(r"```json\s*(.*?)```", md, flags=re.S | re.I)
    if m:
        blob = m.group(1).strip()
        try:
            return json.loads(blob)
        except Exception:
            pass
    # fallback: tenta achar um JSON no início
    md_stripped = md.strip()
    if md_stripped.startswith("{") or md_stripped.startswith("["):
        try:
            return json.loads(md_stripped)
        except Exception:
            # tenta heurística: do início até a primeira linha em branco dupla
            parts = re.split(r"\n\s*\n", md_stripped, maxsplit=1)
            try:
                return json.loads(parts[0])
            except Exception:
                return None
    return None


def _strip_first_json_block(md: str) -> str:
    """Remove o primeiro bloco ```json ... ``` do Markdown, se existir."""
    if not isinstance(md, str):
        return ""
    return re.sub(r"^```json.*?```(\r?\n)?", "", md, flags=re.S | re.I)


def _rebuild_md_with_json(obj: dict | list, tail_md: str) -> str:
    """Reconstrói o Markdown com o JSON (normalizado) no topo e o restante do texto depois."""
    try:
        head = "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```\n\n"
    except Exception:
        head = "```json\n{}\n```\n\n"
    return head + (tail_md or "").lstrip()


def _normalize_first_json(md: str, *, default_obj: dict, list_key: str) -> tuple[dict, str]:
    """
    Garante que o 1º bloco JSON do Markdown seja **objeto**.
    - Se vier LISTA, embrulha em {list_key: lista}
    - Se vier OBJETO, mantém
    - Qualquer outra coisa → default_obj

    Retorna (objeto_normalizado, markdown_normalizado).
    """
    parsed = _extract_json_block(md)
    if isinstance(parsed, list):
        obj = {list_key: parsed}
    elif isinstance(parsed, dict):
        obj = parsed
    else:
        obj = default_obj

    tail = _strip_first_json_block(md)
    md_norm = _rebuild_md_with_json(obj, tail)
    return obj, md_norm


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
        self.font = fonts["large"]
        self.small_font = fonts["medium"]

        # Variáveis do algoritmo
        self.delivery_points: List[DeliveryPoint] = []
        self.distance_matrix = None
        self.population: List[Route] = []
        self.population_size = 50
        self.max_generations = 100
        self.mutation_method = "swap"  # Default method: swap
        self.crossover_method = "pmx"  # Default method: PMX
        self.selection_method = "roulette"  # Default method: roulette
        self.elitism = True
        self.running_algorithm = False
        self.current_generation = 0
        self.best_route: Route | None = None
        self.best_fitness = 0.0
        self.fitness_history: List[float] = []
        self.mean_fitness_history: List[float] = []

        # Interface - usar layout centralizado
        self.ui_layout = UILayout()
        self.map_type = "random"  # "random", "circle", "custom"
        self.num_cities = 10
        self.buttons = UILayout.Buttons.create_button_positions()

        # >>> Botão extra: Perguntar à IA
        side_x = UILayout.MapArea.X + UILayout.MapArea.WIDTH + 20
        side_y = UILayout.MapArea.Y + 320
        self.ask_btn_rect = pygame.Rect(side_x, side_y, 260, 40)
        self._show_console_hint_frames = 0  # contador para aviso “digite no terminal…”

        self.logger.info("Aplicação inicializada com sucesso")

        # Inicialização do módulo LLM
        self.llm = LLMServices()
        self.output_dir = os.path.join(os.getcwd(), "out")
        os.makedirs(self.output_dir, exist_ok=True)

        # Flags por .env (mantidas para futuro uso)
        self.llm_strict = os.getenv("LLM_STRICT") == "1"
        self.llm_disable_cache = os.getenv("LLM_DISABLE_CACHE") == "1"

    def _make_random_product(self, idx: int) -> Product:
        """Gera um produto válido aleatório respeitando as restrições.
        - Cada lado <= 100 cm; soma <= 200 cm; peso <= 10000 g.
        """
        name = f"Produto-{idx}"
        weight = random.randint(100, 10_000)
        for _ in range(100):
            a = random.uniform(5.0, 100.0)
            b = random.uniform(5.0, 100.0)
            max_c = min(100.0, 200.0 - (a + b))
            if max_c > 5.0:
                c = random.uniform(5.0, max_c)
                dims = [a, b, c]
                random.shuffle(dims)
                try:
                    return Product(
                        name=name,
                        weight=weight,
                        length=dims[0],
                        width=dims[1],
                        height=dims[2],
                    )
                except ValueError:
                    continue
        return Product(name=name, weight=min(weight, 10_000), length=100, width=50, height=50)

    def generate_cities(self, map_type: str, num_cities: int = 10):
        """Gera cidades baseado no tipo de mapa selecionado usando configurações centralizadas."""
        self.logger.info(f"Gerando {num_cities} cidades usando mapa tipo '{map_type}'")
        self.delivery_points = []

        if map_type == "random":
            for i in range(num_cities):
                x = random.randint(UILayout.MapArea.RANDOM_MIN_X, UILayout.MapArea.RANDOM_MAX_X)
                y = random.randint(UILayout.MapArea.RANDOM_MIN_Y, UILayout.MapArea.RANDOM_MAX_Y)
                prod = self._make_random_product(i)
                self.delivery_points.append(DeliveryPoint(x, y, product=prod))

        elif map_type == "circle":
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
            self.logger.info("Modo customizado ativado - aguardando input do usuário")

        if self.delivery_points:
            self.calculate_distance_matrix()
            self.logger.info(f"Geradas {len(self.delivery_points)} cidades com sucesso")

    def initialize_population(self):
        """Inicializa a população com cromossomos aleatórios"""
        self.population = []
        base = list(self.delivery_points)
        for _ in range(self.population_size):
            shuffled = base[:]
            random.shuffle(shuffled)
            self.population.append(Route(shuffled))

    def selection(self, population: List[Route], fitness_scores: List[float]) -> List[Route]:
        """Seleção usando métodos do selection_functions.py com suporte a diferentes algoritmos e elitismo."""
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return population.copy()

        new_population = []
        for _ in range(len(population)):
            if self.selection_method == "roulette":
                chosen = Selection.roulette(population, fitness_scores)
            elif self.selection_method == "tournament":
                chosen = Selection.tournament(population, fitness_scores, tournament_size=3)
            elif self.selection_method == "rank":
                chosen = Selection.rank(population, fitness_scores)
            else:
                chosen = Selection.roulette(population, fitness_scores)
            new_population.append(chosen.copy())

        if self.elitism and self.best_route:
            best_idx = fitness_scores.index(max(fitness_scores))
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
            child1 = Crossover.erx_crossover(parent1, parent2)
            child2 = Crossover.erx_crossover(parent2, parent1)
            return child1, child2
        else:
            return Crossover.crossover_parcialmente_mapeado_pmx(parent1, parent2)

    def mutate(self, route: Route) -> Route:
        """Aplica operador de mutação conforme método selecionado."""
        if self.mutation_method == "swap":
            return Mutation.mutacao_por_troca(route)
        elif self.mutation_method == "inverse":
            return Mutation.mutacao_por_inversao(route)
        elif self.mutation_method == "shuffle":
            return Mutation.mutacao_por_embaralhamento(route)
        else:
            return Mutation.mutacao_por_troca(route)

    def calculate_distance_matrix(self):
        """Calcula a matriz de distâncias entre todos os pontos de entrega"""
        self.distance_matrix = DeliveryPoint.compute_distance_matrix(self.delivery_points)

    def run_generation(self):
        """Executa uma geração do algoritmo genético"""
        if not self.population:
            self.initialize_population()

        fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ind) for ind in self.population]

        max_fitness = max(fitness_scores)
        if max_fitness > self.best_fitness:
            old_fitness = self.best_fitness
            self.best_fitness = max_fitness
            best_idx = fitness_scores.index(max_fitness)
            self.best_route = self.population[best_idx].copy()

            if old_fitness == 0 or (max_fitness - old_fitness) / old_fitness > 0.1:
                self.logger.info(
                    f"Geração {self.current_generation}: Nova melhor fitness {max_fitness:.4f} (+{max_fitness - old_fitness:.4f})"
                )

        self.fitness_history.append(max_fitness)
        mean_fitness = np.mean(fitness_scores)
        self.mean_fitness_history.append(mean_fitness)

        if self.current_generation % 10 == 0:
            self.logger.debug(
                f"Geração {self.current_generation}: Fitness média={mean_fitness:.4f}, Melhor={max_fitness:.4f}"
            )

        self.population = self.selection(self.population, fitness_scores)

        new_population = []
        for i in range(0, len(self.population), 2):
            parent1 = self.population[i]
            parent2 = self.population[(i + 1) % len(self.population)]
            child1, child2 = self.crossover(parent1, parent2)
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            new_population.extend([child1, child2])

        self.population = new_population[: self.population_size]
        self.current_generation += 1

    def handle_custom_input(self, pos):
        """Permite ao usuário clicar para adicionar cidades customizadas usando área definida no layout."""
        if self.map_type == "custom" and pos[0] > UILayout.MapArea.X:
            if (
                UILayout.MapArea.CITIES_X <= pos[0] <= UILayout.MapArea.CITIES_X + UILayout.MapArea.CITIES_WIDTH
                and UILayout.MapArea.CITIES_Y <= pos[1] <= UILayout.MapArea.CITIES_Y + UILayout.MapArea.CITIES_HEIGHT
            ):
                prod = self._make_random_product(len(self.delivery_points))
                self.delivery_points.append(DeliveryPoint(pos[0], pos[1], product=prod))
                if len(self.delivery_points) > 1:
                    self.calculate_distance_matrix()

    # -------------------- Fluxo de Perguntas à IA --------------------
    def _ask_llm_flow(self):
        """Fluxo completo para pergunta em linguagem natural via botão/atalho."""
        snapshot = self._build_route_snapshot()
        if not snapshot.get("stops"):
            self.logger.warning("[LLM] Snapshot sem 'stops'. Gere o mapa/rota antes de perguntar.")
            return

        # dica visual por alguns frames
        self._show_console_hint_frames = 180  # ~3s a 60 FPS

        try:
            question = input("Digite sua pergunta sobre a rota (ex.: 'Qual é a primeira parada prioritária?'): ").strip()
        except EOFError:
            question = ""

        if not question:
            self.logger.info("[LLM] Pergunta vazia — cancelado.")
            return

        self.logger.info(f"[LLM] Respondendo pergunta: {question}")
        try:
            # Sem kwargs extras: LLMServices já lida com strict/cache via env
            answer_md = self.llm.answer_natural_language(question, snapshot)
        except Exception as e:
            self.logger.error(f"[LLM] Erro ao obter resposta: {e}")
            return

        # Normalização defensiva local
        default_nlq = {"answer": "", "references": []}
        nlq_obj, answer_md = _normalize_first_json(answer_md, default_obj=default_nlq, list_key="references")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ans_path = os.path.join(self.output_dir, f"resposta_{ts}.md")
        with open(ans_path, "w", encoding="utf-8") as f:
            f.write(f"# Pergunta\n{question}\n\n# Resposta\n{answer_md}\n")
        self.logger.info(f"[LLM] Resposta salva em: {ans_path}")
        print("\n==== RESPOSTA DA IA ====\n" + answer_md + "\n=========================\n")

    def handle_events(self):
        """Gerencia eventos do pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if self.buttons["generate_map"].collidepoint(pos) and not self.running_algorithm:
                    self.generate_cities(self.map_type, self.num_cities)

                elif self.buttons["run_algorithm"].collidepoint(pos) and not self.running_algorithm:
                    if self.delivery_points:
                        self.start_algorithm()

                elif self.buttons["stop_algorithm"].collidepoint(pos) and self.running_algorithm:
                    self.stop_algorithm()

                elif self.buttons["reset"].collidepoint(pos):
                    self.reset_algorithm()

                elif self.buttons["map_random"].collidepoint(pos):
                    self.map_type = "random"

                elif self.buttons["map_circle"].collidepoint(pos):
                    self.map_type = "circle"

                elif self.buttons["map_custom"].collidepoint(pos):
                    self.map_type = "custom"
                    self.delivery_points = []

                elif self.buttons["toggle_elitism"].collidepoint(pos):
                    self.elitism = not self.elitism

                elif "selection_roulette" in self.buttons and self.buttons["selection_roulette"].collidepoint(pos):
                    if self.selection_method != "roulette":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → roulette")
                        self.selection_method = "roulette"
                elif "selection_tournament" in self.buttons and self.buttons["selection_tournament"].collidepoint(pos):
                    if self.selection_method != "tournament":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → tournament")
                        self.selection_method = "tournament"
                elif "selection_rank" in self.buttons and self.buttons["selection_rank"].collidepoint(pos):
                    if self.selection_method != "rank":
                        self.logger.info(f"Método de seleção alterado: {self.selection_method} → rank")
                        self.selection_method = "rank"

                elif self.buttons["cities_minus"].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities > 3:
                        self.num_cities -= 1

                elif self.buttons["cities_plus"].collidepoint(pos) and not self.running_algorithm:
                    if self.num_cities < 50:
                        self.num_cities += 1

                elif self.buttons["mutation_swap"].collidepoint(pos):
                    self.mutation_method = "swap"
                elif self.buttons["mutation_inverse"].collidepoint(pos):
                    self.mutation_method = "inverse"
                elif self.buttons["mutation_shuffle"].collidepoint(pos):
                    self.mutation_method = "shuffle"

                elif self.buttons["crossover_pmx"].collidepoint(pos):
                    self.crossover_method = "pmx"
                elif self.buttons["crossover_ox1"].collidepoint(pos):
                    self.crossover_method = "ox1"
                elif self.buttons["crossover_cx"].collidepoint(pos):
                    self.crossover_method = "cx"
                elif self.buttons["crossover_kpoint"].collidepoint(pos):
                    self.crossover_method = "kpoint"
                elif self.buttons["crossover_erx"].collidepoint(pos):
                    self.crossover_method = "erx"

                # Modo customizado - adicionar cidade
                elif self.map_type == "custom":
                    self.handle_custom_input(pos)

                # >>> Clique no botão "Perguntar à IA"
                if self.ask_btn_rect.collidepoint(pos):
                    self._ask_llm_flow()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.running_algorithm:
                    if self.delivery_points:
                        self.start_algorithm()
                elif event.key == pygame.K_ESCAPE:
                    if self.running_algorithm:
                        self.stop_algorithm()
                    else:
                        return False

                # Atalho "R" para gerar relatórios e instruções
                elif event.key == pygame.K_r:
                    self.logger.info("[LLM] Gerando relatório e instruções via Gemini...")
                    snapshot = self._build_route_snapshot()

                    if not snapshot.get("stops"):
                        self.logger.warning(
                            "[LLM] Snapshot sem 'stops'. Gere o mapa e/ou rode o algoritmo antes de apertar 'R'."
                        )
                        continue
                    print(json.dumps(snapshot, indent=2, ensure_ascii=False))

                    try:
                        # Sem kwargs extras: LLMServices já lida com strict/cache via env
                        instructions_md = self.llm.generate_driver_instructions(snapshot)
                        report_md = self.llm.generate_period_report(
                            {"snapshot": snapshot, "operation_date": snapshot.get("date", "")[:7]},  # mostra YYYY-MM
                            "Diário",
                        )

                        # Normalização defensiva local das duas saídas
                        default_instr = {
                            "vehicle_id": None,
                            "checklist": ["Documentos", "EPIs", "Conferência de volumes"],
                            "stops": [],
                            "cautions": [],
                            "summary": None
                        }
                        instr_obj, instructions_md = _normalize_first_json(
                            instructions_md, default_obj=default_instr, list_key="stops"
                        )

                        default_report = {
                            "period": "diário",
                            "totals": {"km": 0.0, "stops": 0, "time_min": 0},
                            "notes": []
                        }
                        report_obj, report_md = _normalize_first_json(
                            report_md, default_obj=default_report, list_key="rows"
                        )

                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        instr_path = os.path.join(self.output_dir, f"instrucoes_{ts}.md")
                        rep_path = os.path.join(self.output_dir, f"relatorio_{ts}.md")

                        with open(instr_path, "w", encoding="utf-8") as f:
                            f.write(instructions_md)
                        with open(rep_path, "w", encoding="utf-8") as f:
                            f.write(report_md)

                        self.logger.info(f"[LLM] Instruções salvas em: {instr_path}")
                        self.logger.info(f"[LLM] Relatório salvo em: {rep_path}")

                    except Exception as e:
                        self.logger.error(f"[LLM] Erro ao gerar instruções/relatório: {e}")

                # >>> Atalho Q para o mesmo fluxo do botão
                elif event.key == pygame.K_q:
                    self._ask_llm_flow()

        return True

    def start_algorithm(self):
        """Inicia o algoritmo genético"""
        if not self.delivery_points:
            self.logger.warning("Tentativa de iniciar algoritmo sem pontos de entrega")
            return

        self.logger.info(f"Iniciando algoritmo genético com {len(self.delivery_points)} cidades")
        self.logger.info(f"Configurações: população={self.population_size}, gerações={self.max_generations}")
        self.logger.info(
            f"Métodos: seleção={self.selection_method}, crossover={self.crossover_method}, mutação={self.mutation_method}, elitismo={self.elitism}"
        )

        self.running_algorithm = True
        self.current_generation = 0
        self.best_fitness = 0.0
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
        self.best_fitness = 0.0
        self.best_route = None
        self.fitness_history = []
        self.mean_fitness_history = []

    def _build_route_snapshot(self) -> dict:
        """
        Monta um snapshot detalhado da rota para o LLM.
        Regras:
          - Se existir best_route, usa ela.
          - Senão, usa o melhor indivíduo da população (se houver).
          - Senão, usa a ordem dos delivery_points (mapa gerado).
        Sempre devolve 'stops' quando houver pontos disponíveis.
        """
        try:
            # 1) Escolher a sequência de pontos da rota
            points = []
            route_source = "none"
            if getattr(self, "best_route", None) and getattr(self.best_route, "points", None):
                points = list(self.best_route.points)
                route_source = "best_route"
            elif getattr(self, "population", None):
                try:
                    fitness_scores = [FitnessFunction.calculate_fitness_with_constraints(ch) for ch in self.population]
                    if fitness_scores:
                        best_idx = fitness_scores.index(max(fitness_scores))
                        points = list(self.population[best_idx].points)
                        route_source = "population_best"
                except Exception:
                    route_source = "population_error"
                    points = []
            if not points and self.delivery_points:
                points = list(self.delivery_points)
                route_source = "delivery_points"

            if not points:
                # sem pontos, devolve snapshot mínimo (evita lista vazia)
                return {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "map_type": getattr(self, "map_type", "unknown"),
                    "num_cities": 0,
                    "best_fitness": 0.0,
                    "stops": [],
                    "constraints": {
                        "vehicle_capacity_kg": 100,
                        "vehicle_range_km": 200,
                        "priority_policy": "Critica > Alta > Media > Baixa",
                    },
                    "notes": "Sem pontos para gerar snapshot.",
                }

            # 2) Construir stops enxutos (para evitar bloqueios e reduzir tamanho do prompt)
            stops = []
            for i, p in enumerate(points):
                prod = getattr(p, "product", None)
                prod_dict = {}
                if prod:
                    prod_dict = {
                        "name": getattr(prod, "name", f"Item-{i+1}"),
                        "weight_g": int(getattr(prod, "weight", 0) or 0),
                        "cold_chain": False,
                    }

                stops.append({
                    "order": i + 1,
                    "coords": {"x": int(p.x), "y": int(p.y)},
                    "priority": "Media",  # sem acento e sem termos “Crítica”
                    "time_window": "08:00-18:00",
                    "items": [prod_dict] if prod_dict else [],
                })

            # Limitar número de paradas enviadas à LLM (configurável por env)
            max_stops = int(os.getenv("LLM_MAX_STOPS", "6"))
            stops = stops[:max_stops]

            snapshot = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "map_type": getattr(self, "map_type", "unknown"),
                "num_cities": len(self.delivery_points),
                "best_fitness": float(getattr(self, "best_fitness", 0.0) or 0.0),
                "stops": stops,
                "constraints": {
                    "vehicle_capacity_kg": 100,
                    "vehicle_range_km": 200,
                    "priority_policy": "Critica > Alta > Media > Baixa",
                },
                "notes": f"Snapshot gerado automaticamente (fonte da rota: {route_source}).",
            }
            return snapshot

        except Exception as e:
            self.logger.error(f"Erro ao montar snapshot de rota: {e}")
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "map_type": getattr(self, "map_type", "unknown"),
                "num_cities": len(self.delivery_points),
                "best_fitness": float(getattr(self, "best_fitness", 0.0) or 0.0),
                "stops": [],
                "constraints": {
                    "vehicle_capacity_kg": 100,
                    "vehicle_range_km": 200,
                    "priority_policy": "Critica > Alta > Media > Baixa",
                },
                "notes": "Falha ao montar snapshot.",
            }

    def _draw_ask_button(self):
        """Desenha o botão 'Perguntar à IA' e, opcionalmente, uma dica temporária."""
        pygame.draw.rect(self.screen, LIGHT_GRAY, self.ask_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, self.ask_btn_rect, 2, border_radius=8)
        label = self.small_font.render("Perguntar à IA (Q)", True, BLACK)
        label_rect = label.get_rect(center=self.ask_btn_rect.center)
        self.screen.blit(label, label_rect)

        # Mostra aviso por alguns frames quando vamos usar o input no console
        if self._show_console_hint_frames > 0:
            hint = self.small_font.render("Digite sua pergunta no terminal ↑", True, BLUE)
            hint_rect = hint.get_rect()
            hint_rect.topleft = (self.ask_btn_rect.left, self.ask_btn_rect.bottom + 8)
            self.screen.blit(hint, hint_rect)
            self._show_console_hint_frames -= 1

    def run(self):
        """Loop principal do programa"""
        self.logger.info("Iniciando loop principal da aplicação")
        running = True

        while running:
            running = self.handle_events()

            if self.running_algorithm and self.current_generation < self.max_generations:
                self.run_generation()
                if self.current_generation >= self.max_generations:
                    self.logger.info(f"Algoritmo finalizado após {self.max_generations} gerações")
                    self.logger.info(f"Melhor fitness final: {self.best_fitness:.4f}")
                    self.running_algorithm = False

            self.screen.fill(WHITE)

            map_rect = (UILayout.MapArea.X, UILayout.MapArea.Y, UILayout.MapArea.WIDTH, UILayout.MapArea.HEIGHT)
            pygame.draw.rect(self.screen, WHITE, map_rect)
            pygame.draw.rect(self.screen, BLACK, map_rect, 2)

            DrawFunctions.draw_interface(self)

            # Botão "Perguntar à IA"
            self._draw_ask_button()

            if self.delivery_points:
                if self.best_route:
                    DrawFunctions.draw_route(self, self.best_route, RED, 3)

                if self.population and self.running_algorithm:
                    fitness_scores = [
                        FitnessFunction.calculate_fitness_with_constraints(chrom) for chrom in self.population
                    ]
                    if fitness_scores:
                        best_idx = fitness_scores.index(max(fitness_scores))
                        current_best = self.population[best_idx]
                        DrawFunctions.draw_route(self, current_best, BLUE, 2)

                DrawFunctions.draw_cities(self)

            if self.map_type == "custom" and not self.delivery_points:
                instruction = self.font.render("Click on the map to add cities", True, BLACK)
                self.screen.blit(
                    instruction,
                    (UILayout.SpecialElements.CUSTOM_MESSAGE_X, UILayout.SpecialElements.CUSTOM_MESSAGE_Y),
                )

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
