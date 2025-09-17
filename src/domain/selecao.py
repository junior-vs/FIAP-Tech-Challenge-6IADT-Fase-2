
from random import random
from typing import List

from src.rota import Rota


def tournament_selection(
    population: List[Rota],
    aptitudes: List[float],
    tournament_size: int
) -> Rota:
    """
    Seleciona uma Rota da população usando o método de seleção por torneio.
    """
    population_with_aptitude = list(zip(population, aptitudes))
    tournament = random.sample(population_with_aptitude, tournament_size)
    winner = min(tournament, key=lambda item: item[1])
    return winner[0]

def tournament_selection_refined(
    population: List[Rota],
    distances: List[float],
    tournament_size: int
) -> Rota:
    """
    Versão refinada da seleção por torneio.
    - Utiliza 'distances' para clareza (problema de minimização).
    - Trabalha com índices para eficiência de memória.
    - Adiciona uma verificação de robustez.
    """
    population_size = len(population)
    assert 1 <= tournament_size <= population_size, "O tamanho do torneio deve ser válido."

    # Seleciona 'tournament_size' índices aleatórios
    competitor_indices = random.sample(range(population_size), tournament_size)
    
    # Encontra o índice do vencedor (aquele com a menor distância)
    winner_index = min(competitor_indices, key=lambda index: distances[index])
    
    return population[winner_index]

def roulette_wheel_selection(
    population: List[Rota],
    aptitudes: List[float] # Aptidão aqui DEVE ser um valor a ser maximizado (e.g., 1/distancia)
) -> Rota:
    """
    Seleciona uma Rota da população usando o método da Roleta.
    A probabilidade de seleção é proporcional à aptidão.
    """
    total_fitness = sum(aptitudes)
    
    # Se todas as aptidões forem zero (caso extremo), retorna um indivíduo aleatório
    if total_fitness == 0:
        return random.choice(population)
        
    # Gera um ponto aleatório na "roleta"
    pick = random.uniform(0, total_fitness)
    
    current = 0
    for individual, fitness in zip(population, aptitudes):
        current += fitness
        if current > pick:
            return individual
            
    # Fallback para garantir que sempre retorne um indivíduo
    return population[-1]

def rank_selection(
    population: List[Rota],
    aptitudes: List[float] # Aptidão aqui DEVE ser um valor a ser maximizado
) -> Rota:
    """
    Seleciona uma Rota usando Seleção por Rank.
    Resolve o problema de "super-indivíduos" da roleta.
    """
    # 1. Emparelha cada indivíduo com sua aptidão
    pop_with_fitness = list(zip(range(len(population)), aptitudes))
    
    # 2. Ordena a população com base na aptidão (do menor para o maior)
    pop_with_fitness.sort(key=lambda item: item[1])
    
    # 3. Os ranks (1 para o pior, N para o melhor) serão usados como pesos
    ranks = list(range(1, len(population) + 1))
    
    # 4. A lógica da Roleta é aplicada sobre os ranks
    total_rank = sum(ranks)
    pick = random.uniform(0, total_rank)
    
    current = 0
    for i in range(len(population)):
        rank = ranks[i]
        individual_index = pop_with_fitness[i][0]
        
        current += rank
        if current > pick:
            return population[individual_index]
            
    # Fallback
    last_index = pop_with_fitness[-1][0]
    return population[last_index]