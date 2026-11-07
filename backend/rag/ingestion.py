import os
import re
from typing import List, Dict, Any
from rag.embeddings import compute_embeddings
from rag.vector_store import vector_store

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

def chunk_markdown_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    # Split by markdown headers
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

def ingest_knowledge_base():
    if not os.path.exists(KB_DIR):
        print(f"Knowledge base directory {KB_DIR} not found.")
        return 0

    all_chunks = []
    chunk_texts = []

    for root, _, files in os.walk(KB_DIR):
        for file in files:
            if file.endswith(".md") or file.endswith(".txt"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, KB_DIR)
                topic = os.path.splitext(file)[0].replace("_", " ").title()
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                chunks = chunk_markdown_text(content)
                for idx, chunk_text in enumerate(chunks):
                    doc_chunk = {
                        "doc_id": f"{file}_{idx}",
                        "source": rel_path,
                        "topic": topic,
                        "text": chunk_text
                    }
                    all_chunks.append(doc_chunk)
                    chunk_texts.append(chunk_text)

    if not chunk_texts:
        print("No documents found to ingest.")
        return 0

    print(f"Embedding {len(chunk_texts)} knowledge chunks from {len(all_chunks)} files...")
    embeddings = compute_embeddings(chunk_texts)
    vector_store.embeddings = embeddings
    vector_store.chunks = all_chunks
    vector_store.save()
    print(f"Successfully indexed and saved {len(all_chunks)} chunks to vector index.")
    return len(all_chunks)
