"""
llm_provider.py — Modular LLM Provider Architecture

Supports:
  - GroqProvider (Groq Cloud LPU via GROQ_API_KEY, endpoint https://api.groq.com/openai/v1)
  - GrokProvider (xAI API via XAI_API_KEY, endpoint https://api.x.ai/v1)
  - GeminiProvider (Google Gemini API via GEMINI_API_KEY)
  - OpenAIProvider (OpenAI / OpenRouter API via OPENAI_API_KEY or LLM_API_KEY)
  - FallbackProvider (Heuristic / Rule-based local fallback)
"""

import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Ensure backend .env is loaded regardless of process working directory
_backend_dir = Path(__file__).resolve().parent.parent
_backend_env = _backend_dir / ".env"
_root_env = _backend_dir.parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
if _root_env.exists():
    load_dotenv(_root_env)
load_dotenv()

logger = logging.getLogger(__name__)


def _sanitize_log_message(msg: str, keys_to_mask: list) -> str:
    """Ensure API keys are never leaked in log files or console output."""
    sanitized = str(msg)
    for k in keys_to_mask:
        if k and len(k) > 4:
            sanitized = sanitized.replace(k, f"{k[:4]}...[MASKED]")
    # Mask any Groq or xAI key patterns automatically
    sanitized = re.sub(r'gsk_[A-Za-z0-9_\-]+', 'gsk_...[MASKED]', sanitized)
    sanitized = re.sub(r'xai-[A-Za-z0-9_\-]+', 'xai-...[MASKED]', sanitized)
    sanitized = re.sub(r'AIza[A-Za-z0-9_\-]+', 'AIza...[MASKED]', sanitized)
    return sanitized


class BaseLLMProvider(ABC):
    """Abstract Base Class for all LLM providers."""

    @abstractmethod
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        """Execute chat completion and return raw text string or None on failure."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return provider metadata for status and health check."""
        pass


class GroqProvider(BaseLLMProvider):
    """
    Groq Cloud Provider using official OpenAI-compatible REST API.
    Official base URL: https://api.groq.com/openai/v1
    Chat completion endpoint: https://api.groq.com/openai/v1/chat/completions
    Verified available models include:
      - openai/gpt-oss-120b (default recommended)
      - openai/gpt-oss-20b
      - qwen/qwen3.8-27b
    """

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b", base_url: str = ""):
        self.api_key = (api_key or "").strip()
        self.model = model or "openai/gpt-oss-120b"
        self.base_url = (base_url or "https://api.groq.com/openai/v1").rstrip("/")

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        if not self.api_key:
            logger.warning("[GroqProvider] [CONFIG_ERROR] No API key configured. Bypassing Groq API call.")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": max(0.0, min(1.0, temperature)),
            "stream": False
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                status = res.status_code

                if status == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        logger.info(f"[GroqProvider] [SUCCESS] status=200 model={self.model} len={len(content)}")
                        return content
                    logger.warning(f"[GroqProvider] [EMPTY_CHOICES] status=200 model={self.model} but choices empty.")
                    return None

                # Categorized error diagnostics
                safe_err = _sanitize_log_message(res.text, [self.api_key])

                if status in (401, 403):
                    category = "AUTH_ERROR"
                    desc = "Authentication failed. Please verify GROQ_API_KEY in backend/.env."
                elif status == 404:
                    category = "MODEL_NOT_FOUND"
                    desc = f"Model '{self.model}' not found or not accessible on Groq."
                elif status == 400:
                    category = "BAD_REQUEST_OR_DECOMMISSIONED_MODEL"
                    desc = f"Bad request or decommissioned model '{self.model}'. Refer to https://console.groq.com/docs/deprecations."
                elif status == 429:
                    category = "RATE_LIMIT"
                    desc = "Groq rate limit or quota exceeded."
                elif status >= 500:
                    category = "SERVER_ERROR"
                    desc = f"Groq server error (HTTP {status})."
                else:
                    category = "API_ERROR"
                    desc = f"Groq API returned HTTP {status}."

                logger.warning(
                    f"[GroqProvider] [{category}] status={status} model={self.model} error={desc} details={safe_err[:200]}"
                )
                return None

        except httpx.TimeoutException:
            logger.warning(f"[GroqProvider] [TIMEOUT] model={self.model} request timed out after 30 seconds.")
            return None
        except httpx.NetworkError as ne:
            safe_err = _sanitize_log_message(str(ne), [self.api_key])
            logger.warning(f"[GroqProvider] [NETWORK_ERROR] model={self.model} network connection failed: {safe_err}")
            return None
        except Exception as e:
            safe_err = _sanitize_log_message(str(e), [self.api_key])
            logger.warning(f"[GroqProvider] [UNEXPECTED_ERROR] model={self.model} exception: {safe_err}")
            return None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "groq",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "mode": "live" if self.api_key else "fallback",
            "base_url": self.base_url
        }


class GrokProvider(BaseLLMProvider):
    """
    xAI Grok Provider using OpenAI-compatible REST API.
    Official base URL: https://api.x.ai/v1
    Chat completion endpoint: https://api.x.ai/v1/chat/completions
    """

    def __init__(self, api_key: str, model: str = "grok-2-latest", base_url: str = ""):
        self.api_key = (api_key or "").strip()
        self.model = model or "grok-2-latest"
        self.base_url = (base_url or "https://api.x.ai/v1").rstrip("/")

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        if not self.api_key:
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": max(0.0, min(1.0, temperature)),
            "stream": False
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    return None
                else:
                    safe_err = _sanitize_log_message(res.text, [self.api_key])
                    logger.warning(f"xAI Grok API error (HTTP {res.status_code}): {safe_err}")
                    return None
        except httpx.TimeoutException:
            logger.warning("xAI Grok API request timed out after 30 seconds.")
            return None
        except Exception as e:
            safe_err = _sanitize_log_message(str(e), [self.api_key])
            logger.warning(f"xAI Grok API request failed: {safe_err}")
            return None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "grok",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "mode": "live" if self.api_key else "fallback",
            "base_url": self.base_url
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider using standard REST endpoint."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", base_url: str = ""):
        self.api_key = (api_key or "").strip()
        self.model = model or "gemini-1.5-flash"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        if not self.api_key:
            return None

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        generation_config: Dict[str, Any] = {
            "temperature": max(0.0, min(1.0, temperature))
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        prompt_text = f"System Instructions:\n{system_prompt}\n\nUser Request:\n{user_prompt}"
        if json_mode:
            prompt_text += "\n\nRespond strictly with valid JSON."

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt_text}]
                }
            ],
            "generationConfig": generation_config
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return None
                else:
                    safe_err = _sanitize_log_message(res.text, [self.api_key])
                    logger.warning(f"Gemini API error (HTTP {res.status_code}): {safe_err}")
                    return None
        except Exception as e:
            safe_err = _sanitize_log_message(str(e), [self.api_key])
            logger.warning(f"Gemini API request failed: {safe_err}")
            return None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "mode": "live" if self.api_key else "fallback"
        }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI and OpenRouter compatible provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = ""):
        self.api_key = (api_key or "").strip()
        self.model = model or "gpt-4o-mini"
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        if not self.api_key:
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": max(0.0, min(1.0, temperature))
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    return None
                else:
                    safe_err = _sanitize_log_message(res.text, [self.api_key])
                    logger.warning(f"OpenAI API error (HTTP {res.status_code}): {safe_err}")
                    return None
        except Exception as e:
            safe_err = _sanitize_log_message(str(e), [self.api_key])
            logger.warning(f"OpenAI API request failed: {safe_err}")
            return None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "mode": "live" if self.api_key else "fallback"
        }


class FallbackProvider(BaseLLMProvider):
    """Deterministic local fallback provider used when no API keys are configured."""

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        json_mode: bool = True
    ) -> Optional[str]:
        return None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "fallback",
            "model": "local-rule-engine",
            "has_api_key": False,
            "mode": "local-fallback"
        }


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function to instantiate the active LLM provider based on environment variables.

    Priority & Resolution:
      1. Explicit LLM_PROVIDER ('groq' -> GroqProvider, 'grok'/'xai' -> GrokProvider, 'gemini'/'google' -> GeminiProvider, 'openai'/'openrouter' -> OpenAIProvider).
      2. If GROQ_API_KEY is present or key starts with 'gsk_' -> GroqProvider.
      3. If XAI_API_KEY is present (and not a gsk_ key) -> GrokProvider.
      4. If GEMINI_API_KEY or GOOGLE_API_KEY is present -> GeminiProvider.
      5. If OPENAI_API_KEY is present -> OpenAIProvider.
      6. Generic LLM_API_KEY prefix routing:
         - Starts with 'gsk_' -> GroqProvider
         - Starts with 'xai-' -> GrokProvider
         - Starts with 'AIza' -> GeminiProvider
         - Otherwise non-empty -> OpenAIProvider
      7. FallbackProvider (Zero crashes, zero errors when offline or unconfigured).
    """
    prov_env = os.getenv("LLM_PROVIDER", "").strip().lower()

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    xai_key = os.getenv("XAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    generic_key = os.getenv("LLM_API_KEY", "").strip()

    groq_model = os.getenv("GROQ_MODEL", "").strip() or os.getenv("LLM_MODEL", "").strip() or "openai/gpt-oss-120b"
    xai_model = os.getenv("XAI_MODEL", "").strip() or "grok-2-latest"
    gemini_model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-1.5-flash"
    openai_model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"

    groq_base = os.getenv("GROQ_BASE_URL", "").strip() or "https://api.groq.com/openai/v1"
    xai_base = os.getenv("XAI_BASE_URL", "").strip() or "https://api.x.ai/v1"
    openai_base = os.getenv("LLM_BASE_URL", "").strip()
    gemini_base = os.getenv("LLM_BASE_URL", "").strip()

    # Safety: detect if a Groq key (gsk_...) was accidentally placed in XAI_API_KEY
    if xai_key.startswith("gsk_") and not groq_key:
        groq_key = xai_key
        xai_key = ""

    # 1. Explicit LLM_PROVIDER specification
    if prov_env == "groq":
        key = groq_key or (generic_key if generic_key.startswith("gsk_") else generic_key)
        return GroqProvider(api_key=key, model=groq_model, base_url=groq_base)

    if prov_env in ["grok", "xai"]:
        key = xai_key or generic_key
        # Ensure we never send a Groq key to xAI
        if key.startswith("gsk_"):
            return GroqProvider(api_key=key, model=groq_model, base_url=groq_base)
        return GrokProvider(api_key=key, model=xai_model, base_url=xai_base)

    if prov_env in ["gemini", "google"]:
        key = gemini_key or generic_key
        return GeminiProvider(api_key=key, model=gemini_model, base_url=gemini_base)

    if prov_env in ["openai", "openrouter"]:
        key = openai_key or generic_key
        return OpenAIProvider(api_key=key, model=openai_model, base_url=openai_base)

    # 2. Automatic selection: Groq is primary when GROQ_API_KEY or gsk_ is present
    if groq_key or (generic_key and generic_key.startswith("gsk_")):
        key = groq_key or generic_key
        return GroqProvider(api_key=key, model=groq_model, base_url=groq_base)

    # 3. xAI fallback
    if xai_key and not xai_key.startswith("gsk_"):
        return GrokProvider(api_key=xai_key, model=xai_model, base_url=xai_base)

    # 4. Gemini fallback
    if gemini_key:
        return GeminiProvider(api_key=gemini_key, model=gemini_model, base_url=gemini_base)

    # 5. OpenAI fallback
    if openai_key:
        return OpenAIProvider(api_key=openai_key, model=openai_model, base_url=openai_base)

    # 6. Generic key detection
    if generic_key:
        if generic_key.startswith("gsk_"):
            return GroqProvider(api_key=generic_key, model=groq_model, base_url=groq_base)
        if generic_key.startswith("xai-"):
            return GrokProvider(api_key=generic_key, model=xai_model, base_url=xai_base)
        if generic_key.startswith("AIza"):
            return GeminiProvider(api_key=generic_key, model=gemini_model, base_url=gemini_base)
        return OpenAIProvider(api_key=generic_key, model=openai_model, base_url=openai_base)

    # 7. Local deterministic fallback
    return FallbackProvider()
