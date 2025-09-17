import pygame
import random
import math

# --- 1. Representação dos Dados ---
# Cidades serão representadas como uma lista de tuplas (x, y)
# Vamos criar 20 cidades aleatórias para começar
NUM_CIDADES = 20
CIDADES = [(random.randint(50, 750), random.randint(50, 550)) for _ in range(NUM_CIDADES)]

# --- 2. Funções do Algoritmo ---

def calcular_distancia_total(percurso):
    """
    Calcula a distância total de um percurso.
    
    Argumentos:
    percurso (list): Uma lista de tuplas de cidades, na ordem do percurso.
    
    Retorna:
    float: A distância total do percurso.
    """
    distancia = 0
    for i in range(len(percurso) - 1):
        # A distância entre duas cidades é a raiz quadrada da soma dos quadrados da diferença de coordenadas
        distancia += math.sqrt((percurso[i][0] - percurso[i+1][0])**2 + (percurso[i][1] - percurso[i+1][1])**2)
    # Adiciona a distância de volta para a cidade inicial para fechar o ciclo
    distancia += math.sqrt((percurso[-1][0] - percurso[0][0])**2 + (percurso[-1][1] - percurso[0][1])**2)
    return distancia

def trocar_cidades(percurso):
    """
    Cria um novo percurso trocando a posição de duas cidades aleatórias.
    
    Argumentos:
    percurso (list): O percurso original.
    
    Retorna:
    list: O novo percurso com as cidades trocadas.
    """
    novo_percurso = list(percurso)
    # Escolhe duas posições aleatórias para trocar
    i, j = random.sample(range(len(percurso)), 2)
    novo_percurso[i], novo_percurso[j] = novo_percurso[j], novo_percurso[i]
    return novo_percurso

# --- 3. Visualização com Pygame e Algoritmo Principal ---

def main_loop():
    """
    Função principal que gerencia o loop do Pygame e o algoritmo Simulated Annealing.
    """
    pygame.init()
    LARGURA, ALTURA = 800, 600
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Simulated Annealing para o Problema do Caixeiro-Viajante")
    
    relogio = pygame.time.Clock()

    # Parâmetros do Simulated Annealing
    temperatura = 10000.0  # Temperatura inicial (alta)
    taxa_de_resfriamento = 0.9995  # Taxa de resfriamento (deve ser < 1)
    
    # Inicia com uma rota aleatória
    percurso_atual = list(CIDADES)
    random.shuffle(percurso_atual)
    
    melhor_percurso = list(percurso_atual)
    melhor_distancia = calcular_distancia_total(melhor_percurso)
    
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
        
        # --- Lógica do Simulated Annealing ---
        if temperatura > 0.01:
            # Gera um novo percurso
            novo_percurso = trocar_cidades(percurso_atual)
            
            # Calcula as distâncias
            distancia_atual = calcular_distancia_total(percurso_atual)
            nova_distancia = calcular_distancia_total(novo_percurso)
            
            # Calcula a diferença de energia (custo)
            delta_distancia = nova_distancia - distancia_atual
            
            # Se o novo percurso for melhor, aceite-o
            if delta_distancia < 0:
                percurso_atual = novo_percurso
                # Atualiza a melhor solução encontrada até agora
                if nova_distancia < melhor_distancia:
                    melhor_percurso = list(novo_percurso)
                    melhor_distancia = nova_distancia
            # Se o novo percurso for pior, aceite-o com uma certa probabilidade
            else:
                probabilidade_aceitacao = math.exp(-delta_distancia / temperatura)
                if random.random() < probabilidade_aceitacao:
                    percurso_atual = novo_percurso
            
            # Reduz a temperatura
            temperatura *= taxa_de_resfriamento
        
        # --- Desenha na tela ---
        tela.fill((0, 0, 0))  # Limpa a tela
        
        # Desenha o melhor percurso
        for i in range(len(melhor_percurso)):
            pygame.draw.circle(tela, (255, 255, 255), melhor_percurso[i], 5)
            # Desenha as linhas do percurso
            proximo_i = (i + 1) % len(melhor_percurso)
            pygame.draw.line(tela, (255, 0, 0), melhor_percurso[i], melhor_percurso[proximo_i], 2)
            
        # Desenha a distância na tela
        font = pygame.font.SysFont('Arial', 24)
        texto_distancia = font.render(f'Melhor Distância: {melhor_distancia:.2f}', True, (255, 255, 255))
        texto_temperatura = font.render(f'Temperatura: {temperatura:.2f}', True, (255, 255, 255))
        tela.blit(texto_distancia, (10, 10))
        tela.blit(texto_temperatura, (10, 40))
        
        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    
# Inicia o programa
if __name__ == "__main__":
    main_loop()