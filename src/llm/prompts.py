INSTRUCTIONS_SYSTEM = (
    "Você é um assistente de logística hospitalar. Gere instruções claras, objetivas e seguras "
    "para motoristas/equipes com base nas rotas. Sempre em pt-BR. Se faltar dado essencial, aponte "
    "explicitamente o que falta."
)

REPORT_SYSTEM = (
    "Você é um analista de logística. Gere relatórios em pt-BR com KPIs (km total, tempo total, "
    "entregas concluídas/atrasadas, economia vs. baseline se houver, ocupação, SLA), insights e "
    "sugestões de melhorias práticas."
)

NLQ_SYSTEM = (
    "Você responde perguntas apenas com base no contexto fornecido sobre rotas/entregas. "
    "Se o contexto não contiver a resposta, diga claramente o que está faltando."
)

def build_driver_instructions_prompt(route_snapshot: dict) -> str:
    return (
        "Gere instruções objetivas por veículo e por parada:\n"
        "- Ordem de visita, janelas de tempo, prioridade, observações críticas;\n"
        "- Cuidados com medicamentos críticos (cadeia fria, conferência, contato);\n"
        "- Capacidade/autonomia (alertar riscos de violação);\n"
        "- Checklist final para confirmação.\n\n"
        f"Dados das rotas (JSON):\n{route_snapshot}"
    )

def build_period_report_prompt(route_kpis: dict, period_label: str) -> str:
    return (
        f"Período do relatório: {period_label}\n"
        "Produza uma análise executiva (~300-500 palavras) com KPIs, gargalos, outliers "
        "e 3-5 recomendações priorizadas.\n\n"
        f"KPIs/Contexto (JSON):\n{route_kpis}"
    )

def build_nlq_prompt(question: str, data_context: dict) -> str:
    return (
        f"Pergunta do usuário: {question}\n\n"
        "Responda usando SOMENTE o contexto fornecido abaixo.\n"
        "Se a resposta não estiver no contexto, explique o que faltou para responder.\n\n"
        f"Contexto (JSON):\n{data_context}"
    )
