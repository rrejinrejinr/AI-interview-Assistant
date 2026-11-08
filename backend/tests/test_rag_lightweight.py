"""
test_rag_lightweight.py
=======================
Unit and integration tests for the lightweight (512MB RAM-optimized) RAG pipeline.

Covers:
  1. Java-related knowledge retrieval (polymorphism, collections, JVM).
  2. Relevant document retrieval across diverse technical domains.
  3. Empty query handling (whitespace, empty, None).
  4. Missing knowledge-base directory or empty files handling.
  5. Graceful handling of RAG query errors / failures.
  6. Zero-PyTorch verification: importing and executing RAG does not load torch or sentence-transformers.
  7. API endpoint test: POST /api/rag/query executes cleanly.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vector_store import VectorStore, vector_store
from rag.retriever import retrieve_knowledge
from rag.rag_service import answer_with_rag
from app_fastapi import app
from database import SessionLocal
from models_db import User
from auth_utils import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "rag_test_user@example.com").first()
        if not user:
            user = User(
                name="RAG Tester",
                email="rag_test_user@example.com",
                password_hash=get_password_hash("TestPass123!"),
                email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(data={"sub": user.email, "user_id": user.id})
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. Java-Related Knowledge Retrieval
# ---------------------------------------------------------------------------

class TestJavaKnowledgeRetrieval:

    def test_java_polymorphism_retrieval(self):
        """Querying Java polymorphism retrieves java_programming.md with high relevance."""
        results = retrieve_knowledge("Explain polymorphism in Java", top_k=3)
        assert len(results) > 0, "Expected at least one retrieved chunk"
        top_chunk = results[0]
        assert top_chunk["source"] == "java_programming.md"
        assert "Polymorphism" in top_chunk["text"] or "polymorphism" in top_chunk["text"].lower()
        assert top_chunk["score"] > 0.15

    def test_java_collections_retrieval(self):
        """Querying ArrayList vs LinkedList in Java retrieves collections section."""
        results = retrieve_knowledge("What is the difference between ArrayList and LinkedList in Java?", top_k=3)
        assert len(results) > 0
        sources = [r["source"] for r in results]
        assert "java_programming.md" in sources
        matched_text = " ".join([r["text"] for r in results if r["source"] == "java_programming.md"])
        assert "ArrayList" in matched_text
        assert "LinkedList" in matched_text

    def test_jvm_architecture_retrieval(self):
        """Querying JVM and JDK retrieves Java platform components."""
        results = retrieve_knowledge("How does the JVM work and what is JDK vs JRE?", top_k=3)
        assert len(results) > 0
        sources = [r["source"] for r in results]
        assert "java_programming.md" in sources
        matched_text = " ".join([r["text"] for r in results if r["source"] == "java_programming.md"])
        assert "JVM" in matched_text or "Java Virtual Machine" in matched_text


# ---------------------------------------------------------------------------
# 2. Relevant Document Retrieval Across Domains
# ---------------------------------------------------------------------------

class TestRelevantDocumentRetrieval:

    @pytest.mark.parametrize("query,expected_source,expected_keyword", [
        ("How does binary search work and what is its time complexity?", "dsa_algorithms.md", "binary search"),
        ("What are ACID properties and indexing in SQL databases?", "sql_databases.md", "acid"),
        ("How do Docker containers and Kubernetes clusters work?", "cloud_docker_kubernetes.md", "docker"),
        ("Explain FastAPI dependency injection and async routes", "fastapi_backend.md", "fastapi"),
        ("What is machine learning supervised learning and gradient descent?", "machine_learning.md", "learning"),
    ])
    def test_domain_retrieval_accuracy(self, query, expected_source, expected_keyword):
        results = retrieve_knowledge(query, top_k=3)
        assert len(results) > 0, f"No chunks retrieved for query: {query}"
        sources = [r["source"] for r in results]
        assert expected_source in sources, f"Expected {expected_source} in {sources} for query: {query}"
        combined_text = " ".join([r["text"].lower() for r in results if r["source"] == expected_source])
        assert expected_keyword in combined_text, f"Expected '{expected_keyword}' in retrieved text"


# ---------------------------------------------------------------------------
# 3. Empty & Whitespace Query Handling
# ---------------------------------------------------------------------------

class TestEmptyQueryHandling:

    @pytest.mark.parametrize("empty_query", ["", "   ", "\t\n\r", None])
    def test_retrieve_knowledge_empty(self, empty_query):
        """retrieve_knowledge returns empty list for empty/whitespace input without throwing."""
        results = retrieve_knowledge(empty_query)
        assert results == []

    @pytest.mark.parametrize("empty_query", ["", "   ", None])
    def test_answer_with_rag_empty(self, empty_query):
        """answer_with_rag returns helpful empty prompt without failing."""
        res = answer_with_rag(empty_query)
        assert res["retrieved_count"] == 0
        assert res["source"] == "empty_query"
        assert "Please provide a technical question" in res["answer"]


# ---------------------------------------------------------------------------
# 4. Missing Knowledge Base Directory / Empty Store Handling
# ---------------------------------------------------------------------------

class TestMissingKnowledgeBaseHandling:

    def test_missing_directory_build(self, tmp_path):
        """build_from_knowledge_base gracefully returns 0 if directory does not exist."""
        non_existent_dir = str(tmp_path / "does_not_exist")
        dummy_idx = str(tmp_path / "dummy_idx.pkl")
        custom_store = VectorStore(index_path=dummy_idx, kb_dir=non_existent_dir)
        count = custom_store.build_from_knowledge_base(non_existent_dir)
        assert count == 0
        assert not custom_store.is_ready()
        results = custom_store.search("Java polymorphism")
        assert results == []

    def test_empty_directory_build(self, tmp_path):
        """Empty knowledge base directory builds 0 chunks and search returns empty."""
        empty_dir = str(tmp_path / "empty_kb")
        os.makedirs(empty_dir, exist_ok=True)
        dummy_idx = str(tmp_path / "dummy_empty_idx.pkl")
        custom_store = VectorStore(index_path=dummy_idx, kb_dir=empty_dir)
        count = custom_store.build_from_knowledge_base(empty_dir)
        assert count == 0
        assert custom_store.search("Python") == []

    def test_retrieve_knowledge_when_store_empty(self):
        """If vector store fails to load or find chunks, returns empty list without crashing."""
        with patch.object(vector_store, "is_ready", return_value=False), \
             patch.object(vector_store, "load", return_value=False), \
             patch("rag.ingestion.ingest_knowledge_base", return_value=0):
            res = retrieve_knowledge("Java")
            assert res == []


# ---------------------------------------------------------------------------
# 5. Graceful Handling of RAG Query Failures
# ---------------------------------------------------------------------------

class TestRagQueryFailures:

    def test_vector_store_search_exception_handled(self):
        """If search raises an unexpected exception, retrieve_knowledge catches and returns []."""
        with patch.object(vector_store, "search", side_effect=RuntimeError("Unexpected matrix error")):
            results = retrieve_knowledge("Explain Java")
            assert results == []

    def test_answer_with_rag_handles_retrieval_failure(self):
        """If retrieve_knowledge returns empty or fails, answer_with_rag falls back smoothly."""
        with patch("rag.rag_service.retrieve_knowledge", return_value=[]):
            res = answer_with_rag("What is Java?")
            assert res is not None
            assert "answer" in res
            assert len(res["answer"]) > 0


# ---------------------------------------------------------------------------
# 6. Zero PyTorch / SentenceTransformers Verification
# ---------------------------------------------------------------------------

class TestZeroPyTorchFootprint:

    def test_no_torch_or_sentence_transformers_in_modules(self):
        """Verify that importing and querying the RAG path does NOT load torch or sentence_transformers."""
        # Execute RAG query
        results = retrieve_knowledge("Explain polymorphism in Java and Python", top_k=2)
        assert len(results) > 0

        # Check sys.modules
        assert "torch" not in sys.modules, "Regression: PyTorch ('torch') was loaded into sys.modules!"
        assert "sentence_transformers" not in sys.modules, "Regression: 'sentence_transformers' was loaded!"


# ---------------------------------------------------------------------------
# 7. FastAPI Endpoint Integration Test
# ---------------------------------------------------------------------------

class TestRagApiEndpoint:

    def test_post_rag_query_success(self, auth_headers):
        """POST /api/rag/query returns 200 with answers and retrieved citations."""
        response = client.post(
            "/api/rag/query",
            json={"query": "Explain polymorphism in Java."},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got: {response.text}"
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 20
        assert "top_sources" in data
        assert "java_programming.md" in data["top_sources"]
        assert data.get("retrieved_count", 0) > 0
