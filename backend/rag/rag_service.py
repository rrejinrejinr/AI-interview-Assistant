"""
rag_service.py — Intent-Aware & Context-Aware RAG Pipeline for AI Tech Bot

Pipeline Flow:
  User Question + Conversation History
       ↓
  Domain Boundary Verification (is_technical_query with history & typo tolerance)
       ↓
  Intent Classification & Context Resolution (classify_intent)
       ↓
  Vector / Keyword Retrieval on Resolved Query (retrieve_knowledge)
       ↓
  Intent-Aware Synthesis (generate_rag_response with LLM & Structured Fallback)
       ↓
  Answer Delivery
"""

from typing import Dict, Any, Optional, List
from rag.retriever import retrieve_knowledge
from rag.tech_knowledge import is_technical_query
from rag.intent_classifier import classify_intent
from services.llm_service import generate_rag_response


def answer_with_rag(
    query: str,
    candidate_context: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {
            "answer": "Please provide a technical question to search the knowledge base.",
            "citations": [],
            "suggested_next_topics": ["Python", "FastAPI", "Data Structures", "System Design"],
            "retrieved_count": 0,
            "top_sources": [],
            "source": "empty_query",
            "intent": "EMPTY"
        }

    # 1. Enforce technical domain boundary with conversation history awareness
    if not is_technical_query(cleaned_query, history):
        return {
            "answer": "I’m the AI Tech Bot, designed to help with programming, computer science, AI/ML, and software development questions. Please ask me a technical question.",
            "citations": [],
            "suggested_next_topics": [
                "Data Structures & Algorithms",
                "System Design & Microservices",
                "Python / Java Architecture",
                "Database Indexing & ACID"
            ],
            "retrieved_count": 0,
            "top_sources": [],
            "source": "domain_filter",
            "provider": "system",
            "model": "domain_boundary",
            "intent": "NON_TECHNICAL"
        }

    # 1b. Ambiguous question guard — if query is too short and has no recognisable technical topic, ask for clarification
    # Only applies to standalone messages when there is no active conversation topic
    from rag.intent_classifier import extract_topic_from_text, normalize_and_correct_typos, extract_active_topic_from_history
    from rag.tech_knowledge import TECH_KEYWORDS
    active_topic_from_hist = extract_active_topic_from_history(history)
    corrected_for_ambiguity = normalize_and_correct_typos(cleaned_query)
    ambiguity_words = corrected_for_ambiguity.strip().split()
    if len(ambiguity_words) <= 2 and not active_topic_from_hist:
        detected_topic = extract_topic_from_text(corrected_for_ambiguity.lower())
        # Also accept if ANY word in the query is a known TECH_KEYWORD
        query_words_lower = set(w.strip("?.!:,") for w in corrected_for_ambiguity.lower().split())
        has_direct_keyword = bool(query_words_lower & TECH_KEYWORDS)
        if not detected_topic and not has_direct_keyword:
            return {
                "answer": (
                    "Your question is a bit ambiguous. Could you please provide more detail?\n\n"
                    "For example:\n"
                    "- \"What is a binary search tree?\"\n"
                    "- \"Explain polymorphism in Java.\"\n"
                    "- \"How does indexing work in SQL?\""
                ),
                "citations": [],
                "suggested_next_topics": ["Data Structures", "OOP Concepts", "SQL & Databases"],
                "retrieved_count": 0,
                "top_sources": [],
                "source": "ambiguous_query",
                "intent": "AMBIGUOUS"
            }

    # 2. Classify intent & resolve contextual follow-ups from history
    intent_info = classify_intent(cleaned_query, history)
    effective_query = intent_info.get("resolved_query") or cleaned_query

    # 3. Retrieve relevant technical chunks from knowledge base using resolved query
    retrieved = retrieve_knowledge(effective_query, top_k=top_k)

    # 4. Synthesize answer tailored specifically to user's question, resolved intent, and history
    result = generate_rag_response(
        query=effective_query,
        retrieved_chunks=retrieved,
        candidate_context=candidate_context,
        intent_info=intent_info,
        history=history
    )

    result["retrieved_count"] = len(retrieved)
    # Deduplicate sources while preserving ranking order
    seen_sources = set()
    top_sources = []
    for r in retrieved:
        src = r.get("source", "knowledge_base")
        if src and src not in seen_sources:
            seen_sources.add(src)
            top_sources.append(src)

    if not top_sources:
        # Provide domain-specific curated source name
        active_t = intent_info.get("active_topic") or ""
        if "binary search" in active_t or "dsa" in active_t or "sort" in active_t or "stack" in active_t:
            top_sources = ["dsa_algorithms.md"]
        elif "java" in active_t:
            top_sources = ["java_programming.md"]
        elif "python" in active_t:
            top_sources = ["python_programming.md"]
        elif "sql" in active_t or "database" in active_t:
            top_sources = ["sql_databases.md"]
        elif "api" in active_t or "jwt" in active_t:
            top_sources = ["web_apis_networking.md"]
        else:
            top_sources = ["curated_technical_knowledge"]

    result["top_sources"] = top_sources
    if not result.get("citations"):
        result["citations"] = top_sources
    result["intent"] = intent_info.get("primary_intent", "CONCEPT_EXPLANATION")
    result["active_topic"] = intent_info.get("active_topic")
    result["is_followup"] = intent_info.get("is_followup", False)

    return result
