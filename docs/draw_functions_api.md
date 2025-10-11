# DrawFunctions - API Reference

## Métodos Públicos

### Interface Principal

#### `draw(app: Any) -> None`
**Método shell principal para renderização completa da interface.**

- **Parâmetros:**
  - `app`: Instância da aplicação contendo screen e estados
- **Uso:** Chamado a cada frame do loop principal
- **Ordem:** Mapa → Interface de controle

---

#### `draw_interface(app: Any) -> None`
**Orquestrador modular da interface de usuário.**

- **Renderiza:**
  - Painel principal com título
  - Seção Setup (configurações)
  - Priority Slider (controle de prioridade)
  - Seção Run (KPIs e progresso)
  - Seção Operators (seleção e mutação)
  - Seção Crossover (algoritmos e controles)
  - Gráfico de Fitness History

---

### Visualização de Mapas

#### `draw_cities(app: Any) -> None`
**Renderiza pontos de entrega com prioridades visuais.**

- **Características:**
  - Círculos concêntricos para prioridades
  - Numeração sequencial
  - Códigos de cores dinâmicos
- **Dependências:** `_get_city_style()`, `_draw_city_point()`

---

#### `draw_route(app: Any, chromosome: Any, color: Tuple[int, int, int] = BLACK, width: int = 2) -> None`
**Desenha rota individual conectando pontos especificados.**

- **Parâmetros:**
  - `chromosome`: Rota (objeto, lista de índices, ou lista de pontos)
  - `color`: Cor RGB da linha (padrão: preto)
  - `width`: Espessura da linha em pixels (padrão: 2)
- **Flexibilidade:** Normalização automática de tipos de entrada
- **Dependências:** `_normalize_route_points()`, `_draw_route_lines()`

---

### Visualização VRP

#### `draw_routes_vrp(app: Any, routes: List[Any], deposito: Any, show_legend: bool = True) -> None`
**Renderiza solução completa VRP com múltiplas rotas.**

- **Parâmetros:**
  - `routes`: Lista de objetos Route
  - `deposito`: Ponto do depósito central
  - `show_legend`: Exibir legenda e resumo (padrão: True)
- **Componentes**: Pontos → Rotas → Depósito → Legenda (painel de controle) → Resumo
- **Layout**: Legenda posicionada abaixo do gráfico de fitness para liberar área do mapa
- **Dependências**: Todos os métodos auxiliares VRP

---

#### `draw_vrp_summary(app: Any, routes: List[Any], deposito: Any, usage: Dict[str, int] = None, left: int = None, top: int = None, width: int = None) -> None`
**Exibe resumo estatístico das rotas VRP.**

- **Parâmetros opcionais de posicionamento:**
  - `left`, `top`: Posição customizada
  - `width`: Largura customizada
  - `usage`: Dados de uso de veículos
- **Informações:** Rotas totais, distância/custo, uso por tipo
- **Dependências:** `_calculate_route_statistics()`, `_calculate_summary_box_layout()`, `_render_summary_box_content()`

---

### Gráficos e Controles

#### `draw_fitness_graph(app: Any) -> None`
**Renderiza gráfico de evolução do fitness.**

- **Linhas:**
  - Vermelha: Melhor fitness por geração
  - Verde: Fitness médio da população
- **Características:** Escala automática, tratamento de extremos
- **Dependências:** `app.fitness_history`, `app.mean_fitness_history`

---

#### `draw_priority_slider(app: Any) -> None`
**Renderiza controle deslizante de prioridade.**

- **Componentes:** Trilho + Handle + Label
- **Interação:** Visual apenas (lógica em event handlers)
- **Dependências:** `app.priority_percentage`, `app.buttons['priority_slider']`

---

#### `draw_depot(app: Any, deposito) -> None`
**Desenha depósito como quadrado amarelo destacado.**

- **Parâmetros:**
  - `deposito`: Objeto com coordenadas x, y
- **Visual:** Quadrado preto (12x12) com interior amarelo (8x8)

---

## Métodos Auxiliares (Privados)

### Seções da Interface

- `_draw_setup_section()`: Configurações de mapa e cidades
- `_draw_run_section()`: KPIs e barra de progresso  
- `_draw_operators_section()`: Controles de operadores genéticos
- `_draw_crossover_section()`: Algoritmos de cruzamento e controles

### Processamento de Rotas

- `_normalize_route_points()`: Converte entrada para lista de pontos
- `_draw_route_lines()`: Renderiza linhas de rota individual

### VRP Helpers

- `_draw_delivery_points()`: Círculos numerados dos pontos
- `_draw_route_lines()`: Rotas VRP + dados de legenda
- `_draw_route_legend()`: Legenda com cores e distâncias (largura dinâmica)
- `_draw_route_legend_fixed_width()`: Legenda com largura fixa para integração ao painel

### Cálculos e Layout

- `_calculate_route_statistics()`: Estatísticas de rotas VRP
- `_calculate_summary_box_layout()`: Posicionamento de resumo
- `_render_summary_box_content()`: Renderização de conteúdo

### Estilo e Visualização

- `_get_city_style()`: Determina estilo baseado em prioridade
- `_draw_city_point()`: Renderiza ponto individual com estilo

### Utilitários

- `_palette()`: Paleta de cores para rotas
- `_route_distance()`: Calcula distância total de rota
- `_fleet_cost_map()`: Mapeia tipos de veículos para custos
- `_draw_map_board()`: Fundo do mapa com grade

---

## Estados da Aplicação Requeridos

### Obrigatórios
- `app.screen`: Surface do pygame
- `app.delivery_points`: Lista de pontos de entrega
- `app.font`, `app.small_font`: Fontes para renderização

### Para Interface Completa
- `app.buttons`: Dicionário com retângulos de botões
- `app.running_algorithm`: Estado de execução
- `app.map_type`: Tipo de mapa selecionado
- `app.num_cities`: Número de cidades
- `app.priority_percentage`: Percentual de prioridade

### Para KPIs e Progresso
- `app.population_size`: Tamanho da população
- `app.current_generation`: Geração atual
- `app.max_generations`: Total de gerações
- `app.best_fitness`: Melhor fitness encontrado

### Para Operadores
- `app.elitism`: Estado do elitismo
- `app.selection_method`: Método de seleção
- `app.mutation_method`: Método de mutação
- `app.crossover_method`: Método de cruzamento

### Para Gráfico de Fitness
- `app.fitness_history`: Histórico de melhor fitness
- `app.mean_fitness_history`: Histórico de fitness médio

---

## Dependências Externas

### Pygame
```python
import pygame
# Funções utilizadas:
# - pygame.draw.rect(), circle(), line(), lines()
# - pygame.Rect()
# - font.render(), font.size()
```

### UILayout
```python
from src.functions.ui_layout import UILayout
# Configurações utilizadas:
# - UILayout.ControlPanel.*
# - UILayout.MapArea.*
# - UILayout.Colors.*
# - UILayout.get_color()
```

### Typing
```python
from typing import Any, Tuple, List, Dict
# Para type hints e documentação
```