"""
vector_store.py — Lightweight, memory-efficient knowledge store for AI Interview Assistant RAG.
Optimized for 512MB RAM environments (e.g. Render Free tier).
Uses TF-IDF sublinear n-gram matching with cosine similarity instead of heavy PyTorch/SentenceTransformers.
"""

import os
import re
import pickle
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

INDEX_PATH = os.path.join(os.path.dirname(__file__), "vector_index.pkl")
KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")


class VectorStore:
    """
    Lightweight, bounded-memory knowledge store.
    Stores chunk metadata and a compact TF-IDF sparse matrix.
    Memory footprint: < 2 MB (vs 350-500+ MB for SentenceTransformer/PyTorch).
    """

    def __init__(self, index_path: str = INDEX_PATH, kb_dir: str = KB_DIR):
        self.index_path = index_path
        self.kb_dir = kb_dir
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None  # Scipy sparse matrix (N, V)
        self._is_loaded = False

    @property
    def embeddings(self):
        """Backward compatibility alias for self.matrix."""
        return self.matrix

    @embeddings.setter
    def embeddings(self, val):
        self.matrix = val

    def is_ready(self) -> bool:
        """Check if index has chunks and matrix loaded."""
        return bool(self.chunks and self.matrix is not None and self.vectorizer is not None)

    def _init_vectorizer(self) -> TfidfVectorizer:
        return TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            token_pattern=r"(?u)\b\w[\w+\.#-]*\w\b|\b\w+\b",
            lowercase=True,
        )

    def fit(self, chunks: List[Dict[str, Any]]) -> bool:
        """Fit TF-IDF matrix on given chunks."""
        if not chunks:
            self.chunks = []
            self.vectorizer = None
            self.matrix = None
            self._is_loaded = False
            return False

        search_texts = []
        for c in chunks:
            topic = c.get("topic", "")
            source = c.get("source", "")
            text = c.get("text", "")
            # Topic and source repetition gives domain-level query boost (e.g. "Java", "Python")
            search_text = f"{topic} {topic} {source} {text}"
            search_texts.append(search_text)

        self.vectorizer = self._init_vectorizer()
        self.matrix = self.vectorizer.fit_transform(search_texts)
        self.chunks = chunks
        self._is_loaded = True
        logger.info("Fitted lightweight RAG index with %d chunks.", len(chunks))
        return True

    def add_chunks(self, new_chunks: List[Dict[str, Any]], new_embeddings=None):
        """Add chunks to store and refit index."""
        combined = list(self.chunks) + list(new_chunks)
        self.fit(combined)

    def search(
        self,
        query: Union[str, np.ndarray, list],
        top_k: int = 3,
        min_score: float = 0.08
    ) -> List[Dict[str, Any]]:
        """
        Search for top_k most relevant chunks matching query.
        Accepts query as string (fast TF-IDF) or numpy vector (backward compat).
        """
        if not self.is_ready():
            # Attempt to load from configured index path or build from configured knowledge base
            if not self.load(self.index_path):
                self.build_from_knowledge_base(self.kb_dir)

        if not self.is_ready() or not self.chunks:
            return []

        # Handle string query (standard fast path)
        if isinstance(query, str):
            cleaned = query.strip()
            if not cleaned:
                return []
            try:
                q_vec = self.vectorizer.transform([cleaned])
                scores = cosine_similarity(q_vec, self.matrix)[0]
            except Exception as e:
                logger.error("TF-IDF transform failed during search: %s", e)
                return []
        elif isinstance(query, (np.ndarray, list)):
            # Legacy vector query
            try:
                q_arr = np.asarray(query, dtype=np.float32)
                if q_arr.ndim == 1:
                    q_arr = q_arr.reshape(1, -1)
                if hasattr(self.matrix, "toarray"):
                    mat = self.matrix.toarray()
                else:
                    mat = self.matrix
                scores = cosine_similarity(q_arr, mat)[0]
            except Exception as e:
                logger.error("Vector search failed: %s", e)
                return []
        else:
            return []

        top_indices = np.argsort(scores)[::-1]
        results = []
        for idx in top_indices[:top_k]:
            score = float(scores[idx])
            if score >= min_score:
                chunk_copy = dict(self.chunks[idx])
                chunk_copy["score"] = round(score, 4)
                results.append(chunk_copy)
        return results

    def save(self, path: Optional[str] = None):
        """Save chunks, vectorizer and matrix to disk."""
        save_path = path or self.index_path
        try:
            with open(save_path, "wb") as f:
                pickle.dump(
                    {
                        "chunks": self.chunks,
                        "vectorizer": self.vectorizer,
                        "matrix": self.matrix,
                        "format": "tfidf_v1"
                    },
                    f
                )
            logger.info("Saved lightweight RAG index to %s", save_path)
        except Exception as e:
            logger.error("Failed to save RAG index to %s: %s", save_path, e)

    def load(self, path: Optional[str] = None) -> bool:
        """
        Load index from disk.
        If file contains legacy dense embeddings or is corrupt, returns False to trigger fresh rebuild.
        """
        load_path = path or self.index_path
        if not os.path.exists(load_path):
            return False
        try:
            with open(load_path, "rb") as f:
                data = pickle.load(f)
            # Check if this is our lightweight TF-IDF index
            if isinstance(data, dict) and "vectorizer" in data and "matrix" in data and "chunks" in data:
                self.chunks = data["chunks"]
                self.vectorizer = data["vectorizer"]
                self.matrix = data["matrix"]
                self._is_loaded = True
                return True
            # Legacy format with dense numpy array
            elif isinstance(data, dict) and "chunks" in data:
                chunks = data.get("chunks", [])
                if chunks:
                    return self.fit(chunks)
            return False
        except Exception as e:
            logger.warning("Could not load index from %s (%s). Rebuilding...", load_path, e)
            return False

    def build_from_knowledge_base(self, kb_dir: Optional[str] = None) -> int:
        """Parse markdown files in knowledge base directory and build index."""
        target_dir = kb_dir or self.kb_dir
        if not os.path.exists(target_dir):
            logger.warning("Knowledge base directory %s does not exist.", target_dir)
            return 0

        all_chunks = []
        for root, _, files in os.walk(target_dir):
            for file in sorted(files):
                if file.endswith(".md") or file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, target_dir)
                    topic = os.path.splitext(file)[0].replace("_", " ").title()
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        logger.error("Failed to read %s: %s", file_path, e)
                        continue

                    sections = re.split(r"\n(?=##\s+)", content)
                    for idx, sec in enumerate(sections):
                        sec_clean = sec.strip()
                        if not sec_clean:
                            continue
                        doc_chunk = {
                            "doc_id": f"{file}_{idx}",
                            "source": rel_path.replace("\\", "/"),
                            "topic": topic,
                            "text": sec_clean
                        }
                        all_chunks.append(doc_chunk)

        if all_chunks:
            self.fit(all_chunks)
            try:
                self.save(self.index_path)
            except Exception:
                pass
        return len(all_chunks)

    def clear(self):
        """Reset state."""
        self.chunks = []
        self.vectorizer = None
        self.matrix = None
        self._is_loaded = False


# Global singleton instance
vector_store = VectorStore()
