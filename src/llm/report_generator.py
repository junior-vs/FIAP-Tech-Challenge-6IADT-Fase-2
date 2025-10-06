# src/llm/report_generator.py
from __future__ import annotations
from typing import Dict, Any, List
import json
import math
from .llm_client import LLMClient, ChatMessage

# ==========================
# Configuração de segurança
# ==========================
SAFE_SYSTEM = (
    "Você é um assistente de logística hospitalar. "
    "Siga rigorosamente as políticas de segurança: não gere conteúdo sexual, violento, de ódio, perigoso ou fora do escopo. "
    "Escreva de modo neutro, técnico e operacional. "
    "Não invente dados; se algo não estiver no snapshot, informe o que falta e proponha como capturar esses dados futuramente. "
    "Evite qualquer linguagem que possa ser considerada sensível, mantendo foco apenas em rotas, procedimentos, EPIs, conferência e segurança operacional."
)

# Prefixo extra para o retry “suavizado”
SAFE_PREFIX = (
    "Responda apenas com orientações logísticas neutras, operacionais e não sensíveis. "
    "Se algum dado não existir no snapshot, apenas aponte a ausência de forma objetiva. "
    "Evite quaisquer temas sensíveis.\n\n"
)

# ======================================================
# Sanitização/compactação do snapshot para enviar ao LLM
# ======================================================

def _compact_snapshot(snapshot: Dict[str, Any], max_stops: int = 12) -> Dict[str, Any]:
    """
    Reduz o snapshot para um conjunto essencial e seguro. Limita número de paradas (max_stops)
    e remove dados supérfluos.
    """
    out = {
        "date": snapshot.get("date"),
        "map_type": snapshot.get("map_type"),
        "num_cities": snapshot.get("num_cities"),
        "best_fitness": snapshot.get("best_fitness"),
        "constraints": snapshot.get("constraints", {}),
        "notes": snapshot.get("notes", ""),
        "stops": [],
    }

    for stop in (snapshot.get("stops") or [])[:max_stops]:
        sanitized = {
            "order": stop.get("order"),
            "coords": stop.get("coords"),
            "address": stop.get("address"),
            "priority": stop.get("priority", "Média"),
            "time_window": stop.get("time_window", "08:00-18:00"),
            "notes": (stop.get("notes") or "")[:140],  # evita textos longos
        }
        # itens: só metadados logísticos básicos
        items = []
        for it in stop.get("items") or []:
            items.append(
                {
                    "name": it.get("name"),
                    "weight_g": it.get("weight_g"),
                    "dimensions_cm": it.get("dimensions_cm"),
                }
            )
        if items:
            sanitized["items"] = items
        out["stops"].append(sanitized)

    return out


def _compact_even_more(snapshot: Dict[str, Any], max_stops: int = 6) -> Dict[str, Any]:
    """
    Versão ainda mais compacta para o retry (quando houver bloqueio).
    Remove 'notes' e mantém o mínimo necessário.
    """
    out = {
        "date": snapshot.get("date"),
        "map_type": snapshot.get("map_type"),
        "num_cities": snapshot.get("num_cities"),
        "best_fitness": snapshot.get("best_fitness"),
        "constraints": snapshot.get("constraints", {}),
        "stops": [],
    }

    for stop in (snapshot.get("stops") or [])[:max_stops]:
        sanitized = {
            "order": stop.get("order"),
            "coords": stop.get("coords"),
            "address": stop.get("address"),
            "priority": stop.get("priority", "Média"),
            "time_window": stop.get("time_window", "08:00-18:00"),
        }
        items = []
        for it in stop.get("items") or []:
            items.append(
                {
                    "name": it.get("name"),
                    "weight_g": it.get("weight_g"),
                }
            )
        if items:
            sanitized["items"] = items
        out["stops"].append(sanitized)

    return out


def _is_block_message(text: str) -> bool:
    """
    Heurística: nosso LLMClient devolve uma mensagem diagnóstica contendo 'finish_reason: 2'
    quando houve bloqueio. Basta detectar essa substring.
    """
    if not text:
        return True
    t = text.lower()
    return ("finish_reason: 2" in t) or ("não foi possível gerar conteúdo agora" in t)


# ================================================
# Fallback local (não depende do LLM nem da rede)
# ================================================

PIXELS_PER_KM = 50.0     # fator de conversão simples (depende do seu mapa)
VELOCITY_KMH  = 35.0     # velocidade média urbana estimada

def _calc_path_distance(stops: List[Dict[str, Any]]) -> float:
    """Soma distância euclidiana entre paradas na ordem do array (em unidades de tela/pixels)."""
    if not stops or len(stops) < 2:
        return 0.0
    total = 0.0
    for i in range(len(stops) - 1):
        a = stops[i].get("coords") or {}
        b = stops[i + 1].get("coords") or {}
        ax, ay = a.get("x"), a.get("y")
        bx, by = b.get("x"), b.get("y")
        if ax is None or ay is None or bx is None or by is None:
            continue
        total += math.hypot(bx - ax, by - ay)
    return total


def _local_report(snapshot: Dict[str, Any], period_label: str) -> str:
    """Gera um relatório local simples e neutro, usando apenas os dados do snapshot."""
    stops = snapshot.get("stops") or []
    total_dist_px = _calc_path_distance(stops)
    dist_km = total_dist_px / PIXELS_PER_KM if PIXELS_PER_KM > 0 else 0.0
    est_hours = dist_km / VELOCITY_KMH if VELOCITY_KMH > 0 else 0.0

    lines = [
        f"# Relatório {period_label}",
        f"**Paradas (contadas)**: {len(stops)}",
        f"**Distância estimada (km)**: {dist_km:.1f}",
        f"**Tempo estimado (h)**: {est_hours:.2f} (a {VELOCITY_KMH:.0f} km/h)",
        "",
        "## Observações e Gargalos",
        "- Ajustar janelas de tempo para reduzir espera;",
        "- Consolidar paradas próximas para diminuir deslocamentos;",
        "- Avaliar priorização (Crítica/Alta/Média/Baixa) conforme SLA;",
        "",
        "## Próximos Passos",
        "- Padronizar coleta de dados (janela/contato/observações);",
        "- Reprocessar rota com limites operacionais (capacidade/tempo).",
    ]
    return "\n".join(lines)


# ======================================
# Serviços de alto nível consumidos pelo app
# ======================================

class LLMServices:
    def __init__(self):
        self.client = LLMClient()

    # ---------------------- Geração de Instruções ----------------------

    def generate_driver_instructions(self, snapshot: Dict[str, Any]) -> str:
        # 1) Compacta
        clean = _compact_snapshot(snapshot, max_stops=12)

        # 1a) Se não houver paradas, retorna template local
        if not clean.get("stops"):
            return (
                "# Checklist de Saída (Template)\n"
                "- Documentos da rota e contatos úteis\n"
                "- EPIs: luvas, colete, máscara quando aplicável\n"
                "- Acondicionamento: volumes acomodados e fixados\n"
                "- Conferência: quantidade de volumes, integridade, lacres\n"
                "- Equipamentos: smartphone carregado, caneta, prancheta, etiquetas\n\n"
                "# Instruções Operacionais (Template)\n"
                "Não há paradas no snapshot enviado.\n"
                "Inclua pelo menos: ordem, endereço/coord., janela de tempo, prioridade e itens (nome/peso/dimensões).\n"
            )

        # 2) Prompt principal
        user = (
            "Gere **instruções operacionais passo a passo** para motoristas/equipe de entrega, "
            "com base no snapshot de rotas abaixo. Foque em: \n"
            "- checklist de saída (documentos, EPIs, acondicionamento, conferência);\n"
            "- sequência das paradas com instruções objetivas (chegada, conferência, cautelas, assinatura);\n"
            "- recomendações de segurança e boas práticas (linguagem neutra, sem temas sensíveis);\n"
            "- plano de contingência para atrasos/ocorrências comuns.\n\n"
            f"Snapshot (JSON):\n```json\n{json.dumps(clean, ensure_ascii=False, indent=2)}\n```"
        )

        # 3) Chama o LLM (passo normal)
        text = self.client.chat(
            [
                ChatMessage(role="system", content=SAFE_SYSTEM),
                ChatMessage(role="user", content=user),
            ],
            temperature=0.2,
            max_tokens=1100,
        )

        # 4) Se bloqueou, faz retry “suave” com snapshot ainda menor
        if _is_block_message(text):
            compact = _compact_even_more(snapshot, max_stops=6)
            user_retry = (
                SAFE_PREFIX
                + "Gere instruções logísticas objetivas e neutras no formato de tópicos curtos.\n\n"
                f"Snapshot (compacto):\n```json\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n```"
            )
            text_retry = self.client.chat(
                [
                    ChatMessage(role="system", content=SAFE_SYSTEM),
                    ChatMessage(role="user", content=user_retry),
                ],
                temperature=0.1,
                max_tokens=900,
            )
            return text_retry

        return text

    # ---------------------- Geração de Relatório ----------------------

    def generate_period_report(self, context: Dict[str, Any], period_label: str = "Diário") -> str:
        """
        Gera relatório usando o LLM. Caso bloqueie, tenta um retry “suave”.
        Se ainda assim bloquear, gera um relatório local (fallback) e prefixa a data de operação.
        """
        snapshot = context.get("snapshot", {}) or {}
        operation_date = context.get("operation_date") or snapshot.get("date")
        clean = _compact_snapshot(snapshot, max_stops=12)

        # Se não houver paradas, reporte local direto
        if not clean.get("stops"):
            base = _local_report(clean, period_label)
            if operation_date:
                base = f"Instruções:\n*   **Data de Operação:** {operation_date}\n\n" + base
            return base

        user = (
            f"Elabore um **relatório {period_label.lower()}** de eficiência de rotas (neutro, técnico), contendo:\n"
            "- resumo do período (entregas realizadas, ocorrências), sem temas sensíveis;\n"
            "- métricas estimadas: distância total, tempo, economia potencial (declare suposições de forma objetiva);\n"
            "- gargalos observados e **sugestões de melhoria** (processo, priorização, janelas de tempo, consolidação de cargas);\n"
            "- próximos passos recomendados.\n\n"
            f"Snapshot (JSON):\n```json\n{json.dumps(clean, ensure_ascii=False, indent=2)}\n```"
        )

        text = self.client.chat(
            [
                ChatMessage(role="system", content=SAFE_SYSTEM),
                ChatMessage(role="user", content=user),
            ],
            temperature=0.25,
            max_tokens=1100,
        )

        if _is_block_message(text):
            compact = _compact_even_more(snapshot, max_stops=6)
            user_retry = (
                SAFE_PREFIX
                + f"Produza um relatório {period_label.lower()} enxuto, com tópicos, totalmente neutro e operacional.\n\n"
                f"Snapshot (compacto):\n```json\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n```"
            )
            text_retry = self.client.chat(
                [
                    ChatMessage(role="system", content=SAFE_SYSTEM),
                    ChatMessage(role="user", content=user_retry),
                ],
                temperature=0.1,
                max_tokens=900,
            )
            # Se o retry também veio bloqueado, usa fallback local
            if _is_block_message(text_retry):
                base = _local_report(clean, period_label)
                if operation_date:
                    base = f"Instruções:\n*   **Data de Operação:** {operation_date}\n\n" + base
                return base
            else:
                if operation_date:
                    text_retry = f"Instruções:\n*   **Data de Operação:** {operation_date}\n\n" + text_retry
                return text_retry

        # Caso o texto principal não tenha sido bloqueado
        if operation_date:
            text = f"Instruções:\n*   **Data de Operação:** {operation_date}\n\n" + text
        return text

    # ---------------------- Perguntas em Linguagem Natural ----------------------

    def answer_natural_language(self, question: str, snapshot: Dict[str, Any]) -> str:
        clean = _compact_snapshot(snapshot, max_stops=12)

        if not clean.get("stops"):
            return (
                "Snapshot sem paradas. Informe: ordem, endereço/coordenadas, janela de tempo, "
                "prioridade e itens (nome/peso). Com esses dados posso responder perguntas específicas sobre a rota."
            )

        user = (
            "Responda à pergunta abaixo **de forma neutra e objetiva** com base no snapshot de rotas. "
            "Se a informação não existir no snapshot, diga o que falta e proponha como coletar no futuro.\n\n"
            f"Pergunta: {question}\n\n"
            f"Snapshot (JSON):\n```json\n{json.dumps(clean, ensure_ascii=False, indent=2)}\n```"
        )

        text = self.client.chat(
            [
                ChatMessage(role="system", content=SAFE_SYSTEM),
                ChatMessage(role="user", content=user),
            ],
            temperature=0.2,
            max_tokens=900,
        )

        if _is_block_message(text):
            compact = _compact_even_more(snapshot, max_stops=6)
            user_retry = (
                SAFE_PREFIX
                + "Responda de modo curto e 100% operacional. "
                "Se algo não existir no snapshot, apenas diga o que falta.\n\n"
                f"Snapshot (compacto):\n```json\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n```"
            )
            text_retry = self.client.chat(
                [
                    ChatMessage(role="system", content=SAFE_SYSTEM),
                    ChatMessage(role="user", content=user_retry),
                ],
                temperature=0.1,
                max_tokens=700,
            )
            return text_retry

        return text
