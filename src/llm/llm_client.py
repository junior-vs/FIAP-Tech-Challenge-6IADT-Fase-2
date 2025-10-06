# src/llm/llm_client.py
from __future__ import annotations
import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMClient:
    """
    Cliente Gemini com extração robusta (não usa response.text) e retry defensivo
    quando a resposta é bloqueada (finish_reason == 2).
    """
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        model_name = os.getenv("LLM_MODEL", "models/gemini-2.5-flash")
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        self.model_name = model_name

        if self.provider != "gemini":
            raise ValueError("Atualmente este cliente está configurado apenas para 'gemini'.")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("❌ Variável GEMINI_API_KEY não definida no .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    # -------------------- utilidades internas --------------------

    def _merge_messages(self, messages: List[ChatMessage]) -> str:
        system_parts = [m.content for m in messages if m.role == "system"]
        user_parts = [m.content for m in messages if m.role == "user"]

        merged_prompt = ""
        if system_parts:
            merged_prompt += "### INSTRUÇÕES DO SISTEMA\n" + "\n".join(system_parts) + "\n\n"
        if user_parts:
            merged_prompt += "### ENTRADA DO USUÁRIO\n" + "\n\n".join(user_parts)

        if not merged_prompt.strip():
            merged_prompt = "Gere um texto padrão: nenhuma entrada foi fornecida."
        return merged_prompt

    def _extract_text_safely(self, response) -> str:
        """
        NÃO usa response.text (pode lançar exceção se a resposta foi bloqueada).
        Lê apenas de candidates[*].content.parts[*].text.
        """
        texts = []
        finish_reason = None

        candidates = getattr(response, "candidates", []) or []
        for cand in candidates:
            finish_reason = getattr(cand, "finish_reason", finish_reason)
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for p in parts:
                t = getattr(p, "text", None)
                if t:
                    texts.append(t)

        if texts:
            return "\n".join(texts).strip()

        pf = getattr(response, "prompt_feedback", None)
        block_reason = getattr(pf, "block_reason", None) if pf else None

        return (
            "Não foi possível gerar conteúdo agora.\n"
            f"- finish_reason: {finish_reason}\n"
            f"- prompt_feedback.block_reason: {block_reason}\n"
            "Sugestões: reduza o tamanho do snapshot (menos paradas), remova termos ambíguos/sensiveis, "
            "e tente novamente. (O modelo pode ter bloqueado por segurança.)"
        )

    def _call_model(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
    ) -> str:
        resp = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": top_p,
                "top_k": top_k,
            },
            # sem safety_settings customizados — usar defaults do provedor
        )
        return self._extract_text_safely(resp)

    # -------------------- API pública --------------------

    def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        prompt = self._merge_messages(messages)

        # 1ª tentativa (normal)
        try:
            text = self._call_model(
                prompt=prompt,
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 1200),
                top_p=0.95,
                top_k=40,
            )
        except Exception as e:
            return f"[LLM] Falha na geração: {e}"

        # Retry “suave” se diagnóstico indicar bloqueio
        if "finish_reason: 2" in text:
            try:
                soft_prefix = (
                    "Se alguma parte desta solicitação puder violar políticas, responda apenas com "
                    "orientações logísticas neutras, sem mencionar temas sensíveis.\n\n"
                )
                text_retry = self._call_model(
                    prompt=soft_prefix + prompt,
                    temperature=0.1,
                    max_tokens=min(kwargs.get("max_tokens", 1200), 900),
                    top_p=0.9,
                    top_k=40,
                )
                return text_retry if text_retry and "finish_reason: 2" not in text_retry else text
            except Exception as e:
                return text + f"\n\n[Retry falhou: {e}]"

        return text
