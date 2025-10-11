# src/llm/llm_client.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import time
import json
import re
import uuid
import hashlib
from typing import List, Optional, Callable

from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv  # <- corrigido
import google.generativeai as genai

# Carrega .env automaticamente a partir da raiz do projeto
load_dotenv(find_dotenv(usecwd=True), override=True)

# ---------------------------- Tipos e utilitários ----------------------------

class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str

def _mask(text: str) -> str:
    """Mascaramento simples para logs (e-mails, CPF BR, sequências numéricas longas)."""
    if not text:
        return text
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "[CPF]", text)
    text = re.sub(r"\b\d{11,}\b", "[NUM]", text)
    return text

CACHE_DIR = os.getenv("LLM_CACHE_DIR", ".cache/llm")
os.makedirs(CACHE_DIR, exist_ok=True)

def _hash_prompt(messages: List[ChatMessage], model: str, temperature: float, max_tokens: int) -> str:
    payload = json.dumps(
        {
            "messages": [m.model_dump() for m in messages],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")

def _min_interval() -> float:
    return float(os.getenv("LLM_MIN_INTERVAL_SEC", "0.5"))

def _respect_rate_limit(last_ts: float) -> float:
    wait = (last_ts + _min_interval()) - time.time()
    if wait > 0:
        time.sleep(wait)
    return time.time()

def _normalize_model_name(name: str) -> str:
    """Remove prefixo 'models/' caso exista."""
    return name.split("/", 1)[1] if name.startswith("models/") else name

# -------- Guardrail anti-cívico (aplicado ao TEXTO DO USUÁRIO e seu JSON) --------

# Removemos "política" para evitar falso-positivos (ex.: "política de frete").
_CIVIC_DENYLIST = [
    r"\beleic(ão|ões|oes)\b",
    r"\bvoto(s)?\b",
    r"\bcampanh(a|as)\b",
    r"\bpartid(o|os|ária|árias)\b",
    r"\bgovern(o|ador|amental)\b",
    r"\bcongress(o|istas)?\b",
    r"\bparlament(a|ares)\b",
    r"\bdesinformação\b",
    r"\bfake\s*news\b",
]
_CIVIC_RE = re.compile("|".join(_CIVIC_DENYLIST), re.IGNORECASE | re.UNICODE)

def _is_civic_text(text: str) -> bool:
    return bool(_CIVIC_RE.search(text or ""))

def _guardrail_user_text_or_none(user_text: str) -> Optional[str]:
    """
    Se detectar termos cívicos no TEXTO DO USUÁRIO (inclui JSON passado pelo user),
    retorna recusa padronizada. Caso contrário, None.
    """
    if _is_civic_text(user_text):
        return "Fora do escopo logístico informado."
    return None

# ------------------------------- Cliente principal -------------------------------

class LLMClient:

    def __init__(self, logger: Optional[Callable[[str], None]] = print):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if self.provider != "gemini":
            raise ValueError("Atualmente este cliente está configurado apenas para 'gemini'.")

        # chave
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("❌ GOOGLE_API_KEY/GEMINI_API_KEY ausente no .env")
        genai.configure(api_key=api_key)

        # system instruction focada em logística operacional
        system_instruction = (
            "Você é um assistente de logística operacional. "
            "Gere conteúdo APENAS com orientações logísticas e formatação JSON quando solicitado. "
            "NÃO forneça conselhos médicos, não mencione pacientes nem dados pessoais. "
            "Não gere conteúdo cívico/eleitoral. "
            "Se o pedido escapar do domínio logístico, responda: 'Fora do escopo logístico informado.'. "
            "Respeite o contexto fornecido. Conteúdo neutro e operacional apenas."
        )

        # modelo desejado (sem prefixo 'models/')
        desired = _normalize_model_name(os.getenv("LLM_MODEL", "gemini-2.5-flash"))

        # inicialização do modelo com fallback priorizando modelos estáveis
        self._logger = logger or (lambda *_: None)
        try:
            self.model = genai.GenerativeModel(desired, system_instruction=system_instruction)
            self.model_name = desired
        except Exception as e:
            self._logger(f"[LLM] Modelo '{desired}' indisponível ({e}). Buscando fallback…")
            avail = []
            try:
                avail = [
                    _normalize_model_name(m.name)
                    for m in genai.list_models()
                    if "generateContent" in getattr(m, "supported_generation_methods", [])
                ]
            except Exception as _e:
                self._logger(f"[LLM] Falha ao listar modelos: {_e}")

            preferred_order = [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-2.0-flash-001",
                "gemini-2.0-flash-lite",
                "gemini-pro-latest",
                "gemini-flash-latest",
            ]
            stable_like = [m for m in avail if ("flash" in m or "pro" in m) and ("preview" not in m and "exp" not in m)]
            preview_like = [m for m in avail if m not in stable_like]

            fallback = None
            for name in preferred_order:
                if name in avail:
                    fallback = name
                    break
            if not fallback:
                fallback = stable_like[0] if stable_like else (preview_like[0] if preview_like else (avail[0] if avail else desired))

            self._logger(f"[LLM] Fallback selecionado: {fallback}")
            self.model = genai.GenerativeModel(fallback, system_instruction=system_instruction)
            self.model_name = fallback

        self._last_call_ts = 0.0
        self._logger(f"[LLM] Usando modelo: {self.model_name}")

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
            "Sugestões: reduza o tamanho do snapshot, remova termos sensíveis e tente novamente."
        )

    def _build_safety_settings(self):
        """
        Ativa safety_settings permissivo somente se LLM_SAFETY_OFF=1
        (lista de dicts para compatibilidade com versões do SDK).
        """
        if os.getenv("LLM_SAFETY_OFF") != "1":
            return None
        return [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
        ]

    def _call_model(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
    ) -> str:
        safety_settings = self._build_safety_settings()

        try:
            resp = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                },
                safety_settings=safety_settings,
            )
            return self._extract_text_safely(resp)

        except Exception as e:
            # Se o SDK bloquear por integridade cívica, não propaga o erro: devolve recusa neutra
            msg = str(e) or ""
            if "harm_category_civic_integrity" in msg.lower():
                return "Fora do escopo logístico informado."
            return f"[LLM] Falha na geração: {e}"

    # -------------------- API pública --------------------
    def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """
        Gera texto a partir de mensagens no estilo chat.
        Parâmetros opcionais (kwargs):
          - temperature (float)
          - max_tokens (int)
          - disable_cache (bool)  -> ignora cache mesmo que exista
          - strict (bool)         -> NÃO faz retry “suave” se houver bloqueio
        """
        corr_id = str(uuid.uuid4())[:8]

        # Guardrail aplicado SOMENTE ao texto do usuário (inclui JSON anexado pelo user)
        user_parts = [m.content for m in messages if m.role == "user"]
        user_text = "\n\n".join(user_parts)
        routed = _guardrail_user_text_or_none(user_text)
        if routed:
            self._logger(f"[LLM {corr_id}] Guardrail acionado (cívico).")
            return routed

        prompt = self._merge_messages(messages)
        temperature = kwargs.get("temperature", 0.2)
        max_tokens = kwargs.get("max_tokens", 1200)
        strict = bool(kwargs.get("strict", False))

        # cache
        disable_cache = kwargs.get("disable_cache", False) or os.getenv("LLM_DISABLE_CACHE") == "1"
        key = _hash_prompt(messages, self.model_name, temperature, max_tokens)
        cpath = _cache_path(key)
        if not disable_cache and os.path.exists(cpath):
            try:
                with open(cpath, "r", encoding="utf-8") as f:
                    cached_obj = json.load(f)
                self._logger(f"[LLM {corr_id}] HIT cache {cpath}")
                return cached_obj.get("text", "")
            except Exception:
                pass  # cache corrompido → ignora

        # rate-limit
        self._last_call_ts = _respect_rate_limit(self._last_call_ts)

        # log de prévia (mascarado)
        try:
            masked_preview = [{"role": m.role, "content": _mask(m.content)} for m in messages[:2]]
            self._logger(
                f"[LLM {corr_id}] Req model={self.model_name} temp={temperature} max={max_tokens} messages={len(messages)}"
            )
            self._logger(f"[LLM {corr_id}] Preview: {json.dumps(masked_preview, ensure_ascii=False)[:400]}...")
        except Exception:
            pass

        # 1ª tentativa
        text = self._call_model(prompt, temperature, max_tokens, top_p=0.95, top_k=40)

        # Retry “suave” APENAS se não for 'strict'
        if (not strict) and isinstance(text, str) and ("finish_reason: 2" in text.lower()):
            try:
                soft_prefix = (
                    "Se alguma parte desta solicitação puder violar políticas, responda apenas com "
                    "orientações logísticas neutras e conteúdo operacional. Evite qualquer tema sensível.\n\n"
                )
                text_retry = self._call_model(
                    prompt=soft_prefix + prompt,
                    temperature=min(temperature, 0.1),
                    max_tokens=min(max_tokens, 900),
                    top_p=0.9,
                    top_k=40,
                )
                if text_retry and "finish_reason: 2" not in (text_retry or "").lower():
                    text = text_retry
            except Exception as e:
                text = (text or "") + f"\n\n[Retry falhou: {e}]"

        # salvar cache
        try:
            if not disable_cache:
                with open(cpath, "w", encoding="utf-8") as f:
                    json.dump({"text": text, "corr_id": corr_id}, f, ensure_ascii=False, indent=2)
                self._logger(f"[LLM {corr_id}] OK len={len(text)} cached={cpath}")
            else:
                self._logger(f"[LLM {corr_id}] OK len={len(text)} (cache disabled)")
        except Exception:
            self._logger(f"[LLM {corr_id}] OK len={len(text)} (cache skip)")

        return text
