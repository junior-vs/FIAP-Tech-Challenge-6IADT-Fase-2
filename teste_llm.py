import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("LLM_MODEL", "models/gemini-2.5-flash")  # já com 'models/' por padrão

print(f"🔑 GEMINI_API_KEY carregada? {'SIM' if api_key else 'NÃO'}")
print(f"🧠 Modelo: {model_name}")

genai.configure(api_key=api_key)

# ❗️Use o model_name direto, SEM adicionar 'models/' aqui.
model = genai.GenerativeModel(model_name)

resp = model.generate_content("Responda apenas 'ok' se você está funcionando corretamente.")
print("✅ Resposta do modelo:")
print(resp.text)
