# 🚚 FIAP Tech Challenge - Fase 2
## Otimização de Rotas de Entrega com Algoritmos Genéticos e IA

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green)](https://www.pygame.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-orange)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/tests-pytest-green)](https://pytest.org/)

> Sistema inteligente de otimização de rotas de entrega que combina **Algoritmos Genéticos** com **IA Generativa** para resolver o problema de roteamento de veículos (VRP - Vehicle Routing Problem).

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Algoritmos Genéticos](#-algoritmos-genéticos)
- [Integração com IA](#-integração-com-ia)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Equipe](#-equipe)

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como parte do **Tech Challenge da FIAP - Fase 2**, focando na otimização de rotas de entrega utilizando técnicas avançadas de computação evolutiva e inteligência artificial.

### Problema Abordado

O **Vehicle Routing Problem (VRP)** é um problema clássico de otimização combinatória que busca encontrar as melhores rotas para uma frota de veículos atender um conjunto de pontos de entrega, minimizando custos e respeitando diversas restrições:

- 📦 **Capacidade dos veículos**
- ⛽ **Autonomia/alcance**
- 🎯 **Prioridade de entregas**
- ⏰ **Janelas de tempo**
- 📐 **Dimensões físicas das cargas**

### Solução Proposta

Utilizamos **Algoritmos Genéticos** para explorar o espaço de soluções de forma eficiente, combinados com **Google Gemini AI** para gerar insights, relatórios e responder perguntas sobre as rotas otimizadas.

---

## ✨ Funcionalidades

### 🧬 Algoritmos Genéticos

- **Múltiplos operadores de cruzamento:**
  - PMX (Partially Mapped Crossover)
  - OX1 (Order Crossover)
  - CX (Cycle Crossover)
  - K-Point Crossover
  - ERX (Edge Recombination Crossover)

- **Operadores de mutação:**
  - Mutação por troca (swap)
  - Mutação por inversão
  - Mutação por embaralhamento

- **Métodos de seleção:**
  - Roleta (Roulette Wheel)
  - Torneio (Tournament)
  - Ranking

- **Elitismo configurável**
- **Função de fitness com restrições múltiplas**

### 🚛 Otimização de Frota (VRP)

- Suporte a múltiplos tipos de veículos
- Gestão de capacidade e autonomia
- Alocação inteligente de entregas por veículo
- Visualização de rotas por veículo

### 🤖 Integração com IA (Google Gemini)

- 📊 **Geração automática de relatórios** periódicos
- 🗺️ **Instruções para motoristas** com detalhamento de rotas
- 💬 **Perguntas em linguagem natural** sobre as rotas
- ✅ **Validação de outputs** com JSON Schema
- 💾 **Cache de respostas** para otimizar uso da API

### 🎨 Interface Visual

- Visualização em tempo real do algoritmo genético
- Mapa interativo para criação de pontos customizados
- Gráfico de evolução do fitness
- Painel de controle intuitivo
- Sistema de layout centralizado e responsivo

---

## 🛠️ Tecnologias

### Core
- **Python 3.8+** - Linguagem principal
- **NumPy 2.3.3** - Computação numérica
- **SciPy 1.16.2** - Algoritmos científicos

### Interface
- **Pygame 2.6.1** - Interface gráfica e visualização

### IA e Validação
- **Google Generative AI 0.7.0+** - Integração com Gemini
- **Pydantic 2.8.0+** - Validação de dados e schemas
- **python-dotenv 1.0.1+** - Gerenciamento de variáveis de ambiente

### Desenvolvimento
- **pytest 8.4.2** - Framework de testes
- **colorama 0.4.6** - Colorização de logs
- **Pygments 2.19.2** - Syntax highlighting

---

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Conta Google Cloud (para uso da API Gemini)

### Passo a Passo

1. **Clone o repositório:**
```powershell
git clone https://github.com/junior-vs/FIAP-Tech-Challenge-6IADT-Fase-2.git
cd FIAP-Tech-Challenge-6IADT-Fase-2
```

2. **Instale as dependências:**
```powershell
python -m pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**

Crie um arquivo `.env` na raiz do projeto:
```env
# API Google Gemini
GOOGLE_API_KEY=sua_chave_aqui

# Configurações LLM (opcionais)
LLM_MODEL=gemini-2.0-flash-exp
LLM_MAX_STOPS=6
LLM_STRICT=0
LLM_DISABLE_CACHE=0
LLM_CACHE_DIR=.cache/llm
```

---

## 🚀 Uso

### Iniciar a Aplicação

```powershell
python src/main/TSPGeneticAlgorithm.py
```

### Interface Principal

![Interface do Sistema](docs/screenshot_interface.png)

#### Controles do Algoritmo

| Ação | Atalho/Botão | Descrição |
|------|--------------|-----------|
| Gerar Mapa | `Generate Map` | Cria pontos de entrega |
| Iniciar Algoritmo | `Run Algorithm` / `SPACE` | Inicia a otimização |
| Parar Algoritmo | `Stop Algorithm` / `ESC` | Interrompe a execução |
| Resetar | `Reset` | Limpa todos os dados |
| Perguntar à IA | `Q` | Faz pergunta em linguagem natural |
| Gerar Relatório | `R` | Gera relatório e instruções |

#### Tipos de Mapa

- **Random:** Pontos distribuídos aleatoriamente
- **Circle:** Pontos em formato circular
- **Custom:** Clique no mapa para adicionar pontos manualmente

#### Configurações

- **Número de Cidades:** Use `+` / `-` para ajustar (3-50)
- **Porcentagem de Prioridade:** Slider para controlar produtos prioritários
- **Método de Seleção:** Roleta / Torneio / Ranking
- **Método de Crossover:** PMX / OX1 / CX / K-Point / ERX
- **Método de Mutação:** Swap / Inversão / Embaralhamento
- **Elitismo:** Ativar/Desativar preservação do melhor indivíduo

### Usando a IA

#### 1. Gerar Relatório e Instruções (Tecla `R`)

```
[OK] Relatório salvo em: out/relatorio_20251014_143052.md
[OK] Instruções salvas em: out/instrucoes_20251014_143052.md
```

Os arquivos gerados incluem:
- 📊 **Relatório:** Métricas, análise de desempenho, recomendações
- 🗺️ **Instruções:** Roteiro detalhado para cada motorista

#### 2. Fazer Perguntas (Tecla `Q`)

```
Digite sua pergunta sobre a rota: Qual a melhor sequência de entregas?

==== RESPOSTA DA IA ====
A melhor sequência baseada na otimização atual é...
[Resposta detalhada da IA]
=========================
```

---

## 🧬 Algoritmos Genéticos

### Representação do Cromossomo

Cada **cromossomo** representa uma rota completa como uma permutação de pontos de entrega:

```
Cromossomo: [P3, P1, P5, P2, P4]
           └─ Ordem de visita dos pontos
```

### Função de Fitness

A função de fitness considera múltiplos fatores:

```python
fitness = base_fitness * priority_bonus * constraint_penalty

Onde:
- base_fitness: 1 / (distância_total + 1)
- priority_bonus: multiplicador baseado em entregas prioritárias
- constraint_penalty: penaliza violações de restrições
```

### Processo Evolutivo

1. **Inicialização:** População aleatória de N rotas
2. **Avaliação:** Cálculo do fitness de cada rota
3. **Seleção:** Escolha dos pais usando método configurado
4. **Crossover:** Geração de filhos combinando pais
5. **Mutação:** Pequenas alterações aleatórias
6. **Elitismo:** Preservação do melhor indivíduo (opcional)
7. **Repetição:** Volta ao passo 2 até atingir critério de parada

### Operadores Implementados

#### Crossover PMX (Partially Mapped Crossover)
```
Pai1:  [1, 2, | 3, 4, 5 |, 6, 7]
Pai2:  [4, 5, | 1, 2, 7 |, 3, 6]
       --------+---------+--------
Filho: [6, 2, | 3, 4, 5 |, 1, 7]
```

#### Mutação por Troca (Swap)
```
Antes: [1, 2, 3, 4, 5, 6]
              ↓     ↓
Depois:[1, 2, 5, 4, 3, 6]
```

---

## 🤖 Integração com IA

### Arquitetura LLM

```python
# src/llm/llm_client.py - Cliente base
# src/llm/prompts.py - Templates de prompts
# src/llm/report_generator.py - Serviços de alto nível
# src/llm/utils.py - Utilitários
# src/llm/local_fallback.py - Fallback local
```

### Schemas JSON

Todos os outputs da IA são validados contra schemas JSON:

```
schemas/llm_outputs/
├── driver_instructions.schema.json  # Instruções para motoristas
├── improvements.schema.json         # Sugestões de melhoria
├── nlq.schema.json                 # Respostas a perguntas
└── report.schema.json              # Relatórios periódicos
```

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── test_crossover_functions.py           # Testes de crossover
├── test_delivery_point_product_integration.py  # Integração domínio
├── test_product_constraints.py           # Validação de restrições
└── test_route_and_operators.py          # Operadores genéticos

tests_llm/
└── test_json_extraction_and_schema.py   # Validação LLM outputs
```

### Executar Testes

```powershell
# Todos os testes
pytest -v

# Testes específicos
pytest tests/test_crossover_functions.py -v

# Testes LLM
pytest tests_llm/ -v

# Com cobertura
pytest --cov=src tests/
```

---

## 📁 Estrutura do Projeto

```
FIAP-Tech-Challenge-6IADT-Fase-2/
│
├── src/
│   ├── domain/              # Modelos de domínio
│   │   ├── delivery_point.py
│   │   ├── product.py
│   │   ├── route.py
│   │   └── vehicle.py
│   │
│   ├── functions/           # Funções auxiliares
│   │   ├── app_logging.py
│   │   ├── crossover_function.py
│   │   ├── draw_functions.py
│   │   ├── fitness_function.py
│   │   ├── mutation_function.py
│   │   ├── selection_functions.py
│   │   └── ui_layout.py    # 🎯 Layout centralizado
│   │
│   ├── llm/                # Integração IA
│   │   ├── llm_client.py
│   │   ├── local_fallback.py
│   │   ├── prompts.py
│   │   ├── report_generator.py
│   │   └── utils.py
│   │
│   └── main/
│       ├── TSPGeneticAlgorithm.py  # Aplicação principal
│       └── logs/           # Logs de execução
│
├── schemas/
│   └── llm_outputs/        # JSON Schemas para validação
│
├── tests/                  # Testes unitários
├── tests_llm/             # Testes LLM
├── config/                # Configurações
│
├── requirements.txt       # Dependências Python
├── .env.example          # Exemplo de configuração
└── README.md             # Este arquivo
```

---

## 👥 Equipe

**FIAP Tech Challenge - Grupo 6IADT**

- 👤 **Alana Caroline de Oliveira da Luz**
- 👤 **Catherine Cruz Porto**
- 👤 **Etianne Torres Chan**
- 👤 **Renan Augusto Alves da Costa**
- 👤 **Valdir de Souza Junior**

> Projeto desenvolvido para o curso de Pós-Graduação em Inteligência Artificial para Devs da FIAP

---

<div align="center">

**Feito com ❤️ para o FIAP Tech Challenge**

[⬆ Voltar ao topo](#-fiap-tech-challenge---fase-2)

</div>
