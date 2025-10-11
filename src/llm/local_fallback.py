# src/llm/local_fallback.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List

RECUSE_TEXT = "Fora do escopo logístico informado."

def _safe_get(d: Dict[str, Any], key: str, default=None):
    v = d.get(key, default)
    return v if v is not None else default

# ---------------- Instruções (local) ----------------
def generate_driver_instructions_local(route_snapshot: Dict[str, Any]) -> str:
    """
    Gera instruções em Markdown SEM usar LLM, apenas com base no snapshot.
    Espera chaves como: vehicle_id, checklist[], stops[], cautions[], summary (se existirem).
    Também tolera estruturas simples: stops = [ {order, coords, priority, time_window}, ... ]
    """
    vehicle_id = _safe_get(route_snapshot, "vehicle_id", "N/D")
    checklist = list(_safe_get(route_snapshot, "checklist", [])) or ["Documentos", "EPIs", "Conferência"]
    cautions = list(_safe_get(route_snapshot, "cautions", []))
    summary = _safe_get(route_snapshot, "summary")

    # Stops podem vir em chaves alternativas
    stops = list(_safe_get(route_snapshot, "stops", []))
    if not stops and "route" in route_snapshot:
        stops = list(route_snapshot["route"])
    if not stops and "paradas" in route_snapshot:
        stops = list(route_snapshot["paradas"])

    md: List[str] = []
    md += [
        "## Instruções por Veículo (Fallback Local)",
        f"- **Veículo**: {vehicle_id}",
        "",
        "### Checklist",
    ]
    if checklist:
        md += [f"- {item}" for item in checklist]
    else:
        md.append("- N/D")

    md += ["", "### Paradas (ordem planejada)"]
    if stops:
        for s in stops:
            order = s.get("order", "?")
            coords = s.get("coords") or s.get("location") or s.get("address") or "N/D"
            priority = s.get("priority", "N/D")
            tw = s.get("time_window") or s.get("janela") or s.get("eta") or "N/D"
            md.append(f"- #{order}: {coords}, prioridade={priority}, janela={tw}")
    else:
        md.append("- N/D")

    md += ["", "### Cuidados / Observações"]
    if cautions:
        md += [f"- {c}" for c in cautions]
    else:
        md.append("- N/D")

    md += ["", "### Resumo"]
    md.append(summary or "Gerado localmente a partir do snapshot. Revise janelas de tempo e prioridades.")

    return "\n".join(md)

# ---------------- Relatório (local) ----------------
def generate_period_report_local(route_kpis: Dict[str, Any], period_label: str) -> str:
    """
    Gera relatório em Markdown SEM usar LLM.
    Tenta ler totals (km, stops, time_min) ou calcula a partir de campos similares.
    """
    totals = _safe_get(route_kpis, "totals", {}) or {}
    km = totals.get("km")
    stops = totals.get("stops")
    time_min = totals.get("time_min")

    km = km if km is not None else _safe_get(route_kpis, "km", 0)
    stops = stops if stops is not None else _safe_get(route_kpis, "stops", 0)
    time_min = time_min if time_min is not None else _safe_get(route_kpis, "time_min", 0)

    notes = list(_safe_get(route_kpis, "notes", []))

    md: List[str] = []
    md += [
        "## Relatório Operacional (Fallback Local)",
        f"- **Período**: {period_label}",
        f"- **Total km**: {km}",
        f"- **Paradas**: {stops}",
        f"- **Tempo (min)**: {time_min}",
        "",
        "### Notas / Insights",
    ]
    if notes:
        md += [f"- {n}" for n in notes]
    else:
        if km:
            md.append(f"- Cobertura de {km} km no período.")
        if stops:
            md.append(f"- {stops} paradas executadas.")
        if time_min:
            md.append(f"- Tempo total estimado de {time_min} minutos.")
        if not (km or stops or time_min):
            md.append("- Sem dados suficientes para insights.")

    md += ["", "### Resumo Executivo"]
    resumo = (
        f"Período {period_label}: {stops or 0} parada(s), {km or 0} km e {time_min or 0} min. "
        "Dados consolidados localmente com base nos KPIs informados."
    )
    md.append(resumo)

    return "\n".join(md)

# ---------------- NLQ (local) ----------------
def answer_nlq_local(question: str, data_context: Dict[str, Any]) -> str:
    """
    Resposta determinística baseada no dicionário (sem LLM).
    Suporta:
      - "qual a primeira/última parada prioritária", "parada com maior prioridade", "alta prioridade"
      - "km", "paradas", "tempo", "sla"
      - genérico: lista chaves do contexto

    Estratégia p/ prioridade:
      1) Encontrar lista de paradas (stops|route|paradas).
      2) Normalizar prioridade: Alta > Média > Baixa.
      3) Escolher a(s) de maior prioridade; em empate, menor 'order'.
    """
    q = (question or "").lower()

    # localizar paradas
    stops = []
    for key in ("stops", "route", "paradas"):
        if isinstance(data_context.get(key), list):
            stops = data_context[key]
            break

    def pr_rank(p: Any) -> int:
        if p is None:
            return 0
        s = str(p).strip().lower()
        if s in ("alta", "high", "alta prioridade", "prioridade alta"):
            return 3
        if s in ("media", "média", "medium", "prioridade media", "prioridade média"):
            return 2
        if s in ("baixa", "low", "prioridade baixa"):
            return 1
        return 0

    def first_priority_stop(stops_list: list[dict]) -> dict | None:
        ranked = []
        for s in stops_list:
            rank = pr_rank(s.get("priority"))
            order = s.get("order", 10**9)
            ranked.append((rank, order, s))
        if not ranked:
            return None
        ranked.sort(key=lambda x: (-x[0], x[1]))  # maior rank, menor order
        top = ranked[0]
        return top[2] if top[0] > 0 else None

    def last_stop(stops_list: list[dict]) -> dict | None:
        if not stops_list:
            return None
        filtered = [s for s in stops_list if isinstance(s.get("order"), int)]
        if not filtered:
            return None
        filtered.sort(key=lambda s: s.get("order", -10**9))
        return filtered[-1]

    # intents de prioridade
    if any(kw in q for kw in (
        "primeira parada prioritária", "parada prioritária", "mais prioritária",
        "maior prioridade", "alta prioridade", "parada com maior prioridade",
        "primeira parada de alta", "primeira de alta"
    )):
        if not stops:
            return "Não encontrei lista de paradas no contexto para avaliar prioridade."
        best = first_priority_stop(stops)
        if not best:
            return "Nenhuma parada com prioridade definida foi encontrada no contexto."
        order = best.get("order", "N/D")
        coords = best.get("coords") or best.get("location") or best.get("address") or "N/D"
        prio = best.get("priority", "N/D")
        tw = best.get("time_window") or best.get("janela") or best.get("eta") or "N/D"
        return f"Primeira parada prioritária: ordem #{order}, prioridade={prio}, janela={tw}, coords={coords}"

    # intent: última parada
    if "última parada" in q or "ultima parada" in q or "last stop" in q:
        if not stops:
            return "Não encontrei lista de paradas no contexto."
        last = last_stop(stops)
        if not last:
            return "Não foi possível identificar a última parada."
        order = last.get("order", "N/D")
        coords = last.get("coords") or last.get("location") or last.get("address") or "N/D"
        prio = last.get("priority", "N/D")
        tw = last.get("time_window") or last.get("janela") or last.get("eta") or "N/D"
        return f"Última parada: ordem #{order}, prioridade={prio}, janela={tw}, coords={coords}"

    # intents numéricas simples
    def pick(*keys, default="N/D"):
        for k in keys:
            if k in data_context:
                return data_context[k]
            if "totals" in data_context and k in data_context["totals"]:
                return data_context["totals"][k]
        return default

    if "km" in q:
        v = pick("km", default="N/D")
        v = data_context.get("totals", {}).get("km", v)
        return f"Total de km no período (conforme contexto): {v}"

    if "parada" in q or "stop" in q:
        if stops:
            return f"Paradas no contexto: {stops}"
        v = pick("stops", default="N/D")
        v = data_context.get("totals", {}).get("stops", v)
        return f"Número de paradas (conforme contexto): {v}"

    if "tempo" in q or "min" in q:
        v = pick("time_min", default="N/D")
        v = data_context.get("totals", {}).get("time_min", v)
        return f"Tempo total (min) (conforme contexto): {v}"

    if "sla" in q:
        v = pick("SLA", "sla", default="N/D")
        return f"SLA informado no contexto: {v}"

    # fallback genérico
    keys = ", ".join(sorted(list(data_context.keys())))
    return f"Não encontrei um valor específico para sua pergunta. Chaves disponíveis no contexto: {keys or 'N/D'}"
