import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional

INDEX_PATH = os.path.join(os.path.dirname(__file__), "vector_index.pkl")

class VectorStore:
    def __init__(self):
        self.embeddings: Optional[np.ndarray] = None  # Shape: (N, D)
        self.chunks: List[Dict[str, Any]] = []

    def add_chunks(self, new_chunks: List[Dict[str, Any]], new_embeddings: np.ndarray):
        if self.embeddings is None or len(self.chunks) == 0:
            self.embeddings = new_embeddings
            self.chunks = new_chunks
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
            self.chunks.extend(new_chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 3, min_score: float = 0.25) -> List[Dict[str, Any]]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        # Compute cosine similarity: dot(A, B) / (|A| * |B|)
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        norms[norms == 0] = 1e-10
        scores = np.dot(self.embeddings, query_embedding) / norms

        top_indices = np.argsort(scores)[::-1]
        results = []
        for idx in top_indices[:top_k]:
            score = float(scores[idx])
            if score >= min_score:
                chunk_copy = dict(self.chunks[idx])
                chunk_copy["score"] = round(score, 4)
                results.append(chunk_copy)
        return results

    def save(self, path: str = INDEX_PATH):
        with open(path, "wb") as f:
            pickle.dump({"embeddings": self.embeddings, "chunks": self.chunks}, f)

    def load(self, path: str = INDEX_PATH) -> bool:
        if not os.path.exists(path):
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.embeddings = data["embeddings"]
                self.chunks = data["chunks"]
            return True
        except Exception as e:
            print(f"Error loading vector index: {e}")
            return False

# Global singleton
vector_store = VectorStore()
