"""
embeddings.py — Lightweight text embedding module for AI Interview Assistant RAG.
Optimized for 512MB RAM environments (e.g. Render Free tier).
Uses scikit-learn TF-IDF vectorization to avoid loading heavy PyTorch/SentenceTransformers.
"""

import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

_lightweight_embedder = None


def get_embedder():
    """
    Returns a lightweight TF-IDF vectorizer.
    Does NOT import or load PyTorch or SentenceTransformer to keep memory well under 512MB.
    """
    global _lightweight_embedder
    if _lightweight_embedder is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _lightweight_embedder = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            token_pattern=r"(?u)\b\w[\w+\.#-]*\w\b|\b\w+\b",
            lowercase=True
        )
        logger.info("Lightweight TF-IDF embedder initialized.")
    return _lightweight_embedder


def compute_embedding(text: str) -> np.ndarray:
    """Compute lightweight TF-IDF embedding vector for single query string."""
    from rag.vector_store import vector_store
    if vector_store.is_ready() and vector_store.vectorizer is not None:
        try:
            vec = vector_store.vectorizer.transform([text])
            return np.asarray(vec.toarray()[0], dtype=np.float32)
        except Exception:
            pass
    # Fallback to local lightweight embedder
    embedder = get_embedder()
    try:
        vec = embedder.transform([text])
        return np.asarray(vec.toarray()[0], dtype=np.float32)
    except Exception:
        vec = embedder.fit_transform([text])
        return np.asarray(vec.toarray()[0], dtype=np.float32)


def compute_embeddings(texts: List[str]) -> np.ndarray:
    """Compute lightweight TF-IDF embedding vectors for a list of texts."""
    from rag.vector_store import vector_store
    if vector_store.is_ready() and vector_store.vectorizer is not None:
        try:
            vecs = vector_store.vectorizer.transform(texts)
            return np.asarray(vecs.toarray(), dtype=np.float32)
        except Exception:
            pass
    embedder = get_embedder()
    try:
        vecs = embedder.transform(texts)
        return np.asarray(vecs.toarray(), dtype=np.float32)
    except Exception:
        vecs = embedder.fit_transform(texts)
        return np.asarray(vecs.toarray(), dtype=np.float32)
