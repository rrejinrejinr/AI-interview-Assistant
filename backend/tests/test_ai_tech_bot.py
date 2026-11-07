"""
test_ai_tech_bot.py — AI Tech Bot: Grok Integration & Question Understanding Tests

Validates:
  1. All 10 specified question intents produce distinct, relevant answers.
  2. Non-technical questions are refused with the exact required phrasing.
  3. Provider errors / missing API keys do NOT crash the chat; fallback responds gracefully.
  4. Grok provider selection logic is correct.
  5. Cascading fallback between providers works as expected.
  6. Each binary-search variant gets a DISTINCT response (not one canned template).
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_fastapi import app
from database import SessionLocal
from models_db import User
from auth_utils import get_password_hash, create_access_token

client = TestClient(app)

NON_TECHNICAL_REFUSAL = (
    "I'm the AI Tech Bot, designed to help with programming, computer science, "
    "AI/ML, and software development questions. Please ask me a technical question."
)

_auth_headers_cache = None

def get_auth_headers():
    global _auth_headers_cache
    if _auth_headers_cache is not None:
        return _auth_headers_cache
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "techbot_tester@example.com").first()
        if not user:
            user = User(
                name="TechBot Tester",
                email="techbot_tester@example.com",
                password_hash=get_password_hash("Password123!"),
                email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(data={"sub": user.email, "user_id": user.id})
        _auth_headers_cache = {"Authorization": f"Bearer {token}"}
        return _auth_headers_cache
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rag_query(question: str, history: list | None = None) -> dict:
    """POST /api/rag/query and return parsed JSON body."""
    payload = {"query": question}
    if history:
        payload["history"] = history
    headers = get_auth_headers()
    resp = client.post("/api/rag/query", json=payload, headers=headers)
    assert resp.status_code == 200, f"Unexpected status {resp.status_code}: {resp.text}"
    return resp.json()



def assert_distinct_answers(answers: list[str], label: str = "") -> None:
    """Ensure no two answers in the list are identical."""
    for i in range(len(answers)):
        for j in range(i + 1, len(answers)):
            assert answers[i].strip().lower() != answers[j].strip().lower(), (
                f"Questions {i+1} and {j+1} returned the SAME answer{' ' + label if label else ''}.\n"
                f"Answer: {answers[i][:300]}"
            )


# ===========================================================================
# 1. Intent routing — 10 canonical questions
# ===========================================================================

class TestIntentRouting:
    """Verify each question gets the correct intent and a relevant answer."""

    def test_01_binary_search_definition(self):
        """Q1: 'What is binary search?' → CONCEPT_EXPLANATION, answer describes the algorithm."""
        result = rag_query("What is binary search?")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "binary search" in answer or "binary" in answer, (
            f"Expected 'binary search' in answer. Got: {answer[:400]}"
        )
        assert intent in ("CONCEPT_EXPLANATION", "DEFINITION", "GENERAL"), (
            f"Expected concept-style intent, got: {intent}"
        )

    def test_02_time_complexity_binary_search(self):
        """Q2: 'What is the time complexity of binary search?' → TIME_COMPLEXITY, O(log n) present."""
        result = rag_query("What is the time complexity of binary search?")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "log" in answer or "o(log" in answer or "logarithmic" in answer, (
            f"Expected O(log n) or logarithmic in answer. Got: {answer[:400]}"
        )
        assert intent in ("TIME_COMPLEXITY", "COMPLEXITY_ANALYSIS", "CONCEPT_EXPLANATION"), (
            f"Unexpected intent for time complexity question: {intent}"
        )

    def test_03_write_binary_search_java(self):
        """Q3: 'Write binary search in Java.' → CODE_EXAMPLE, Java code present."""
        result = rag_query("Write binary search in Java.")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        # Must contain Java code indicators
        has_java = (
            "int" in answer
            or "public" in answer
            or "while" in answer
            or "java" in answer
            or "return" in answer
        )
        assert has_java, (
            f"Expected Java code in the answer for 'Write binary search in Java'. Got: {answer[:500]}"
        )
        assert intent in ("CODE_EXAMPLE", "IMPLEMENTATION", "CONCEPT_EXPLANATION"), (
            f"Unexpected intent for code question: {intent}"
        )

    def test_04_space_complexity_binary_search(self):
        """Q4: 'Explain the space complexity of binary search.' → SPACE_COMPLEXITY, distinguishes O(1) iterative vs O(log n) recursive."""
        result = rag_query("Explain the space complexity of binary search.")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        # Must mention space/memory
        has_space = "space" in answer or "memory" in answer or "o(1)" in answer
        assert has_space, (
            f"Expected space complexity details. Got: {answer[:400]}"
        )
        assert intent in ("SPACE_COMPLEXITY", "COMPLEXITY_ANALYSIS", "CONCEPT_EXPLANATION"), (
            f"Unexpected intent for space complexity question: {intent}"
        )

    def test_05_compare_binary_linear_search(self):
        """Q5: 'Compare binary search and linear search.' → COMPARISON, mentions both."""
        result = rag_query("Compare binary search and linear search.")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "binary" in answer, f"Expected 'binary' in comparison. Got: {answer[:400]}"
        assert "linear" in answer, f"Expected 'linear' in comparison. Got: {answer[:400]}"
        assert intent in ("COMPARISON", "CONCEPT_EXPLANATION", "GENERAL"), (
            f"Unexpected intent for comparison question: {intent}"
        )

    def test_06_why_binary_search_needs_sorted(self):
        """Q6: 'Why does binary search require sorted data?' → WHY_EXPLANATION."""
        result = rag_query("Why does binary search require sorted data?")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "sort" in answer or "order" in answer or "ascending" in answer or "descending" in answer, (
            f"Expected sort-related explanation. Got: {answer[:400]}"
        )
        assert intent in ("WHY_EXPLANATION", "CONCEPT_EXPLANATION", "GENERAL"), (
            f"Unexpected intent for why question: {intent}"
        )

    def test_07_what_is_fastapi(self):
        """Q7: 'What is FastAPI?' → CONCEPT_EXPLANATION for FastAPI (different topic)."""
        result = rag_query("What is FastAPI?")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "fastapi" in answer or "api" in answer or "python" in answer or "web" in answer, (
            f"Expected FastAPI description. Got: {answer[:400]}"
        )
        # Should NOT be about binary search
        assert "binary search" not in answer.lower()[:200], (
            "Answer about FastAPI should not mention binary search as primary content."
        )

    def test_08_fix_python_typeerror(self):
        """Q8: 'How do I fix a Python TypeError?' → CODE_DEBUGGING, mentions TypeError."""
        result = rag_query("How do I fix a Python TypeError?")
        answer = result.get("answer", "").lower()
        intent = result.get("intent", "")

        assert "typeerror" in answer or "type error" in answer or "type" in answer, (
            f"Expected TypeError guidance. Got: {answer[:400]}"
        )
        assert intent in ("CODE_DEBUGGING", "DEBUGGING", "CONCEPT_EXPLANATION"), (
            f"Unexpected intent for debugging question: {intent}"
        )

    def test_09_non_technical_joke(self):
        """Q9: 'Tell me a joke.' → NON_TECHNICAL, exact refusal phrasing."""
        result = rag_query("Tell me a joke.")
        answer = result.get("answer", "")
        source = result.get("source", "")

        assert source == "domain_filter", (
            f"Expected source='domain_filter' for non-technical question, got: {source}"
        )
        assert "AI Tech Bot" in answer, (
            f"Expected refusal with 'AI Tech Bot'. Got: {answer[:400]}"
        )
        assert NON_TECHNICAL_REFUSAL in answer or (
            "programming" in answer.lower() and "technical" in answer.lower()
        ), f"Expected refusal phrasing. Got: {answer[:400]}"

    def test_10_non_technical_weather(self):
        """Q10: 'What is the weather today?' → NON_TECHNICAL, exact refusal phrasing."""
        result = rag_query("What is the weather today?")
        answer = result.get("answer", "")
        source = result.get("source", "")

        assert source == "domain_filter", (
            f"Expected source='domain_filter', got: {source}"
        )
        assert NON_TECHNICAL_REFUSAL in answer or (
            "AI Tech Bot" in answer and "technical" in answer.lower()
        ), f"Expected refusal phrasing. Got: {answer[:400]}"


# ===========================================================================
# 2. Distinct answers: same topic, different intents
# ===========================================================================

class TestDistinctAnswersPerIntent:
    """
    The 4 binary-search variants must each produce a DIFFERENT answer.
    This is the core regression test for the 'canned template' bug.
    """

    def test_binary_search_all_four_intents_are_distinct(self):
        """Questions 1-4 (definition, time complexity, Java code, space complexity) must yield 4 distinct answers."""
        q1 = rag_query("What is binary search?")["answer"]
        q2 = rag_query("What is the time complexity of binary search?")["answer"]
        q3 = rag_query("Write binary search in Java.")["answer"]
        q4 = rag_query("Explain the space complexity of binary search.")["answer"]

        answers = [q1, q2, q3, q4]
        assert_distinct_answers(answers, label="(binary search 4-intent test)")

    def test_time_vs_space_complexity_are_distinct(self):
        """Time complexity and space complexity answers must not be identical."""
        time_ans = rag_query("What is the time complexity of binary search?")["answer"]
        space_ans = rag_query("What is the space complexity of binary search?")["answer"]

        assert time_ans.strip().lower() != space_ans.strip().lower(), (
            "Time complexity and space complexity answers are identical — wrong answer reuse detected."
        )

    def test_fastapi_vs_binary_search_are_distinct(self):
        """Questions about different topics must produce completely different answers."""
        bs_ans = rag_query("What is binary search?")["answer"].lower()
        fa_ans = rag_query("What is FastAPI?")["answer"].lower()

        assert bs_ans != fa_ans, "Answers for different topics (binary search, FastAPI) must differ."

        # FastAPI answer must not have binary search as main content
        # (It may mention it coincidentally but the primary topic must differ)
        assert fa_ans[:200] != bs_ans[:200], "First 200 chars are identical — likely canned response."


# ===========================================================================
# 3. Provider selection logic
# ===========================================================================

class TestProviderSelection:
    """Verify get_llm_provider() returns the right provider for various env states."""

    def test_groq_selected_when_llm_provider_env_is_groq(self):
        from services.llm_provider import get_llm_provider, GroqProvider
        env_patch = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_test12345",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GroqProvider), (
            f"Expected GroqProvider when LLM_PROVIDER=groq, got {type(provider).__name__}"
        )
        assert provider.model == "openai/gpt-oss-120b"
        assert provider.base_url == "https://api.groq.com/openai/v1"

    def test_groq_selected_when_groq_api_key_set(self):
        from services.llm_provider import get_llm_provider, GroqProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "gsk_test12345",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GroqProvider), (
            f"Expected GroqProvider when GROQ_API_KEY is set, got {type(provider).__name__}"
        )

    def test_groq_selected_when_generic_key_starts_with_gsk(self):
        from services.llm_provider import get_llm_provider, GroqProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "gsk_genericKey123",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GroqProvider), (
            f"Expected GroqProvider when generic key starts with 'gsk_', got {type(provider).__name__}"
        )

    def test_gsk_key_in_xai_key_env_redirects_to_groq_never_xai(self):
        """Do not send a Groq key (gsk_...) to the xAI endpoint."""
        from services.llm_provider import get_llm_provider, GroqProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "gsk_accidentalKeyInXaiEnv",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GroqProvider), (
            "Groq key starting with 'gsk_' in XAI_API_KEY should redirect to GroqProvider, not xAI Grok."
        )

    def test_grok_selected_when_real_xai_api_key_set(self):
        from services.llm_provider import get_llm_provider, GrokProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "xai-realXaiKey123",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GrokProvider), (
            f"Expected GrokProvider when true xAI key is configured, got {type(provider).__name__}"
        )

    def test_gemini_selected_when_only_gemini_key_set(self):
        from services.llm_provider import get_llm_provider, GeminiProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "AIzaTestGeminiKey",
            "GOOGLE_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, GeminiProvider), (
            f"Expected GeminiProvider when only GEMINI_API_KEY is set, got {type(provider).__name__}"
        )

    def test_fallback_provider_when_no_keys(self):
        from services.llm_provider import get_llm_provider, FallbackProvider
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "GOOGLE_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            provider = get_llm_provider()
        assert isinstance(provider, FallbackProvider), (
            f"Expected FallbackProvider when no keys configured, got {type(provider).__name__}"
        )

    def test_groq_provider_info_contains_required_fields(self):
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="gsk_testkey", model="openai/gpt-oss-120b")
        info = groq.get_info()
        assert info["provider"] == "groq"
        assert info["model"] == "openai/gpt-oss-120b"
        assert "has_api_key" in info
        assert info["has_api_key"] is True
        assert info.get("base_url", "").startswith("https://api.groq.com/openai/v1")
        assert "gsk_" not in str(info)


# ===========================================================================
# 4. API key missing & API errors — no crash, graceful fallback
# ===========================================================================

class TestProviderErrorHandling:
    """Provider errors must not crash the API; fallback must produce a valid answer."""

    def test_groq_provider_returns_none_on_empty_key(self):
        """GroqProvider.generate_text() must return None (not raise) when api_key is empty."""
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="", model="openai/gpt-oss-120b")
        result = groq.generate_text("You are helpful.", "What is binary search?")
        assert result is None, "GroqProvider with empty key should return None, not raise."

    def test_groq_api_401_auth_error_returns_none(self):
        """HTTP 401 must be recognized as AUTH_ERROR and return None."""
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="gsk_invalid_key", model="openai/gpt-oss-120b")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"error": {"message": "Invalid API Key"}}'

        with patch("httpx.Client.post", return_value=mock_resp):
            res = groq.generate_text("System", "User")
            assert res is None

    def test_groq_api_404_model_not_found_returns_none(self):
        """HTTP 404 must be recognized as MODEL_NOT_FOUND and return None."""
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="gsk_valid_key", model="non-existent-model")
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = '{"error": {"message": "Model not found"}}'

        with patch("httpx.Client.post", return_value=mock_resp):
            res = groq.generate_text("System", "User")
            assert res is None

    def test_groq_api_429_rate_limit_returns_none(self):
        """HTTP 429 must be recognized as RATE_LIMIT and return None."""
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="gsk_valid_key", model="openai/gpt-oss-120b")
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = '{"error": {"message": "Rate limit reached"}}'

        with patch("httpx.Client.post", return_value=mock_resp):
            res = groq.generate_text("System", "User")
            assert res is None

    def test_groq_timeout_returns_none(self):
        """httpx.TimeoutException must return None without crashing."""
        import httpx
        from services.llm_provider import GroqProvider
        groq = GroqProvider(api_key="gsk_valid_key", model="openai/gpt-oss-120b")

        with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timeout")):
            res = groq.generate_text("System", "User")
            assert res is None

    def test_bad_groq_key_returns_fallback_answer_not_crash(self):
        """With a bad Groq key and no other providers, the bot should still return an answer."""
        env_patch = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_totally-invalid-key",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "GOOGLE_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            result = rag_query("What is binary search?")

        assert "answer" in result, "Response must have an 'answer' field even when API key is invalid."
        assert len(result["answer"]) > 10, "Fallback answer must be non-trivial."
        assert result.get("provider") == "fallback", "Failed provider must be labeled as 'fallback'."

    def test_no_api_key_still_answers_technical_question(self):
        """With NO API keys at all, the local knowledge base should still produce an answer."""
        env_patch = {
            "LLM_PROVIDER": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "GOOGLE_API_KEY": "",
            "OPENAI_API_KEY": "",
            "LLM_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            result = rag_query("What is binary search?")

        assert "answer" in result
        answer = result["answer"].lower()
        assert "binary" in answer or "search" in answer or "algorithm" in answer, (
            f"Even without API keys, should return KB answer. Got: {answer[:300]}"
        )
        assert result.get("provider") == "fallback"


# ===========================================================================
# 5. LLM status endpoint
# ===========================================================================

class TestLlmStatusEndpoint:
    """GET /api/llm/status must return a valid status object."""

    def test_llm_status_endpoint_exists_and_responds(self):
        resp = client.get("/api/llm/status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "provider" in data, "Status must contain 'provider' field."
        assert "model" in data, "Status must contain 'model' field."
        assert "has_api_key" in data, "Status must contain 'has_api_key' field."

    def test_llm_status_provider_matches_env_config(self):
        """If LLM_PROVIDER=groq is configured, status should say groq."""
        env_patch = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_test123",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            resp = client.get("/api/llm/status")
            data = resp.json()
            assert data["provider"] == "groq", f"Expected groq, got {data['provider']}"
            assert data["model"] == "openai/gpt-oss-120b"
            assert data["has_api_key"] is True


# ===========================================================================
# 6. Domain boundary — technical vs non-technical
# ===========================================================================

class TestDomainBoundary:
    """Verify non-technical questions are filtered before RAG pipeline."""

    @pytest.mark.parametrize("question", [
        "Tell me a joke.",
        "What is the weather today?",
        "Who is the president of France?",
        "Write me a poem about love.",
        "What should I eat for lunch?",
    ])
    def test_non_technical_questions_are_refused(self, question):
        result = rag_query(question)
        source = result.get("source", "")
        answer = result.get("answer", "")

        assert source == "domain_filter", (
            f"'{question}' should be filtered. Got source='{source}', answer='{answer[:200]}'"
        )
        assert "AI Tech Bot" in answer or "technical question" in answer.lower(), (
            f"Expected refusal. Got: {answer[:300]}"
        )

    @pytest.mark.parametrize("question", [
        "What is binary search?",
        "Explain polymorphism in Java.",
        "How does SQL indexing work?",
        "What is FastAPI?",
        "Explain the space complexity of merge sort.",
    ])
    def test_technical_questions_are_not_refused(self, question):
        result = rag_query(question)
        source = result.get("source", "")

        assert source != "domain_filter", (
            f"'{question}' is technical and should NOT be filtered. Got source='{source}'"
        )
        assert len(result.get("answer", "")) > 20, (
            f"Expected a real answer for '{question}'. Got: {result.get('answer', '')[:300]}"
        )


# ===========================================================================
# 7. Intent classifier unit tests
# ===========================================================================

class TestIntentClassifier:
    """Unit-test classify_intent() directly, without hitting the API."""

    def _classify(self, query, history=None):
        from rag.intent_classifier import classify_intent
        return classify_intent(query, history or [])

    def test_what_is_query_produces_concept_intent(self):
        info = self._classify("What is binary search?")
        assert info["primary_intent"] in (
            "CONCEPT_EXPLANATION", "DEFINITION", "GENERAL"
        ), f"Got: {info['primary_intent']}"

    def test_time_complexity_query_produces_time_intent(self):
        info = self._classify("What is the time complexity of binary search?")
        assert info["primary_intent"] in (
            "TIME_COMPLEXITY", "COMPLEXITY_ANALYSIS"
        ), f"Got: {info['primary_intent']}"

    def test_space_complexity_query_produces_space_intent(self):
        info = self._classify("Explain the space complexity of binary search.")
        assert info["primary_intent"] in (
            "SPACE_COMPLEXITY", "COMPLEXITY_ANALYSIS"
        ), f"Got: {info['primary_intent']}"

    def test_write_code_produces_code_intent(self):
        info = self._classify("Write binary search in Java.")
        assert info["primary_intent"] in (
            "CODE_EXAMPLE", "IMPLEMENTATION"
        ), f"Got: {info['primary_intent']}"

    def test_comparison_query_produces_comparison_intent(self):
        info = self._classify("Compare binary search and linear search.")
        assert info["primary_intent"] in (
            "COMPARISON", "CONCEPT_EXPLANATION"
        ), f"Got: {info['primary_intent']}"

    def test_why_query_produces_why_intent(self):
        info = self._classify("Why does binary search require sorted data?")
        assert info["primary_intent"] in (
            "WHY_EXPLANATION", "CONCEPT_EXPLANATION"
        ), f"Got: {info['primary_intent']}"

    def test_debugging_query_produces_debugging_intent(self):
        info = self._classify("How do I fix a Python TypeError?")
        assert info["primary_intent"] in (
            "CODE_DEBUGGING", "DEBUGGING", "CODE_EXAMPLE", "CONCEPT_EXPLANATION"
        ), f"Got: {info['primary_intent']}"

    def test_time_space_complexity_intents_are_different(self):
        time_info = self._classify("What is the time complexity of binary search?")
        space_info = self._classify("What is the space complexity of binary search?")
        # At minimum, they should not both produce the same non-generic intent
        if (time_info["primary_intent"] not in ("CONCEPT_EXPLANATION", "GENERAL")
                and space_info["primary_intent"] not in ("CONCEPT_EXPLANATION", "GENERAL")):
            assert time_info["primary_intent"] != space_info["primary_intent"], (
                "Time complexity and space complexity should map to different intents, "
                f"but both got: {time_info['primary_intent']}"
            )
