import json, re
from typing import Any, Dict

def extract_json_from_markdown(md: str) -> Dict[str, Any]:
    m = re.search(r"```json\s*(.*?)\s*```", md, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        raise ValueError("Nenhum bloco ```json``` encontrado na resposta.")
    raw = m.group(1)
    return json.loads(raw)
