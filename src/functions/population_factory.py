"""
Population factory for genetic algorithm initialization.

This module provides utilities for creating initial populations of routes
following the Factory pattern and Single Responsibility Principle.
"""

import random
from typing import List
from route import Route
from delivery_point import DeliveryPoint
from app_logging import get_logger


class PopulationFactory:
    """
    Factory class for creating genetic algorithm populations.
    
    Handles the creation and initialization of route populations while
    maintaining immutability principles and providing logging capabilities.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_initial_population(self, delivery_points: List[DeliveryPoint], 
                                 population_size: int) -> List[Route]:
        """
        Cria população inicial de rotas de forma otimizada.
        
        Args:
            delivery_points: Lista de pontos de entrega
            population_size: Tamanho da população a criar
            
        Returns:
            Lista de rotas embaralhadas formando a população inicial
            
        Raises:
            ValueError: Se delivery_points estiver vazia ou population_size <= 0
        """
        if not delivery_points:
            raise ValueError("Lista de pontos de entrega não pode estar vazia")
        if population_size <= 0:
            raise ValueError("Tamanho da população deve ser maior que zero")
            
        self.logger.info(f"Inicializando população de tamanho {population_size}")
        
        # Usar tuple para imutabilidade da base
        base_points = tuple(delivery_points)
        population = []
        
        for _ in range(population_size):
            # Converter para lista, embaralhar e criar rota
            shuffled = list(base_points)
            random.shuffle(shuffled)
            population.append(Route(shuffled))
        
        self.logger.debug(f"População inicializada com {len(population)} rotas")
        return population
    
    @staticmethod
    def create_random_route(delivery_points: List[DeliveryPoint]) -> Route:
        """
        Cria uma única rota aleatória.
        
        Args:
            delivery_points: Lista de pontos de entrega
            
        Returns:
            Rota com pontos embaralhados aleatoriamente
            
        Raises:
            ValueError: Se delivery_points estiver vazia
        """
        if not delivery_points:
            raise ValueError("Lista de pontos de entrega não pode estar vazia")
            
        shuffled = list(delivery_points)
        random.shuffle(shuffled)
        return Route(shuffled)