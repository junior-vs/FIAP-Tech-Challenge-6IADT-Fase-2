# src/tools/llm_cli.py
import argparse, json, os
from pathlib import Path
from ..llm.report_generator import LLMServices
from ..llm.utils import extract_json_from_markdown

def _save_txt(s, outdir, name):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    p = Path(outdir)/f"{name}.md"; p.write_text(s, encoding="utf-8"); return str(p)

def _save_json(d, outdir, name):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    p = Path(outdir)/f"{name}.json"; p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8"); return str(p)

def main():
    ap = argparse.ArgumentParser("LLM CLI")
    ap.add_argument("--plan", help="JSON do plano (instruções)")
    ap.add_argument("--kpis", help="JSON de KPIs (relatório/melhorias)")
    ap.add_argument("--period", choices=["diário","semanal","mensal"], default="diário")
    ap.add_argument("--improvements", action="store_true")
    ap.add_argument("--question", help="Pergunta NLQ")
    ap.add_argument("--context", help="JSON contexto para NLQ")
    ap.add_argument("--outdir", default="out")
    # NOVO:
    ap.add_argument("--strict", action="store_true", help="Sem retry/fallback; aceita apenas a saída direta do LLM")
    ap.add_argument("--nocache", action="store_true", help="Ignora cache de LLM (também desliga retry suave)")
    a = ap.parse_args()

    # controla cache via env só nesse processo
    prev = os.environ.get("LLM_DISABLE_CACHE")
    if a.nocache:
        os.environ["LLM_DISABLE_CACHE"] = "1"

    try:
        svc = LLMServices()

        if a.plan:
            plan = json.load(open(a.plan, "r", encoding="utf-8"))
            md = svc.generate_driver_instructions(plan, strict=a.strict, disable_cache=a.nocache)
            _save_txt(md, a.outdir, "driver_instructions")
            try: _save_json(extract_json_from_markdown(md), a.outdir, "driver_instructions")
            except Exception as e: print(f"[WARN] JSON: {e}")

        if a.kpis and not a.improvements:
            k = json.load(open(a.kpis, "r", encoding="utf-8"))
            md = svc.generate_period_report(k, a.period, strict=a.strict, disable_cache=a.nocache)
            _save_txt(md, a.outdir, "report")
            try: _save_json(extract_json_from_markdown(md), a.outdir, "report")
            except Exception as e: print(f"[WARN] JSON: {e}")

        if a.kpis and a.improvements:
            k = json.load(open(a.kpis, "r", encoding="utf-8"))
            md = svc.generate_improvement_suggestions(k, strict=a.strict, disable_cache=a.nocache)
            _save_txt(md, a.outdir, "improvements")
            try: _save_json(extract_json_from_markdown(md), a.outdir, "improvements")
            except Exception as e: print(f"[WARN] JSON: {e}")

        if a.question and a.context:
            ctx = json.load(open(a.context, "r", encoding="utf-8"))
            md = svc.generate_nlq_answer(a.question, ctx, strict=a.strict, disable_cache=a.nocache)
            _save_txt(md, a.outdir, "nlq")
            try: _save_json(extract_json_from_markdown(md), a.outdir, "nlq")
            except Exception as e: print(f"[WARN] JSON: {e}")

    finally:
        # restaura env
        if a.nocache:
            if prev is None: os.environ.pop("LLM_DISABLE_CACHE", None)
            else: os.environ["LLM_DISABLE_CACHE"] = prev

if __name__ == "__main__":
    main()
