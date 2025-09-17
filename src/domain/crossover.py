from ast import Tuple
from random import random
from typing import Optional
from src.rota import Rota

# === ETAPA 1: IMPLEMENTAÇÃO DOS OPERADORES DE CROSSOVER ===

def order_crossover(parent1: Rota, parent2: Rota) -> Rota:
    """
    Realiza o cruzamento Order Crossover (OX) para criar um filho.
    """
    size = len(parent1.cidades)
    start_index, end_index = sorted(random.sample(range(size), 2))
    child_segment = parent1.cidades[start_index:end_index]
    remaining_genes = [gene for gene in parent2.cidades if gene not in child_segment]
    child = [None] * size
    child[start_index:end_index] = child_segment
    fill_index = 0
    for i in range(size):
        if child[i] is None:
            child[i] = remaining_genes[fill_index]
            fill_index += 1
    return Rota(child)

def erx_crossover(parent1: Rota, parent2: Rota) -> Rota:
    """
    Realiza o cruzamento Edge Recombination Crossover (ERX) para criar um filho.
    O ERX constrói um mapa de vizinhança (arestas) a partir dos dois pais e gera o filho priorizando cidades com menos vizinhos disponíveis.

    Parâmetros:
    - parent1: Rota representando o primeiro pai.
    - parent2: Rota representando o segundo pai.

    Retorna:
    - Rota: filho gerado pelo ERX.
    """
    def build_edge_map(parent1: Rota, parent2: Rota) -> dict[int, set[int]]:
        edge_map = {i: set() for i in range(len(parent1.cidades))}
        for parent in [parent1, parent2]:
            for i in range(len(parent.cidades)):
                left = (i - 1) % len(parent.cidades)
                right = (i + 1) % len(parent.cidades)
                edge_map[i].update([left, right])
        return edge_map

    def select_next(current: int, edge_map: dict[int, set[int]], visited: list[int]) -> Optional[int]:
        for neighbor in edge_map[current]:
            edge_map[neighbor].discard(current)
        del edge_map[current]
        candidates = [(node, len(edge_map[node])) for node in edge_map if node not in visited and current in edge_map[node]]
        if not candidates:
            candidates = [(node, len(edge_map[node])) for node in edge_map if node not in visited]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    edge_map = build_edge_map(parent1, parent2)
    current = random.randint(0, len(parent1.cidades) - 1)
    visited = [current]

    while len(visited) < len(parent1.cidades):
        next_city = select_next(current, edge_map, visited)
        if next_city is None:
            remaining = [i for i in range(len(parent1.cidades)) if i not in visited]
            next_city = random.choice(remaining)
        visited.append(next_city)
        current = next_city

    child_cidades = [parent1.cidades[i] for i in visited]
    return Rota(child_cidades)





def crossover_ordenado_ox1(parent1: Rota, parent2: Rota) -> Tuple[Rota, Rota]:
    """
    Implementa o Crossover Ordenado (OX1).
    Preserva uma subsequência de um pai e preenche o resto com genes do outro.
    """
    size = len(parent1)
    child1, child2 = [None] * size, [None] * size

    # 1. Seleciona uma subsequência aleatória do pai 1
    start, end = sorted(random.sample(range(size), 2))
    
    # 2. Copia a subsequência para os filhos
    child1[start:end] = parent1[start:end]
    child2[start:end] = parent2[start:end]
    
    # 3. Preenche os genes restantes para o filho 1
    parent2_genes = [item for item in parent2 if item not in child1]
    idx = 0
    for i in range(size):
        if child1[i] is None:
            child1[i] = parent2_genes[idx]
            idx += 1
            
    # 4. Preenche os genes restantes para o filho 2
    parent1_genes = [item for item in parent1 if item not in child2]
    idx = 0
    for i in range(size):
        if child2[i] is None:
            child2[i] = parent1_genes[idx]
            idx += 1
            
    return child1, child2

def crossover_parcialmente_mapeado_pmx(parent1: Rota, parent2: Rota) -> Tuple[Rota, Rota]:
    """
    Implementa o Crossover Parcialmente Mapeado (PMX).
    Preserva a ordem e a posição absoluta de uma subsequência.
    """
    size = len(parent1)
    child1, child2 = list(parent1), list(parent2)
    
    # 1. Seleciona uma subsequência e cria os mapeamentos
    start, end = sorted(random.sample(range(size), 2))
    
    # Mapeamento e troca
    for i in range(start, end):
        gene1 = parent1[i]
        gene2 = parent2[i]
        
        # Troca os genes nos filhos
        child1[i], child2[i] = gene2, gene1
    
    # Corrigir duplicatas fora da seção de crossover
    def repair_child(child, mapping_parent):
        for i in range(size):
            if not (start <= i < end):
                while child[i] in child[start:end]:
                    # Encontra o gene mapeado
                    index_in_parent = mapping_parent.index(child[i])
                    child[i] = child[index_in_parent]
        return child

    # Mapeamentos são baseados na seção original dos pais
    mapping_parent1_section = parent1[start:end]
    mapping_parent2_section = parent2[start:end]
    
    # Reparo de Child1 (que recebeu seção do P2) usando mapeamento do P1
    repaired_child1 = [None] * size
    repaired_child1[start:end] = parent2[start:end]
    
    for i in list(range(start)) + list(range(end, size)):
        gene_to_add = parent1[i]
        while gene_to_add in repaired_child1[start:end]:
            idx = parent2[start:end].index(gene_to_add)
            gene_to_add = parent1[start:end][idx]
        repaired_child1[i] = gene_to_add
        
    # Reparo de Child2 (que recebeu seção do P1) usando mapeamento do P2
    repaired_child2 = [None] * size
    repaired_child2[start:end] = parent1[start:end]
    
    for i in list(range(start)) + list(range(end, size)):
        gene_to_add = parent2[i]
        while gene_to_add in repaired_child2[start:end]:
            idx = parent1[start:end].index(gene_to_add)
            gene_to_add = parent2[start:end][idx]
        repaired_child2[i] = gene_to_add
            
    return repaired_child1, repaired_child2

def crossover_de_ciclo_cx(parent1: Rota, parent2: Rota) -> Tuple[Rota, Rota]:
    """
    Implementa o Crossover de Ciclo (CX).
    Preserva a posição absoluta do máximo de genes possível de cada pai.
    """
    size = len(parent1)
    child1, child2 = [None] * size, [None] * size
    
    cycles = []
    visited_indices = [False] * size
    for i in range(size):
        if not visited_indices[i]:
            cycle = []
            start_index = i
            current_index = i
            while start_index != current_index or not cycle:
                cycle.append(current_index)
                visited_indices[current_index] = True
                gene_value = parent2[current_index]
                current_index = parent1.index(gene_value)
            cycles.append(cycle)

    for i, cycle in enumerate(cycles):
        for index_in_cycle in cycle:
            if i % 2 == 0:  # Ciclos pares (ou o primeiro) pegam do Pai 1 para Filho 1
                child1[index_in_cycle] = parent1[index_in_cycle]
                child2[index_in_cycle] = parent2[index_in_cycle]
            else:  # Ciclos ímpares pegam do Pai 2 para Filho 1
                child1[index_in_cycle] = parent2[index_in_cycle]
                child2[index_in_cycle] = parent1[index_in_cycle]
                
    return child1, child2

# NOVO OPERADOR ADICIONADO
def crossover_multiplos_pontos_kpoint(parent1: Rota, parent2: Rota, k: int = 2) -> Tuple[Rota, Rota]:
    """
    Implementa uma versão do K-Point Crossover adaptada para permutações,
    baseada na lógica do Crossover Ordenado (OX).
    """
    size = len(parent1)
    assert 1 <= k < size, "O número de pontos de corte 'k' deve ser pelo menos 1 e menor que o tamanho da rota."

    child1, child2 = [None] * size, [None] * size
    
    # 1. Seleciona 'k' pontos de corte únicos e os ordena
    points = sorted(random.sample(range(1, size), k))
    
    # Adiciona 0 e 'size' para facilitar a iteração por segmentos
    all_points = [0] + points + [size]
    
    # 2. Copia segmentos alternados de cada pai para os filhos
    for i in range(len(all_points) - 1):
        start, end = all_points[i], all_points[i+1]
        if i % 2 == 0:
            # Segmento par: Pai 1 -> Filho 1, Pai 2 -> Filho 2
            child1[start:end] = parent1[start:end]
            child2[start:end] = parent2[start:end]

    # 3. Preenche os genes restantes (slots 'None')
    def fill_gaps(child, other_parent):
        other_parent_genes = [gene for gene in other_parent if gene not in child]
        gene_idx = 0
        for i in range(size):
            if child[i] is None:
                child[i] = other_parent_genes[gene_idx]
                gene_idx += 1
        return child

    child1 = fill_gaps(child1, parent2)
    child2 = fill_gaps(child2, parent1)
    
    return Rota(child1), Rota(child2)

