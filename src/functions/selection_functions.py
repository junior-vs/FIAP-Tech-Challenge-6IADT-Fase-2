import random
from typing import List

from route import Route
from app_logging import log_performance, get_logger

# Logger para este módulo
logger = get_logger(__name__)


@log_performance
def tournament_selection(
    population: List[Route],
    aptitudes: List[float],
    tournament_size: int
) -> Route:
    """
    Seleciona uma Rota da população usando o método de seleção por torneio.
    """
    logger.debug(f"Seleção por torneio: população={len(population)}, tamanho_torneio={tournament_size}")
    
    population_with_aptitude = list(zip(population, aptitudes))
    tournament = random.sample(population_with_aptitude, tournament_size)
    winner = min(tournament, key=lambda item: item[1])
    
    logger.debug(f"Vencedor do torneio com fitness: {winner[1]:.6f}")
    return winner[0]


@log_performance
def tournament_selection_refined(
    population: List[Route],
    distances: List[float],
    tournament_size: int
) -> Route:
    """
    Versão refinada da seleção por torneio.
    - Utiliza 'distances' para clareza (problema de minimização).
    - Trabalha com índices para eficiência de memória.
    - Adiciona uma verificação de robustez.
    """
    population_size = len(population)
    logger.debug(f"Seleção por torneio refinada: população={population_size}, tamanho_torneio={tournament_size}")
    
    assert 1 <= tournament_size <= population_size, "O tamanho do torneio deve ser válido."

    # Seleciona 'tournament_size' índices aleatórios
    competitor_indices = random.sample(range(population_size), tournament_size)
    
    # Encontra o índice do vencedor (aquele com a menor distância)
    winner_index = min(competitor_indices, key=lambda index: distances[index])
    
    logger.debug(f"Vencedor com distância: {distances[winner_index]:.2f}")
    return population[winner_index]


@log_performance
def roulette_wheel_selection(
    population: List[Route],
    aptitudes: List[float] # Fitness here MUST be a value to be maximized (e.g., 1/distance)
) -> Route:
    """
    Seleciona uma Rota da população usando o método da Roleta.
    A probabilidade de seleção é proporcional à aptidão.
    """
    total_fitness = sum(aptitudes)
    logger.debug(f"Seleção por roleta: população={len(population)}, fitness_total={total_fitness:.6f}")
    
    # Se todas as aptidões forem zero (caso extremo), retorna um indivíduo aleatório
    if total_fitness == 0:
        logger.warning("Todas as aptidões são zero - seleção aleatória")
        return random.choice(population)
        
    # Gera um ponto aleatório na "roleta"
    pick = random.uniform(0, total_fitness)
    logger.debug(f"Ponto da roleta: {pick:.6f}")
    
    current = 0
    for individual, fitness in zip(population, aptitudes):
        current += fitness
        if current > pick:
            logger.debug(f"Indivíduo selecionado com fitness: {fitness:.6f}")
            return individual
            
    # Fallback para garantir que sempre retorne um indivíduo
    logger.debug("Fallback: retornando último indivíduo")
    return population[-1]


@log_performance
def rank_selection(
    population: List[Route],
    aptitudes: List[float] # Aptidão aqui DEVE ser um valor a ser maximizado
) -> Route:
    """
    Seleciona uma Rota usando Seleção por Rank.
    Resolve o problema de "super-indivíduos" da roleta.
    """
    logger.debug(f"Seleção por ranking: população={len(population)}")
    
    # 1. Emparelha cada indivíduo com sua aptidão
    pop_with_fitness = list(zip(range(len(population)), aptitudes))
    
    # 2. Ordena a população com base na aptidão (do menor para o maior)
    pop_with_fitness.sort(key=lambda item: item[1])
    
    # 3. Os ranks (1 para o pior, N para o melhor) serão usados como pesos
    ranks = list(range(1, len(population) + 1))
    
    # 4. A lógica da Roleta é aplicada sobre os ranks
    total_rank = sum(ranks)
    pick = random.uniform(0, total_rank)
    logger.debug(f"Rank total: {total_rank}, ponto selecionado: {pick:.2f}")
    
    current = 0
    for i in range(len(population)):
        rank = ranks[i]
        individual_index = pop_with_fitness[i][0]
        
        current += rank
        if current > pick:
            selected_fitness = aptitudes[individual_index]
            logger.debug(f"Selecionado com rank {rank}, fitness: {selected_fitness:.6f}")
            return population[individual_index]
            
    # Fallback
    last_index = pop_with_fitness[-1][0]
    logger.debug("Fallback: retornando melhor rankeado")
    return population[last_index]


class Selection:
    """Wrapper class that exposes selection functions as static methods.

    This preserves a class-based API if callers expect `Selection.method(...)`.
    """

    @staticmethod
    def tournament(population: List[Route], aptitudes: List[float], tournament_size: int) -> Route:
        return tournament_selection(population, aptitudes, tournament_size)

    @staticmethod
    def tournament_refined(population: List[Route], distances: List[float], tournament_size: int) -> Route:
        return tournament_selection_refined(population, distances, tournament_size)

    @staticmethod
    def roulette(population: List[Route], aptitudes: List[float]) -> Route:
        return roulette_wheel_selection(population, aptitudes)

    @staticmethod
    def rank(population: List[Route], aptitudes: List[float]) -> Route:
        return rank_selection(population, aptitudes)
