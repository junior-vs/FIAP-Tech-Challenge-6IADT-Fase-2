# === ETAPA 2: IMPLEMENTAÇÃO DOS OPERADORES DE MUTAÇÃO ===
import random
from route import Route
from app_logging import log_performance, get_logger

# Logger para este módulo
logger = get_logger(__name__)

class Mutation:
    
    @staticmethod
    @log_performance
    def mutacao_por_troca(route: Route) -> Route:
        """
        Troca a posição de duas cidades aleatórias na rota.
        """
        logger.debug(f"Mutação por troca: rota com {len(route.delivery_points)} cidades")
        mutated_individual = route.delivery_points[:]
        idx1, idx2 = random.sample(range(len(mutated_individual)), 2)
        logger.debug(f"Trocando posições {idx1} e {idx2}")
        mutated_individual[idx1], mutated_individual[idx2] = mutated_individual[idx2], mutated_individual[idx1]
        return Route(mutated_individual)

    @staticmethod
    @log_performance
    def mutacao_por_inversao(route: Route) -> Route:
        """
        Inverte uma subsequência aleatória da rota.
        """
        logger.debug(f"Mutação por inversão: rota com {len(route.delivery_points)} cidades")
        mutated_individual = route.delivery_points[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        logger.debug(f"Invertendo subsequência [{start}:{end}]")
        sub_sequence = mutated_individual[start:end]
        sub_sequence.reverse()
        mutated_individual[start:end] = sub_sequence
        return Route(mutated_individual)

    @staticmethod
    @log_performance
    def mutacao_por_embaralhamento(route: Route) -> Route:
        """
        Embaralha uma subsequência aleatória da rota.
        """
        logger.debug(f"Mutação por embaralhamento: rota com {len(route.delivery_points)} cidades")
        mutated_individual = route.delivery_points[:]
        start, end = sorted(random.sample(range(len(mutated_individual)), 2))
        logger.debug(f"Embaralhando subsequência [{start}:{end}]")
        sub_sequence = mutated_individual[start:end]
        random.shuffle(sub_sequence)
        mutated_individual[start:end] = sub_sequence
        return Route(mutated_individual)