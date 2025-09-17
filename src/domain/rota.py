from typing import List, Self
from src.cidade import Cidade
import random

class Rota:
    def __init__(self, cidades: List[Cidade]):
        self.cidades = cidades

    def distancia_total(self) -> float:
        total = 0.0
        for i in range(len(self.cidades)):
            cidade_a = self.cidades[i]
            cidade_b = self.cidades[(i + 1) % len(self.cidades)]  # volta ao início
            total += cidade_a.distancia_euclidean(cidade_b)
        return total

    def __repr__(self):
        return f"Rota({self.cidades})"

    # === ETAPA 2: IMPLEMENTAÇÃO DOS OPERADORES DE MUTAÇÃO ===

    def mutacao_por_troca(self) -> "Rota":
        """
        Troca a posição de duas cidades aleatórias na rota.
        """
        mutated_individual = self.cidades[:]
        idx1, idx2 = random.sample(range(len(mutated_individual)), 2)
        mutated_individual[idx1], mutated_individual[idx2] = mutated_individual[idx2], mutated_individual[idx1]
        return Rota(mutated_individual)

    def mutacao_por_inversao(self) -> "Rota":
        """
        Inverte uma subsequência aleatória da rota.
        """
        mutated_individual = self.cidades[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        sub_sequence = mutated_individual[start:end]
        sub_sequence.reverse()
        mutated_individual[start:end] = sub_sequence
        return Rota(mutated_individual)

    def mutacao_por_embaralhamento(self) -> "Rota":
        """
        Embaralha uma subsequência aleatória da rota.
        """
        mutated_individual = self.cidades[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        sub_sequence = mutated_individual[start:end]
        random.shuffle(sub_sequence)
        mutated_individual[start:end] = sub_sequence
        return Rota(mutated_individual)