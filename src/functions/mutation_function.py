    # === ETAPA 2: IMPLEMENTAÇÃO DOS OPERADORES DE MUTAÇÃO ===
import random
from route import Route

class Mutation:
    
    @staticmethod
    def mutacao_por_troca(route: Route) -> Route:
        """
        Troca a posição de duas cidades aleatórias na rota.
        """
        mutated_individual = route.delivery_points[:]
        idx1, idx2 = random.sample(range(len(mutated_individual)), 2)
        mutated_individual[idx1], mutated_individual[idx2] = mutated_individual[idx2], mutated_individual[idx1]
        return Route(mutated_individual)

    @staticmethod
    def mutacao_por_inversao(route: Route) -> Route:
        """
        Inverte uma subsequência aleatória da rota.
        """
        mutated_individual = route.delivery_points[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        sub_sequence = mutated_individual[start:end]
        sub_sequence.reverse()
        mutated_individual[start:end] = sub_sequence
        return Route(mutated_individual)

    @staticmethod
    def mutacao_por_embaralhamento(route: Route) -> Route:
        """
        Embaralha uma subsequência aleatória da rota.
        """
        mutated_individual = route.delivery_points[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        sub_sequence = mutated_individual[start:end]
        random.shuffle(sub_sequence)
        mutated_individual[start:end] = sub_sequence
        return Route(mutated_individual)