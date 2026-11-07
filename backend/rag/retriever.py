from typing import List, Dict, Any
from rag.embeddings import compute_embedding
from rag.vector_store import vector_store

def retrieve_knowledge(query: str, top_k: int = 3, min_score: float = 0.42) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        return []
    # If vector store is empty, attempt load
    if vector_store.embeddings is None:
        if not vector_store.load():
            from rag.ingestion import ingest_knowledge_base
            ingest_knowledge_base()

    query_emb = compute_embedding(query)
    results = vector_store.search(query_emb, top_k=top_k, min_score=min_score)
    return results
