import os, json, argparse
from datetime import datetime
from ..llm.report_generator import LLMServices

def save_text(text: str, out_dir: str, prefix: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{prefix}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def main():
    ap = argparse.ArgumentParser(description="Geração de instruções/relatórios com LLM")
    ap.add_argument("--snapshot", help="Caminho p/ JSON com rotas/paradas/veículos")
    ap.add_argument("--kpis", help="Caminho p/ JSON com KPIs agregados")
    ap.add_argument("--period", default="Diário", help="Rótulo do período (Diário/Semanal)")
    ap.add_argument("--question", help="Pergunta em linguagem natural (NLQ)")
    ap.add_argument("--context", help="JSON com contexto de dados para NLQ")
    ap.add_argument("--outdir", default="out", help="Pasta de saída para os arquivos gerados")
    args = ap.parse_args()

    svc = LLMServices()

    if args.snapshot:
        data = json.load(open(args.snapshot, "r", encoding="utf-8"))
        instr = svc.generate_driver_instructions(data)
        p = save_text(instr, args.outdir, "instrucoes")
        print(f"Instruções salvas em: {p}")

    if args.kpis:
        kpis = json.load(open(args.kpis, "r", encoding="utf-8"))
        rep = svc.generate_period_report(kpis, args.period)
        p = save_text(rep, args.outdir, "relatorio")
        print(f"Relatório salvo em: {p}")

    if args.question and args.context:
        ctx = json.load(open(args.context, "r", encoding="utf-8"))
        ans = svc.answer_nlq(args.question, ctx)
        p = save_text(ans, args.outdir, "nlq_resposta")
        print(f"Resposta NLQ salva em: {p}")

if __name__ == "__main__":
    main()
