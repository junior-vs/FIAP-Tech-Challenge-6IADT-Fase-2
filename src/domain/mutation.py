    # === ETAPA 2: IMPLEMENTAÇÃO DOS OPERADORES DE MUTAÇÃO ===
import random
from src.rota import Rota


def mutacao_por_troca(rota: Rota) -> Rota:
    """
    Troca a posição de duas cidades aleatórias na rota.
    """
    mutated_individual = rota.cidades[:]
    idx1, idx2 = random.sample(range(len(mutated_individual)), 2)
    mutated_individual[idx1], mutated_individual[idx2] = mutated_individual[idx2], mutated_individual[idx1]
    return Rota(mutated_individual)

def mutacao_por_inversao(rota: Rota) -> Rota:
    """
    Inverte uma subsequência aleatória da rota.
    """
    mutated_individual = rota.cidades[:]
    start, end = sorted(random.sample(range(len(mutated_individual)), 2))
    sub_sequence = mutated_individual[start:end]
    sub_sequence.reverse()
    mutated_individual[start:end] = sub_sequence
    return Rota(mutated_individual)

def mutacao_por_embaralhamento(rota: Rota) -> Rota:
    """
    Embaralha uma subsequência aleatória da rota.
    """
    mutated_individual = rota.cidades[:]
    start, end = sorted(random.sample(range(len(mutated_individual)), 2))
    sub_sequence = mutated_individual[start:end]
    random.shuffle(sub_sequence)
    mutated_individual[start:end] = sub_sequence
    return Rota(mutated_individual)