"""
retriever.py — Lightweight RAG knowledge retrieval module.
Uses fast TF-IDF / sublinear matching from vector_store (< 1MB RAM)
without importing or running heavy deep learning models.
"""

import logging
from typing import List, Dict, Any
from rag.vector_store import vector_store

logger = logging.getLogger(__name__)

DEFAULT_MIN_SCORE = 0.08  # Calibrated for TF-IDF cosine similarity


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE
) -> List[Dict[str, Any]]:
    """
    Retrieve top_k relevant technical knowledge chunks matching the query.
    Uses lightweight TF-IDF / sublinear n-gram matching (< 1 MB RAM)
    without loading heavy PyTorch or SentenceTransformer models.
    """
    if not query or not str(query).strip():
        return []

    cleaned_query = str(query).strip()

    # Lazy-load or rebuild store if not loaded
    if not vector_store.is_ready():
        if not vector_store.load():
            from rag.ingestion import ingest_knowledge_base
            ingest_knowledge_base()

    try:
        results = vector_store.search(cleaned_query, top_k=top_k, min_score=min_score)
        return results
    except Exception as e:
        logger.error("Error retrieving knowledge for query: %s", e)
        return []
