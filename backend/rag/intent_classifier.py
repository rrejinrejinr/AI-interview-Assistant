"""
intent_classifier.py — Precise Technical Query Intent Detection, Typo Correction & Context Resolution

Provides:
  1. Typo normalization and fuzzy keyword matching (e.g., complexsitiy -> complexity, binarry -> binary)
  2. Conversation context & active topic extraction from recent chat history
  3. Strict topic-switch detection (e.g. "what is binary search" followed by "what is java" resets active topic)
  4. Contextual query expansion ONLY for genuine follow-ups (e.g. "time complexsitiy", "explain it in Java", "why?", "how do I join two tables")
  5. Precise multi-intent classification (CONCEPT_EXPLANATION, CODE_EXAMPLE, WHY_EXPLANATION, COMPLEXITY_ANALYSIS, etc.)
"""

import re
import difflib
from typing import Dict, Any, Optional, List

# Standard Technical Vocabulary Targets for Fuzzy Matching
TECH_FUZZY_TARGETS = [
    "complexity", "time complexity", "space complexity", "binary", "search", "binary search",
    "algorithm", "recursion", "recursive", "recursively", "java", "python", "javascript", "typescript",
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "authentication", "stateless",
    "infinite", "loop", "useeffect", "usestate", "react", "arraylist", "linkedlist", "stack", "queue",
    "merge", "sort", "mergesort", "quicksort", "heapsort", "dynamic", "programming", "tree", "graph",
    "database", "indexing", "normalization", "docker", "kubernetes", "microservices", "linear search",
    "linear", "handshake", "fastapi", "django", "spring", "springboot", "jwt", "sql", "api", "apis"
]

EXPLICIT_TYPO_MAP = {
    "complexsitiy": "complexity",
    "complexsity": "complexity",
    "complexty": "complexity",
    "complexitiy": "complexity",
    "binarry": "binary",
    "binry": "binary",
    "serach": "search",
    "serch": "search",
    "algoritm": "algorithm",
    "algorithem": "algorithm",
    "recurrsion": "recursion",
    "reccursion": "recursion",
    "recursiv": "recursive",
    "jav": "java",
    "pyhton": "python",
    "pyton": "python",
    "postgre": "postgresql",
    "postgres": "postgresql",
    "autentication": "authentication",
    "authentcation": "authentication",
    "auth": "authentication",
    "useefect": "useeffect",
    "useefct": "useeffect",
    "statles": "stateless",
    "statless": "stateless",
    "infinit": "infinite",
    "infinitly": "infinite",
    "arraylst": "arraylist",
    "linkedlst": "linkedlist"
}

SUPPORTED_LANGUAGES = {
    "java": "Java",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "js": "JavaScript",
    "ts": "TypeScript",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "php": "PHP",
    "ruby": "Ruby"
}

COMMON_NON_TYPO_WORDS = {
    "what", "why", "how", "when", "where", "who", "which", "is", "are", "was", "were", "do", "does",
    "did", "can", "could", "should", "would", "must", "in", "on", "at", "to", "for", "with", "from",
    "by", "of", "and", "or", "not", "an", "the", "a", "it", "its", "this", "that", "these", "those",
    "give", "me", "show", "tell", "explain", "write", "code", "example", "program", "syntax", "work",
    "works", "use", "uses", "used", "call", "called", "cause", "causes", "loop", "array", "sorted",
    "render", "diff", "difference", "between", "vs", "versus", "compare", "problem", "problems",
    "best", "practice", "practices", "time", "space", "fast", "slow", "better", "join", "table", "tables"
}

# Recognized technical anchor topics in priority order
KNOWN_ANCHORS = [
    ("binary search", ["binary search", "binarry search", "binary serach"]),
    ("jwt", ["jwt", "json web token", "stateless authentication"]),
    ("react useeffect", ["useeffect", "react useeffect", "use effect"]),
    ("recursion", ["recursion", "recurrsion", "recursive"]),
    ("merge sort", ["merge sort", "mergesort"]),
    ("quicksort", ["quicksort", "quick sort"]),
    ("arraylist vs linkedlist", ["arraylist", "linkedlist", "array list", "linked list"]),
    ("stack", ["stack", "arraystack"]),
    ("queue", ["queue"]),
    ("tcp", ["tcp", "tcp handshake", "3-way handshake", "tcp vs udp"]),
    ("sql", ["sql", "database", "databases", "rdbms", "postgresql", "postgres", "mysql", "sqlite", "indexing", "normalization", "tables", "join"]),
    ("api", ["api", "apis", "rest api", "rest apis", "restful", "endpoints"]),
    ("java", ["java", "jvm", "jre", "jdk"]),
    ("python", ["python", "cpython", "gil"]),
    ("fastapi", ["fastapi"]),
    ("spring boot", ["spring boot", "springboot", "spring"]),
    ("docker", ["docker", "container", "containers"]),
    ("kubernetes", ["kubernetes", "k8s", "pod", "pods"]),
    ("rag", ["rag", "retrieval augmented generation", "retrieval-augmented generation"]),
    ("embeddings", ["embedding", "embeddings", "vector embedding"]),
    ("overfitting", ["overfitting", "overfit"]),
    ("gradient descent", ["gradient descent", "gradient"]),
    ("polymorphism", ["polymorphism"]),
    ("typeerror", ["typeerror", "type error", "python typeerror"]),
    ("git", ["git", "git rebase", "git merge", "rebase"])
]


def normalize_and_correct_typos(query: str) -> str:
    """
    Normalizes lowercase query and performs targeted typo correction
    without over-correcting standard English words.
    """
    if not query:
        return ""

    q_lower = query.strip().lower()

    # Check explicit multi-word typo replacements first
    for typo, correct in EXPLICIT_TYPO_MAP.items():
        if " " in typo and typo in q_lower:
            q_lower = q_lower.replace(typo, correct)

    # Tokenize preserving punctuation boundaries
    tokens = re.findall(r"[a-z0-9+#.-]+|[^\w\s]", q_lower)
    corrected_tokens = []

    for tok in tokens:
        clean_tok = tok.lower().strip(".,;:!?()[]{}")
        if not clean_tok or not clean_tok.isalpha():
            corrected_tokens.append(tok)
            continue

        # 1. Check if token is in explicit dictionary
        if clean_tok in EXPLICIT_TYPO_MAP:
            corrected_tokens.append(EXPLICIT_TYPO_MAP[clean_tok])
            continue

        # 2. Do not modify common ordinary words
        if clean_tok in COMMON_NON_TYPO_WORDS or len(clean_tok) <= 3:
            corrected_tokens.append(tok)
            continue

        # 3. Fuzzy match against technical keywords if token is not an exact match
        if clean_tok not in TECH_FUZZY_TARGETS:
            matches = difflib.get_close_matches(clean_tok, TECH_FUZZY_TARGETS, n=1, cutoff=0.82)
            if matches:
                corrected_tokens.append(matches[0])
                continue

        corrected_tokens.append(tok)

    # Reassemble string cleanly
    result = " ".join(corrected_tokens)
    result = re.sub(r"\s+([.,;:!?])", r"\1", result)
    result = re.sub(r"\(\s+", "(", result)
    result = re.sub(r"\s+\)", ")", result)
    result = re.sub(r"\b([a-zA-Z0-9]+)\s+\(", r"\1(", result)
    return result


def detect_language(query: str) -> Optional[str]:
    """Detects if a specific programming language is mentioned in the query."""
    q_lower = query.lower()
    cleaned = re.sub(r"[^\w\s+#.-]", " ", q_lower)
    words = [w.strip(".,;:!?()[]{}") for w in cleaned.split()]

    for w in words:
        if w in SUPPORTED_LANGUAGES:
            return SUPPORTED_LANGUAGES[w]

    if "c plus plus" in q_lower or "c++" in q_lower:
        return "C++"
    if "c sharp" in q_lower or "c#" in q_lower:
        return "C#"

    return None


def extract_topic_from_text(text: str) -> Optional[str]:
    """Extracts the primary technical topic entity from a given text string."""
    if not text:
        return None
    t_lower = text.lower()
    for anchor_name, patterns in KNOWN_ANCHORS:
        for p in patterns:
            # Match whole word pattern or phrase
            if re.search(r"\b" + re.escape(p) + r"\b", t_lower):
                return anchor_name
    return None


def extract_active_topic_from_history(history: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Extracts the primary active technical topic from recent conversation turns."""
    if not history:
        return None

    # Look backwards from most recent message
    for msg in reversed(history[-6:]):
        text = str(msg.get("text", "")).lower()
        topic = extract_topic_from_text(text)
        if topic:
            return topic

    return None


def resolve_contextual_query(query: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Resolves short follow-up questions and typos by leveraging conversation history.
    Strictly distinguishes NEW TOPICS (topic switches) from GENUINE FOLLOW-UPS.
    """
    corrected = normalize_and_correct_typos(query)
    c_lower = corrected.lower().strip("?!. ")
    prev_active_topic = extract_active_topic_from_history(history)
    current_topic_in_query = extract_topic_from_text(c_lower)

    # 1. Check for Pronoun References FIRST
    has_pronoun_reference = any(re.search(r"\b" + re.escape(p) + r"\b", c_lower) for p in ["it", "this", "that", "its", "these"])

    # 2. If query explicitly mentions its own topic entity and does NOT contain pronoun references to earlier topics, it is a standalone topic
    if current_topic_in_query and not has_pronoun_reference:
        return {
            "original_query": query,
            "corrected_query": corrected,
            "resolved_query": corrected,
            "active_topic": current_topic_in_query,
            "is_followup": False
        }

    followup_exact_patterns = [
        "time complexity", "space complexity", "complexity", "what is the time complexity",
        "what is the space complexity", "big o", "big-o",
        "why", "why?", "why is that", "why is it", "why is it o(log n)",
        "why stateless", "why stateless?", "why infinite loop", "why infinite loop?",
        "java code", "python code", "c++ code", "code", "show code", "example", "show java code", "code example",
        "recursive", "recursive code", "recursive version", "recursive implementation",
        "how does it work", "compare with linear search", "linear search", "practice problems", "give me 5 problems"
    ]

    is_followup_pattern = (
        c_lower in followup_exact_patterns or
        c_lower.startswith("why ") or
        "time complexity" in c_lower or
        "space complexity" in c_lower or
        "recursive" in c_lower or
        c_lower in ["java", "python", "c++", "code", "example"]
    )

    # Sub-topic continuations for specific domains
    is_domain_continuation = False
    if prev_active_topic in ["sql", "database"] and any(k in c_lower for k in ["join", "tables", "two tables", "inner join", "left join", "group by", "query"]):
        is_domain_continuation = True
    elif prev_active_topic == "react useeffect" and any(k in c_lower for k in ["infinite loop", "re-render", "cleanup", "dependency"]):
        is_domain_continuation = True
    elif prev_active_topic == "jwt" and any(k in c_lower for k in ["stateless", "refresh token", "secret", "payload"]):
        is_domain_continuation = True
    elif prev_active_topic == "binary search" and any(k in c_lower for k in ["sorted", "why sorted", "unsorted", "log n", "divide"]):
        is_domain_continuation = True

    is_followup = False
    resolved = corrected
    active_topic = current_topic_in_query or prev_active_topic

    if prev_active_topic and (has_pronoun_reference or is_followup_pattern or is_domain_continuation):
        is_followup = True
        active_topic = prev_active_topic

        # Expand follow-up cleanly with active topic
        words = c_lower.split()
        if ("space complexity" in c_lower or c_lower == "space") and "time" not in c_lower:
            resolved = f"What is the space complexity of {active_topic}?"
        elif ("time complexity" in c_lower or c_lower == "time") and "space" not in c_lower:
            resolved = f"What is the time complexity of {active_topic}?"
        elif "complexity" in c_lower:
            resolved = f"What is the time and space complexity of {active_topic}?"
        elif c_lower in ["why", "why?", "why is that", "why is it"]:
            if active_topic == "binary search":
                resolved = "Why is binary search O(log n)?"
            elif active_topic == "jwt":
                resolved = "Why is JWT called stateless authentication?"
            elif active_topic == "react useeffect":
                resolved = "Why can React useEffect cause an infinite render loop?"
            else:
                resolved = f"Why does {active_topic} work that way?"
        elif "java" in c_lower and ("code" in c_lower or "explain" in c_lower or has_pronoun_reference or len(words) <= 2):
            resolved = f"Explain {active_topic} in Java with an example."
        elif "python" in c_lower and ("code" in c_lower or "explain" in c_lower or has_pronoun_reference or len(words) <= 2):
            resolved = f"Explain {active_topic} in Python with an example."
        elif c_lower in ["code", "show code", "example"]:
            resolved = f"Explain {active_topic} with a code example."
        elif "why stateless" in c_lower:
            resolved = "Why is JWT called stateless authentication?"
        elif "why infinite" in c_lower or "infinite loop" in c_lower:
            resolved = "Why can React useEffect cause an infinite render loop?"
        elif "recursive" in c_lower:
            resolved = f"Give me recursive {active_topic} in Java."
        elif is_domain_continuation and prev_active_topic in ["sql", "database"] and "join" in c_lower:
            resolved = f"How do I join two tables in SQL?"
        elif has_pronoun_reference:
            resolved = re.sub(r"\b(it|this|that)\b", active_topic, corrected, flags=re.IGNORECASE)
        else:
            resolved = f"{corrected} for {active_topic}"

    return {
        "original_query": query,
        "corrected_query": corrected,
        "resolved_query": resolved,
        "active_topic": active_topic,
        "is_followup": is_followup
    }


def classify_intent(query: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Analyzes query semantics, typo-corrected text, and conversation context
    to determine the exact user intent and target language.
    """
    if not query:
        return {
            "primary_intent": "CONCEPT_EXPLANATION",
            "language": None,
            "is_why": False,
            "is_complexity": False,
            "is_time_complexity": False,
            "is_space_complexity": False,
            "is_code": False,
            "is_recursive": False,
            "is_comparison": False,
            "is_debugging": False,
            "is_practice": False,
            "resolved_query": "",
            "active_topic": None
        }

    context_info = resolve_contextual_query(query, history)
    effective_query = context_info["resolved_query"]
    q = effective_query.strip().lower()
    lang = detect_language(effective_query)

    is_recursive = any(k in q for k in ["recursive", "recursion", "recursively"])

    is_space_complexity = any(k in q for k in [
        "space complexity", "auxiliary space", "memory complexity", "space of", "space analysis"
    ]) or ("space" in q and ("complexity" in q or "explain" in q))

    is_time_complexity = any(k in q for k in [
        "time complexity", "runtime complexity", "time of", "time analysis"
    ]) or ("time" in q and ("complexity" in q or "explain" in q))

    is_complexity = is_space_complexity or is_time_complexity or any(k in q for k in [
        "o(log n)", "o(n)", "o(1)", "o(n^2)", "o(n log n)", "o(log_2", "o(log", "o (log n)",
        "big o", "big-o", "asymptotic", "complexity", "logarithmic", "why o(", "why is it o("
    ]) or bool(re.search(r"\bo\s*\(\s*[a-z0-9^ _-]+\s*\)", q))

    is_why = (
        q.startswith("why ") or "why is" in q or "why does" in q or "why must" in q or
        "why should" in q or "reason why" in q or "why can" in q or "why are" in q or
        "why require" in q or "why need" in q or
        "why stateless" in q or "why infinite" in q
    )

    is_comparison = any(k in q for k in [
        "compare", "difference between", "differences between", " vs ", " vs. ", "versus",
        "how does it differ", "better than", "different from"
    ]) or (q.startswith("vs ") or q.startswith("difference "))

    is_debugging = any(k in q for k in [
        "debug", "fix this", "why is this failing", "error in this", "find the bug",
        "compile error", "nullpointerexception", "stack overflow", "typeerror", "type error",
        "how do i fix", "how to fix", "fix a", "fix python"
    ])

    is_practice = any(k in q for k in [
        "problems", "practice questions", "exercises", "leetcode", "interview questions",
        "give me 5", "give me some problems", "coding questions"
    ])

    # True code request check (must explicitly ask for code/implementation, not just naming a language in "what is java")
    explicit_code_words = ["code", "implementation", "implement", "write a program", "write code", "program for", "syntax", "snippet", "function to", "class for", "with an example", "java code", "python code", "write "]
    is_code = any(k in q for k in explicit_code_words) or (lang is not None and any(k in q for k in ["example", "show", "give me", "write", "how to write", "in java", "in python", "in c++"]))

    # Determine primary intent with strict priority ordering
    if is_debugging:
        primary_intent = "CODE_DEBUGGING"
    elif is_practice:
        primary_intent = "PRACTICE_PROBLEMS"
    elif is_recursive and is_code:
        primary_intent = "RECURSIVE_IMPLEMENTATION"
    elif is_comparison:
        primary_intent = "COMPARISON"
    elif is_space_complexity and not is_time_complexity:
        primary_intent = "SPACE_COMPLEXITY"
    elif is_time_complexity and not is_space_complexity:
        primary_intent = "TIME_COMPLEXITY"
    elif is_complexity:
        primary_intent = "COMPLEXITY_ANALYSIS"
    elif is_why:
        primary_intent = "WHY_EXPLANATION"
    elif is_code:
        primary_intent = "CODE_EXAMPLE"
    else:
        primary_intent = "CONCEPT_EXPLANATION"

    return {
        "primary_intent": primary_intent,
        "language": lang,
        "is_why": is_why,
        "is_complexity": is_complexity,
        "is_time_complexity": is_time_complexity,
        "is_space_complexity": is_space_complexity,
        "is_code": is_code,
        "is_recursive": is_recursive,
        "is_comparison": is_comparison,
        "is_debugging": is_debugging,
        "is_practice": is_practice,
        "original_query": query,
        "corrected_query": context_info["corrected_query"],
        "resolved_query": effective_query,
        "active_topic": context_info["active_topic"],
        "is_followup": context_info["is_followup"]
    }
