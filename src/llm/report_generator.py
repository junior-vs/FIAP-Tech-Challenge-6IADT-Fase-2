# src/llm/report_generator.py
from __future__ import annotations

import os
import json
from typing import Dict, Any, List

from .llm_client import LLMClient, ChatMessage
from .prompts import (
    INSTRUCTIONS_SYSTEM,
    REPORT_SYSTEM,
    NLQ_SYSTEM,
    build_driver_instructions_prompt,
    build_period_report_prompt,
    build_nlq_prompt,
)
from .local_fallback import (
    generate_driver_instructions_local,
    generate_period_report_local,
    answer_nlq_local,
    RECUSE_TEXT as _RECUSE_TEXT,
)

# Utilitário simples para extrair o primeiro bloco JSON entre crases
_JSON_FENCE = "```json"
_FENCE = "```"

def extract_json_from_markdown(text: str) -> Any:
    if not text:
        return None
    try:
        if _JSON_FENCE in text:
            start = text.index(_JSON_FENCE) + len(_JSON_FENCE)
            end = text.index(_FENCE, start)
            return json.loads(text[start:end].strip())
        return json.loads(text)
    except Exception:
        return None

def _is_blocked_or_recused(text: str) -> bool:
    if not text:
        return True
    t = text.lower()
    if _RECUSE_TEXT.lower() in t:
        return True
    if "harm_category_civic_integrity" in t:
        return True
    if "[llm] falha na geração" in t:
        return True
    if "prompt_feedback.block_reason" in t:
        return True
    if "finish_reason: 2" in t:
        return True
    return False

class LLMServices:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

        # parâmetros conservadores por padrão
        self.temp_instr = float(os.getenv("LLM_TEMP_INSTR", "0.10"))
        self.max_tokens_instr = int(os.getenv("LLM_MAXTOK_INSTR", "700"))

        self.temp_report = float(os.getenv("LLM_TEMP_REPORT", "0.15"))
        self.max_tokens_report = int(os.getenv("LLM_MAXTOK_REPORT", "800"))

        self.temp_qa = float(os.getenv("LLM_TEMP_QA", "0.10"))
        self.max_tokens_qa = int(os.getenv("LLM_MAXTOK_QA", "500"))

        # modo sem cache e estrito (sem retry “suave”)
        self.disable_cache = os.getenv("LLM_DISABLE_CACHE", "1") == "1"
        self.strict = os.getenv("LLM_STRICT", "1") == "1"

    # ---------------- Instruções para motoristas ----------------
    def generate_driver_instructions(self, route_snapshot: Dict[str, Any]) -> str:
        messages = [
            ChatMessage(role="system", content=INSTRUCTIONS_SYSTEM),
            ChatMessage(role="user", content=build_driver_instructions_prompt(route_snapshot)),
        ]
        text = self.client.chat(
            messages,
            temperature=self.temp_instr,
            max_tokens=self.max_tokens_instr,
            disable_cache=self.disable_cache,
            strict=self.strict,
        )

        if _is_blocked_or_recused(text):
            return generate_driver_instructions_local(route_snapshot)

        data = extract_json_from_markdown(text)
        if isinstance(data, dict):
            vehicle_id = data.get("vehicle_id")
            checklist = data.get("checklist") or []
            stops = data.get("stops") or []
            cautions = data.get("cautions") or []
            summary = data.get("summary")

            md = [
                "## Instruções por Veículo",
                f"- **Veículo**: {vehicle_id or 'N/D'}",
                "",
                "### Checklist",
                *(((f"- {item}" for item in checklist)) if checklist else ["- N/D"]),
                "",
                "### Paradas (ordem planejada)",
            ]
            if stops:
                for s in stops:
                    md.append(f"- #{s.get('order','?')}: {s.get('coords')}, prioridade={s.get('priority')}, janela={s.get('time_window')}")
            else:
                md.append("- N/D")
            md += [
                "",
                "### Cuidados / Observações",
                *(((f"- {c}" for c in cautions)) if cautions else ["- N/D"]),
                "",
                "### Resumo",
                summary or "N/D",
            ]
            return "\n".join(md)

        return generate_driver_instructions_local(route_snapshot)

    # ---------------- Relatório periódico ----------------
    def generate_period_report(self, route_kpis: Dict[str, Any], period_label: str) -> str:
        messages = [
            ChatMessage(role="system", content=REPORT_SYSTEM),
            ChatMessage(role="user", content=build_period_report_prompt(route_kpis, period_label)),
        ]
        text = self.client.chat(
            messages,
            temperature=self.temp_report,
            max_tokens=self.max_tokens_report,
            disable_cache=self.disable_cache,
            strict=self.strict,
        )

        if _is_blocked_or_recused(text):
            return generate_period_report_local(route_kpis, period_label)

        data = extract_json_from_markdown(text)
        md: List[str] = []
        if isinstance(data, dict):
            period = data.get("period", period_label)
            totals = data.get("totals") or {}
            notes = data.get("notes") or []

            md += [
                "## Relatório Operacional",
                f"- **Período**: {period}",
                f"- **Total km**: {totals.get('km', 0)}",
                f"- **Paradas**: {totals.get('stops', 0)}",
                f"- **Tempo (min)**: {totals.get('time_min', 0)}",
                "",
                "### Notas / Insights",
            ]
            if notes:
                md += [f"- {n}" for n in notes]
            else:
                md.append("- N/D")

        md.append("")
        md.append("### Resumo Executivo")
        tail = text
        try:
            if _JSON_FENCE in text:
                start = text.index(_JSON_FENCE)
                end = text.index(_FENCE, start + len(_JSON_FENCE))
                tail = (text[:start] + text[end + len(_FENCE):]).strip()
        except Exception:
            pass
        md.append(tail or "N/D")

        if len([line for line in md if line.strip()]) <= 3:
            return generate_period_report_local(route_kpis, period_label)

        return "\n".join(md)

    # ---------------- Q&A (NATURAL LANGUAGE) ----------------
    def answer_natural_language(self, question: str, data_context: Dict[str, Any]) -> str:
        messages = [
            ChatMessage(role="system", content=NLQ_SYSTEM),
            ChatMessage(role="user", content=build_nlq_prompt(question, data_context)),
        ]
        text = self.client.chat(
            messages,
            temperature=self.temp_qa,
            max_tokens=self.max_tokens_qa,
            disable_cache=self.disable_cache,
            strict=self.strict,
        )

        # 1) bloqueio/recusa → fallback local
        if _is_blocked_or_recused(text):
            return answer_nlq_local(question, data_context)

        # 2) se o LLM devolveu JSON com {"answer": ""} ou vazio → fallback local
        parsed = None
        try:
            if "```json" in (text or ""):
                start = text.index("```json") + len("```json")
                end = text.index("```", start)
                parsed = json.loads(text[start:end].strip())
            else:
                parsed = json.loads(text)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            ans = str(parsed.get("answer", "") or "").strip()
            if not ans:
                return answer_nlq_local(question, data_context)

        # 3) caso normal
        return text or answer_nlq_local(question, data_context)
