"""
test_groq_live_smoke.py — Live API Smoke Test for Groq Cloud Provider

NOTE: This is a REAL live network API test against Groq Cloud LPU.
It reads GROQ_API_KEY from backend/.env (or environment variables).
It validates live credentials, model availability, and chat completion,
without printing the secret API key.
"""

import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend .env is loaded
backend_dir = Path(__file__).resolve().parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
load_dotenv()

sys.path.insert(0, str(backend_dir))

from services.llm_provider import GroqProvider, get_llm_provider


class TestGroqLiveSmoke:
    """Real live network smoke test for Groq Provider."""

    def test_live_groq_chat_completion(self):
        """Execute a minimal live chat completion against https://api.groq.com/openai/v1."""
        groq_key = os.getenv("GROQ_API_KEY", "").strip() or os.getenv("XAI_API_KEY", "").strip()
        if not groq_key:
            pytest.skip("GROQ_API_KEY not configured in backend/.env — skipping live API test.")

        # Ensure key is a valid Groq key format
        assert groq_key.startswith("gsk_"), (
            f"Expected Groq key prefix 'gsk_', but got '{groq_key[:4]}...'. Verify GROQ_API_KEY in backend/.env."
        )

        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        provider = GroqProvider(api_key=groq_key, model=model)

        info = provider.get_info()
        assert info["provider"] == "groq"
        assert info["has_api_key"] is True
        assert info["mode"] == "live"
        assert "gsk_" not in str(info)  # Key never leaked in info dict

        system_prompt = "You are a concise technical assistant. Respond in one sentence."
        user_prompt = "What is the time complexity of quicksort in the average case?"

        result = provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            json_mode=False
        )

        # Validate that live response was received
        assert result is not None, (
            f"Groq API returned None for model '{model}'. Check backend logs for HTTP status and error category."
        )
        assert len(result.strip()) > 5, "Groq response was empty or too short."
        assert groq_key not in result, "Security check failed: API key leaked in response body."

        # Average case quicksort should mention log n, O(n log n), or Theta(n log n)
        res_norm = result.lower().replace("\u202f", " ").replace("\u00a0", " ")
        has_complexity = "log" in res_norm and "n" in res_norm
        assert has_complexity, (
            f"Expected average case complexity (n log n) in response. Got: {result[:200]}"
        )
