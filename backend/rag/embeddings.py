import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

_rag_embedder = None

def get_embedder():
    global _rag_embedder
    if _rag_embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _rag_embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("RAG SentenceTransformer embedder 'all-MiniLM-L6-v2' loaded.")
        except Exception as e:
            logger.error(f"Failed to load RAG embedder: {e}")
            raise e
    return _rag_embedder
def compute_embedding(text: str) -> np.ndarray:
    embedder = get_embedder()
    emb = embedder.encode([text])[0]
    return np.array(emb, dtype=np.float32)

def compute_embeddings(texts: List[str]) -> np.ndarray:
    embedder = get_embedder()
    embs = embedder.encode(texts)
    return np.array(embs, dtype=np.float32)
