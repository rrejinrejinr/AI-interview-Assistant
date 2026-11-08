"""
ingestion.py — Lightweight knowledge base chunking and indexing.
Constructs lightweight TF-IDF index directly without SentenceTransformer.
"""

import os
import re
import logging
from typing import List
from rag.vector_store import vector_store

logger = logging.getLogger(__name__)

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")


def chunk_markdown_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split markdown text into logical section chunks."""
    sections = re.split(r'\n(?=##\s+)', text)
    chunks = []
    for sec in sections:
        sec_clean = sec.strip()
        if not sec_clean:
            continue
        words = sec_clean.split()
        if len(words) <= chunk_size:
            chunks.append(sec_clean)
        else:
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append(chunk)
    return chunks


def ingest_knowledge_base(kb_dir: str = KB_DIR) -> int:
    """
    Ingest markdown files from knowledge base directory into lightweight TF-IDF index.
    Zero PyTorch, zero sentence-transformers, < 2 MB memory.
    """
    if not os.path.exists(kb_dir):
        logger.warning("Knowledge base directory %s not found.", kb_dir)
        return 0

    count = vector_store.build_from_knowledge_base(kb_dir)
    logger.info("Successfully ingested and indexed %d knowledge chunks.", count)
    return count
