# DrawFunctions - Documentação da Classe de Renderização

## Visão Geral

A classe `DrawFunctions` é responsável por toda a renderização da interface gráfica do algoritmo genético TSP/VRP utilizando a biblioteca Pygame. A classe segue o princípio de responsabilidade única (SRP) com métodos modulares e bem definidos.

## Arquitetura

### Padrões Implementados
- **Single Responsibility Principle (SRP)**: Cada método tem uma responsabilidade específica
- **Modularização**: Interface dividida em seções independentes
- **Separação de Responsabilidades**: Lógica de negócio separada da renderização
- **Reutilização**: Métodos auxiliares podem ser reutilizados em diferentes contextos

### Estrutura da Interface

A interface é dividida em áreas principais:

1. **Painel de Controle (Esquerda)**: Configurações e controles do algoritmo
   - Seções de Setup, Priority Slider, Run, Operators, Crossover
   - Gráfico de Fitness History
   - **Legenda de Rotas VRP** (posicionada abaixo do gráfico de fitness)
   - **Resumo Estatístico VRP** (abaixo da legenda)
2. **Área do Mapa (Direita)**: Visualização das rotas e pontos de entrega (área livre para melhor visualização)

## Métodos Principais

### Interface do Usuário

#### `draw_interface(app: Any) -> None`
**Descrição**: Método orquestrador que desenha toda a interface do usuário de forma modular.

**Responsabilidades**:
- Coordena o desenho de todas as seções da interface
- Mantém consistência visual entre componentes
- Garante ordem correta de renderização

**Seções Renderizadas**:
- Setup (configuração de mapas e cidades)
- Priority Slider (controle de prioridade)
- Run (KPIs e barra de progresso)
- Operators (seleção e mutação)
- Crossover (algoritmos de cruzamento)
- Fitness History (gráfico de evolução)

#### Métodos de Seção (Modulares)

##### `_draw_setup_section(app: Any, x: int, w: int) -> None`
- **Propósito**: Renderiza controles de configuração inicial
- **Elementos**: Geração de mapas, reset, tipos de mapa, número de cidades
- **Estado**: Desabilita controles durante execução do algoritmo

##### `_draw_run_section(app: Any, x: int, w: int) -> None`
- **Propósito**: Exibe KPIs e progresso da execução
- **Elementos**: Grid 2x2 de indicadores, barra de progresso
- **Dados**: Cidades, população, geração atual, melhor distância

##### `_draw_operators_section(app: Any, x: int, w: int) -> None`
- **Propósito**: Controles de operadores genéticos
- **Elementos**: Toggle elitismo, seleção (roleta/torneio/ranking), mutação (swap/inverse/shuffle)
- **Interação**: Destaque visual para método selecionado

##### `_draw_crossover_section(app: Any, x: int, w: int) -> None`
- **Propósito**: Seleção de algoritmos de cruzamento e controles de execução
- **Elementos**: PMX, OX1, CX, K-Point, ERX, botões Run/Stop
- **Estado**: Cores dinâmicas baseadas no estado de execução

### Visualização de Mapas e Rotas

#### `draw_cities(app: Any) -> None`
**Descrição**: Renderiza pontos de entrega com prioridades visuais.

**Funcionalidades**:
- Círculos concêntricos para diferentes prioridades
- Numeração sequencial dos pontos
- Códigos de cores baseados na prioridade do produto

**Métodos Auxiliares**:
- `_get_city_style()`: Determina estilo visual baseado na prioridade
- `_draw_city_point()`: Renderiza ponto individual com estilo especificado

#### `draw_route(app: Any, chromosome: Any, color: Tuple[int, int, int], width: int) -> None`
**Descrição**: Desenha uma rota individual conectando pontos especificados.

**Flexibilidade**:
- Suporta diferentes tipos de input (cromossomo, lista de índices, lista de pontos)
- Normalização automática de dados de entrada
- Fechamento automático da rota (retorno ao ponto inicial)

**Métodos Auxiliares**:
- `_normalize_route_points()`: Converte diferentes formatos para lista de pontos
- `_draw_route_lines()`: Renderiza linhas conectando os pontos

### Visualização VRP (Vehicle Routing Problem)

#### `draw_routes_vrp(app: Any, routes: List[Any], deposito: Any, show_legend: bool) -> None`
**Descrição**: Renderiza solução completa do VRP com múltiplas rotas.

**Componentes**:
1. **Pontos de Entrega**: Círculos numerados na área do mapa
2. **Rotas**: Linhas coloridas conectando depósito aos pontos
3. **Depósito**: Quadrado amarelo destacado na área do mapa
4. **Legenda**: Lista de veículos com cores e distâncias (painel de controle, abaixo do gráfico de fitness)
5. **Resumo**: Estatísticas consolidadas (abaixo da legenda no painel de controle)

**Métodos Auxiliares**:
- `_draw_delivery_points()`: Renderiza todos os pontos de entrega
- `_draw_route_lines()`: Desenha rotas e coleta dados para legenda
- `_draw_route_legend()`: Cria legenda com cores e distâncias
- `draw_vrp_summary()`: Exibe estatísticas consolidadas

#### `draw_vrp_summary(app: Any, routes: List[Any], deposito: Any, ...) -> None`
**Descrição**: Exibe resumo estatístico das rotas VRP.

**Informações Exibidas**:
- Número total de rotas
- Distância/custo total
- Uso por tipo de veículo

**Métodos Auxiliares**:
- `_calculate_route_statistics()`: Computa estatísticas das rotas
- `_calculate_summary_box_layout()`: Define posicionamento do box
- `_render_summary_box_content()`: Renderiza conteúdo visual

### Gráficos e Visualizações

#### `draw_fitness_graph(app: Any) -> None`
**Descrição**: Renderiza gráfico de evolução do fitness ao longo das gerações.

**Características**:
- Duas linhas: fitness máximo (vermelho) e médio (verde)
- Escala automática baseada nos valores
- Tratamento de casos extremos (valores iguais, dados insuficientes)

#### `draw_priority_slider(app: Any) -> None`
**Descrição**: Renderiza controle deslizante para ajuste de prioridade.

**Elementos**:
- Barra horizontal
- Handle circular interativo
- Label com valor percentual

### Utilitários e Helpers

#### `_palette() -> List[Tuple[int, int, int]]`
**Descrição**: Retorna paleta de cores para diferenciação de rotas.

**Uso**: Cores distintas para até 10 rotas simultâneas.

#### `_route_distance(app: Any, r: Any, deposito: Any) -> float`
**Descrição**: Calcula distância total de uma rota incluindo retorno ao depósito.

**Algoritmo**: Distância euclidiana entre pontos consecutivos.

#### `_fleet_cost_map(app: Any) -> Dict[str, float]`
**Descrição**: Mapeia tipos de veículos para custos por quilômetro.

## Configuração e Layout

A classe utiliza `UILayout` para centralizar configurações de:
- Posições e dimensões de componentes
- Cores padronizadas
- Espaçamentos e margens

## Dependências

- **pygame**: Biblioteca de renderização gráfica
- **typing**: Type hints para melhor documentação
- **UILayout**: Configurações centralizadas de layout

## Padrões de Qualidade

### Code Quality
- **Type Hints**: Todos os métodos tipados
- **Docstrings**: Documentação clara de propósito e parâmetros
- **SRP Compliance**: Cada método com responsabilidade única
- **Cognitive Complexity**: Mantida abaixo de 15 por método

### Performance
- **Renderização Eficiente**: Desenhos diretos sem overhead
- **Reutilização**: Cálculos compartilhados entre métodos
- **Lazy Evaluation**: Verificações de pré-condições

### Manutenibilidade
- **Modularidade**: Seções independentes e reutilizáveis
- **Extensibilidade**: Fácil adição de novos componentes
- **Testabilidade**: Métodos pequenos e focados

## Exemplo de Uso

```python
# Renderização da interface completa
DrawFunctions.draw_interface(app)

# Desenho do mapa com rotas VRP
DrawFunctions.draw_routes_vrp(app, routes, depot, show_legend=True)

# Renderização de uma rota específica
DrawFunctions.draw_route(app, chromosome, color=RED, width=3)

# Desenho apenas das cidades
DrawFunctions.draw_cities(app)
```

## Extensões Futuras

- Suporte a mais tipos de visualização
- Animações de transição
- Zoom e pan no mapa
- Exportação de imagens
- Temas de cores customizáveis