"""
tech_knowledge.py — Curated Technical Knowledge Base & Intent-Aware Grounding

Provides:
  1. Comprehensive technology domain validation with typo & context awareness (is_technical_query)
  2. Broad technical coverage across DSA, Languages, Frameworks, DBs, OS, Networks, DevOps, Cloud, AI/ML/LLMs
  3. Intent-aware local fallback generator with clean plain-text math and zero fake citations
"""

import re
from typing import Dict, Any, Optional, List
from rag.intent_classifier import normalize_and_correct_typos, extract_active_topic_from_history

# Core Technical Vocabulary
TECH_KEYWORDS = {
    # Languages & Runtimes
    "python", "java", "c", "c++", "cpp", "c#", "csharp", "golang", "go", "rust", "javascript", "typescript",
    "js", "ts", "html", "html5", "css", "css3", "flexbox", "grid", "ruby", "php", "swift", "kotlin", "scala",
    "r", "dart", "node", "nodejs", "deno", "bun", "jvm", "jre", "jdk", "pypy", "v8", "assembly", "pointer", "pointers",

    # Frameworks & Libraries
    "react", "reactjs", "vue", "angular", "svelte", "nextjs", "nuxt", "fastapi", "flask", "django",
    "spring", "spring boot", "springboot", "express", "expressjs", "nest", "nestjs", "asp.net", "laravel",
    "tailwind", "bootstrap", "redux", "graphql", "rest", "rest api", "rest apis", "restful", "grpc", "protobuf",
    "useeffect", "usestate", "usememo", "usecallback",

    # Databases & Storage
    "sql", "mysql", "postgres", "postgresql", "sqlite", "mongodb", "mongo", "redis", "cassandra",
    "dynamodb", "elasticsearch", "neo4j", "mariadb", "oracle", "database", "databases", "dbms", "rdbms", "nosql",
    "acid", "transaction", "indexing", "indexes", "index", "b-tree", "btree", "normalization", "1nf", "2nf", "3nf", "bcnf",
    "sharding", "replication", "partitioning", "connection pool", "orm", "sqlalchemy", "hibernate", "prisma",
    "join", "joins", "inner join", "left join", "right join", "outer join", "table", "tables", "query", "queries",
    "select", "where", "group by", "order by", "having",

    # Data Structures & Algorithms
    "dsa", "data structure", "data structures", "algorithm", "algorithms", "array", "arraylist", "linked list",
    "linkedlist", "stack", "queue", "priority queue", "priorityqueue", "deque", "hashmap", "hash table", "hashtable",
    "hash set", "hashset", "treemap", "treeset", "vector", "tree", "binary tree", "bst", "binary search tree",
    "avl", "red-black tree", "trie", "heap", "graph", "bfs", "dfs", "dijkstra", "bellman-ford", "kruskal", "prim",
    "topological sort", "toposort", "dynamic programming", "dp", "memoization", "tabulation", "recursion", "recursive",
    "greedy", "backtracking", "binary search", "two pointer", "sliding window", "sorting", "quicksort", "mergesort",
    "heapsort", "time complexity", "space complexity", "complexity", "big o", "big-o", "asymptotic", "linear search",

    # Object Oriented Programming (OOP)
    "oop", "oops", "object oriented", "polymorphism", "inheritance", "encapsulation", "abstraction",
    "interface", "abstract class", "design pattern", "solid", "factory pattern", "singleton",

    # Operating Systems & Concurrency
    "operating system", "operating systems", "os", "process", "thread", "threads", "multithreading", "concurrency",
    "parallelism", "deadlock", "deadlocks", "semaphore", "mutex", "lock", "race condition", "critical section",
    "cpu scheduling", "round robin", "context switch", "paging", "segmentation", "virtual memory",
    "mmu", "cache", "thrashing", "kernel", "system call", "posix", "ipc",

    # Computer Networks
    "network", "networking", "computer networks", "osi", "osi model", "tcp", "udp", "ip", "ipv4", "ipv6", "dns",
    "http", "https", "tls", "ssl", "handshake", "tcp handshake", "socket", "websocket",
    "router", "switch", "subnet", "cidr", "nat", "vpn", "cors", "cookie", "session", "jwt",
    "oauth", "oauth2", "cdn", "load balancer", "proxy", "reverse proxy", "stateless",

    # System Design & Architecture
    "system design", "microservice", "microservices", "monolith", "scalability", "high availability",
    "cap theorem", "load balancing", "rate limit", "rate limiting", "circuit breaker", "api gateway",
    "message queue", "kafka", "rabbitmq", "event driven", "cqrs", "caching", "cache aside",
    "write through", "consistent hashing", "idempotency",

    # DevOps, Tools & Cloud
    "docker", "container", "containers", "containerization", "kubernetes", "k8s", "pod", "pods", "deployment",
    "service discovery", "ingress", "helm", "statefulset", "daemonset", "configmap",
    "git", "github", "gitlab", "bitbucket", "rebase", "merge", "commit", "branch",
    "ci/cd", "jenkins", "github actions", "gitlab ci", "aws", "azure", "gcp", "ec2", "s3",
    "lambda", "serverless", "terraform", "ansible", "nginx", "apache", "linux", "bash", "shell",

    # AI / Machine Learning / Deep Learning / LLMs / RAG
    "machine learning", "ml", "deep learning", "dl", "ai", "artificial intelligence", "neural network", "neural networks",
    "cnn", "rnn", "lstm", "transformer", "transformers", "attention", "self-attention", "bert", "gpt", "llm", "llms",
    "rag", "retrieval augmented generation", "retrieval-augmented generation", "embeddings", "embedding",
    "vector database", "vector search", "cosine similarity", "faiss", "overfitting", "underfitting",
    "bias-variance", "regularization", "gradient descent", "sgd", "adam", "backpropagation",
    "loss function", "cross-entropy", "precision", "recall", "f1-score", "roc-auc", "confusion matrix",
    "hyperparameter", "fine-tuning", "prompt engineering", "supervised", "unsupervised", "nlp", "computer vision", "cv",
    "generative ai", "genai", "svm", "random forest", "decision tree", "kmeans", "clustering",

    # General Engineering & Debugging
    "debug", "debugging", "bug", "nullpointerexception", "segmentation fault", "stack overflow",
    "typeerror", "type error", "valueerror", "indexerror", "keyerror", "syntaxerror",
    "memory leak", "garbage collection", "gc", "compiler", "runtime", "unit test", "integration test"
}

NON_TECH_PATTERNS = [
    r"\b(recipe|cook|bake|cake|food|dinner|pizza|salad|soup)\b",
    r"\b(weather|temperature|rain|climate|forecast)\b",
    r"\b(movie|cinema|actor|actress|hollywood|bollywood|song|music|guitar)\b",
    r"\b(football|soccer|cricket|nba|match|score|ipl|world cup|olympics)\b",
    r"\b(travel|flight|hotel|vacation|tourism|visa|capital of)\b",
    r"\b(medicine|symptom|doctor|disease|pill|fever|cough)\b",
    r"\b(politics|president|election|minister|senator|parliament)\b",
    r"\b(joke|story|poem|riddle|horoscope|astrology)\b"
]


def is_technical_query(query: str, history: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    Checks if user query belongs strictly to the technology domain,
    with support for typo normalization, short acronyms, and conversation context.
    """
    if not query or not query.strip():
        return False

    # 1. Normalize typos
    cleaned = normalize_and_correct_typos(query).lower()

    # 2. Reject explicit non-technical patterns
    for pat in NON_TECH_PATTERNS:
        if re.search(pat, cleaned):
            return False

    # 3. If query is a conversational follow-up and active tech topic exists in history, accept as technical
    active_topic = extract_active_topic_from_history(history)
    if active_topic:
        followup_cues = [
            "time", "space", "complexity", "why", "code", "java", "python", "how", "example",
            "loop", "stateless", "recursive", "compare", "diff", "difference", "join", "table", "tables", "query"
        ]
        words_in_query = cleaned.split()
        if len(words_in_query) <= 10 and any(c in cleaned for c in followup_cues):
            return True

    # 4. Check standalone short tech acronyms & languages
    raw_tokens = re.findall(r"[a-z0-9+#.-]+", cleaned)
    words = [t.strip(".,;:!?()[]{}") for t in raw_tokens if t.strip(".,;:!?()[]{}")]

    short_tech_tokens = {
        "c", "r", "go", "js", "ts", "os", "db", "ml", "ai", "dl", "cv", "nlp", "llm", "rag", "sql", "css",
        "git", "k8s", "dsa", "oop", "jwt", "api", "tcp", "udp", "ip", "dns", "uri", "url", "ssh", "ssl",
        "tls", "dom", "npm", "pip", "ide", "bst", "bfs", "dfs", "dp", "vm", "pod", "pods"
    }
    for tok in words:
        if tok in short_tech_tokens:
            return True

    # 5. Match tech keywords
    for w in words:
        if w in TECH_KEYWORDS:
            return True

    # 6. Match multi-word phrases
    for kw in TECH_KEYWORDS:
        if " " in kw and kw in cleaned:
            return True

    # 7. Coding syntax symbols & declarations
    coding_symbols = [
        "def ", "class ", "function", "import ", "const ", "let ", "var ", "select ", "from ", "where ",
        "public static void", "public class", "#include", "std::", "=>", "==", "!=", "->", "useeffect", "usestate"
    ]
    for sym in coding_symbols:
        if sym.lower() in cleaned:
            return True

    # 8. Technical question starters
    tech_question_starters = [
        "how to", "how do", "explain", "difference between", "what is", "why use", "compare",
        "when to use", "why is", "why must", "why can", "time complexity", "space complexity",
        "implement", "debug"
    ]
    if any(cleaned.startswith(starter) for starter in tech_question_starters):
        for w in words:
            if len(w) >= 3 and (w in TECH_KEYWORDS or w.endswith("db") or w.endswith("js") or w.endswith("api") or w.endswith("sql")):
                return True

    return False


def get_intent_aware_fallback_answer(query: str, intent_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Synthesizes an intent-specific technical answer when running in local fallback mode.
    Does NOT output generic monolithic articles; tailors content directly to user's question and intent.
    Uses clean Markdown/plain-text formatting for math & complexity expressions.
    """
    if not query:
        return None

    # Use resolved query if available (expanded with active topic)
    effective_q = intent_info.get("resolved_query") or query
    q = effective_q.strip().lower()
    intent = intent_info.get("primary_intent", "CONCEPT_EXPLANATION")
    lang = intent_info.get("language")

    # =========================================================================
    # 1. BINARY SEARCH FAMILY
    # =========================================================================
    if "binary search" in q and "tree" not in q:
        # A. Debugging
        if intent == "CODE_DEBUGGING" or "debug" in q or "fix" in q:
            return {
                "answer": (
                    "### Debugging Binary Search in Java\n\n"
                    "Common bugs in binary search implementations include **integer overflow**, **off-by-one boundary errors**, and **infinite loops**.\n\n"
                    "#### 1. Identified Common Bugs:\n"
                    "- **Integer Overflow:** Using `int mid = (left + right) / 2;` causes overflow when `left + right > Integer.MAX_VALUE`.\n"
                    "- **Infinite Loop / Off-by-One:** Using `left = mid` or `right = mid` instead of `mid + 1` / `mid - 1` when the target is not at `mid`.\n\n"
                    "#### 2. Corrected Java Implementation:\n"
                    "```java\n"
                    "public class BinarySearchCorrected {\n"
                    "    public static int binarySearch(int[] arr, int target) {\n"
                    "        int left = 0;\n"
                    "        int right = arr.length - 1;\n\n"
                    "        while (left <= right) {\n"
                    "            // Safe mid calculation preventing integer overflow\n"
                    "            int mid = left + (right - left) / 2;\n\n"
                    "            if (arr[mid] == target) {\n"
                    "                return mid;\n"
                    "            } else if (arr[mid] < target) {\n"
                    "                left = mid + 1; // Correct boundary advance\n"
                    "            } else {\n"
                    "                right = mid - 1; // Correct boundary advance\n"
                    "            }\n"
                    "        }\n"
                    "        return -1; // Not found\n"
                    "    }\n"
                    "}\n"
                    "```\n\n"
                    "**Fix Explanation:** `left + (right - left) / 2` calculates the identical midpoint algebraically without risking arithmetic overflow."
                ),
                "citations": [],
                "suggested_next_topics": ["Binary Search Edge Cases", "Why Binary Search is O(log n)", "Recursive Binary Search in Java"]
            }

        # B1. Space Complexity Analysis
        if intent == "SPACE_COMPLEXITY" or ("space" in q and ("complexity" in q or "auxiliary" in q or "memory" in q or "explain" in q)):
            return {
                "answer": (
                    "### Space Complexity of Binary Search\n\n"
                    "The space complexity of Binary Search depends on whether it is implemented **iteratively** or **recursively**:\n\n"
                    "#### 1. Iterative Implementation: O(1) Auxiliary Space\n"
                    "- An iterative binary search maintains three pointer variables (`left`, `right`, `mid`) inside a standard `while` loop.\n"
                    "- No dynamic memory or recursive function call frames are created as the input size `n` grows.\n"
                    "- **Auxiliary Space:** **O(1)** (constant extra space, in-place).\n\n"
                    "#### 2. Recursive Implementation: O(log n) Auxiliary Space\n"
                    "- Each recursive call allocates a new stack frame on the call stack to hold arguments, local variables, and return pointers.\n"
                    "- Because the array is divided in half at each step, the recursion depth is at most **log2(n)** levels.\n"
                    "- **Auxiliary Space:** **O(log n)** stack frames on the runtime call stack.\n\n"
                    "#### Summary:\n"
                    "- **Iterative:** O(1) extra space  \n"
                    "- **Recursive:** O(log n) stack space"
                ),
                "citations": [],
                "suggested_next_topics": ["Iterative vs Recursive Binary Search", "Time Complexity of Binary Search", "Binary Search in Java"]
            }

        # B2. Time Complexity Analysis
        if intent in ["TIME_COMPLEXITY", "COMPLEXITY_ANALYSIS"] or "time complexity" in q or ("time" in q and "complexity" in q) or "o(log n)" in q or "complexity" in q or "logarithmic" in q or ("why" in q and ("o(" in q or "log" in q or "fast" in q)):
            return {
                "answer": (
                    "### Time Complexity of Binary Search\n\n"
                    "Binary Search operates by halving the search space at every step, yielding a logarithmic time complexity:\n\n"
                    "- **Best Case: O(1)** — Occurs when the target element is located exactly at the initial middle index (`arr[mid] == target`).\n"
                    "- **Average Case: O(log n)** — The target is found after dividing the search interval roughly log2(n) / 2 times.\n"
                    "- **Worst Case: O(log n)** — Occurs when the target is at the extreme ends or is not present in the array at all.\n\n"
                    "#### Mathematical Derivation:\n"
                    "- Start with `n` elements.\n"
                    "- After step 1: `n / 2` elements remain.\n"
                    "- After step 2: `n / 4` elements remain.\n"
                    "- After `k` steps: `n / (2^k)` elements remain.\n\n"
                    "The search terminates when 1 element remains:\n"
                    "`n / (2^k) = 1` -> `2^k = n` -> `k = log2(n)`\n\n"
                    "Therefore, the maximum number of comparisons needed is **log2(n)**.\n\n"
                    "**Time:** O(log n)  \n"
                    "**Space:** O(1) iterative, O(log n) recursive"
                ),
                "citations": [],
                "suggested_next_topics": ["Space Complexity of Binary Search", "Why Binary Search Requires a Sorted Array", "Binary Search vs Linear Search"]
            }

        # C. Why must array be sorted?
        if "sorted" in q or ("why" in q and ("must" in q or "need" in q or "require" in q)):
            return {
                "answer": (
                    "### Why Binary Search Requires a Sorted Array\n\n"
                    "Binary search relies on the **monotonicity property** (ordered structure) of the array:\n\n"
                    "1. When comparing the target value with the middle element (`arr[mid]`):\n"
                    "   - If `target < arr[mid]`, the sorted order **guarantees** that all elements to the right of `mid` are also strictly greater than `target`.\n"
                    "   - If `target > arr[mid]`, the sorted order **guarantees** that all elements to the left of `mid` are also strictly smaller than `target`.\n\n"
                    "2. This invariant enables the algorithm to safely eliminate (discard) half of the entire remaining search space in **O(1)** time.\n\n"
                    "If the array were **unsorted**, `arr[mid]` provides zero information about the positions of other elements, and discarding either half could cause the target element to be missed."
                ),
                "citations": [],
                "suggested_next_topics": ["Linear Search on Unsorted Data", "Binary Search in Java", "Why Binary Search is O(log n)"]
            }

        # D. Recursive Implementation
        if intent == "RECURSIVE_IMPLEMENTATION" or "recursive" in q:
            return {
                "answer": (
                    "### Recursive Binary Search in Java\n\n"
                    "In recursive binary search, the search boundaries (`left` and `right`) are passed as function arguments until the target is found or `left > right`.\n\n"
                    "```java\n"
                    "public class RecursiveBinarySearch {\n"
                    "    public static int binarySearch(int[] arr, int left, int right, int target) {\n"
                    "        // Base case: element is not present in array\n"
                    "        if (left > right) {\n"
                    "            return -1;\n"
                    "        }\n\n"
                    "        // Prevent integer overflow\n"
                    "        int mid = left + (right - left) / 2;\n\n"
                    "        // Target found at mid\n"
                    "        if (arr[mid] == target) {\n"
                    "            return mid;\n"
                    "        }\n\n"
                    "        // If target is smaller than mid, search left half\n"
                    "        if (target < arr[mid]) {\n"
                    "            return binarySearch(arr, left, mid - 1, target);\n"
                    "        }\n\n"
                    "        // Else target is larger than mid, search right half\n"
                    "        return binarySearch(arr, mid + 1, right, target);\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        int[] arr = {2, 4, 7, 10, 15};\n"
                    "        int target = 10;\n"
                    "        int index = binarySearch(arr, 0, arr.length - 1, target);\n"
                    "        System.out.println(\"Found at index: \" + index); // Output: 3\n"
                    "    }\n"
                    "}\n"
                    "```\n\n"
                    "**Complexity:** O(log n) time, O(log n) auxiliary space on the call stack."
                ),
                "citations": [],
                "suggested_next_topics": ["Iterative vs Recursive Binary Search", "Binary Search vs Linear Search", "Tail Call Optimization"]
            }

        # E. Comparison with Linear Search
        if intent == "COMPARISON" or "linear search" in q or "compare" in q:
            return {
                "answer": (
                    "### Binary Search vs Linear Search\n\n"
                    "| Feature | Linear Search | Binary Search |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **Array Requirement** | Works on unsorted & sorted arrays | Strictly requires a **sorted array** |\n"
                    "| **Time Complexity (Best)** | O(1) (target at index 0) | O(1) (target at middle index) |\n"
                    "| **Time Complexity (Worst/Avg)** | O(n) (scans all elements) | O(log n) (halves search space) |\n"
                    "| **Space Complexity** | O(1) | O(1) iterative, O(log n) recursive |\n"
                    "| **Data Structure Access** | Sequential (works on Linked Lists & Arrays) | Direct random index access (requires Arrays) |\n"
                    "| **Best Use Case** | Small or unsorted datasets | Large, static, or frequently queried sorted data |"
                ),
                "citations": [],
                "suggested_next_topics": ["Why Binary Search is O(log n)", "Ternary Search", "Binary Search in Java"]
            }

        # F. Java Code Example with Walkthrough
        if intent == "CODE_EXAMPLE" or lang == "Java" or "java" in q or "example" in q or "code" in q or "implement" in q:
            return {
                "answer": (
                    "### Binary Search in Java\n\n"
                    "Binary Search finds a target value in a **sorted array** by repeatedly checking the middle element and halving the search space.\n\n"
                    "```java\n"
                    "public class BinarySearch {\n"
                    "    public static int binarySearch(int[] arr, int target) {\n"
                    "        int left = 0;\n"
                    "        int right = arr.length - 1;\n\n"
                    "        while (left <= right) {\n"
                    "            int mid = left + (right - left) / 2;\n\n"
                    "            if (arr[mid] == target) {\n"
                    "                return mid; // Target found\n"
                    "            } else if (arr[mid] < target) {\n"
                    "                left = mid + 1; // Search right half\n"
                    "            } else {\n"
                    "                right = mid - 1; // Search left half\n"
                    "            }\n"
                    "        }\n"
                    "        return -1; // Target not found\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        int[] arr = {2, 4, 7, 10, 15};\n"
                    "        System.out.println(\"Found at index: \" + binarySearch(arr, 10)); // Output: 3\n"
                    "    }\n"
                    "}\n"
                    "```\n\n"
                    "**How it works:**\n"
                    "1. Start with pointers at `left = 0` and `right = arr.length - 1`.\n"
                    "2. Compute `mid` safely using `left + (right - left) / 2` to prevent integer overflow.\n"
                    "3. If `arr[mid] == target`, return `mid`. Otherwise, adjust `left` or `right` to search the remaining half.\n\n"
                    "**Time:** O(log n)  \n"
                    "**Space:** O(1)"
                ),
                "citations": [],
                "suggested_next_topics": ["Why Binary Search is O(log n)", "Recursive Binary Search in Java", "Arrays.binarySearch in Java"]
            }

        # G. Basic Concept Explanation (Default for "What is binary search?")
        return {
            "answer": (
                "### Binary Search\n\n"
                "Binary Search is a searching algorithm used on a **sorted array**.\n\n"
                "It checks the middle element and eliminates half of the remaining search space each time.\n\n"
                "For example, if the target is greater than the middle element, we search only the right half.\n\n"
                "**Time:** O(log n)  \n"
                "**Space:** O(1)"
            ),
            "citations": [],
            "suggested_next_topics": ["Explain Binary Search in Java", "Why Binary Search is O(log n)", "Binary Search vs Linear Search"]
        }

    # =========================================================================
    # 2. JWT (JSON WEB TOKEN) FAMILY & SPRING BOOT
    # =========================================================================
    if "jwt" in q or "json web token" in q:
        # A. How JWT works in Spring Boot
        if "spring" in q or "springboot" in q or "spring boot" in q:
            return {
                "answer": (
                    "### How JWT Works in Spring Boot\n\n"
                    "In a Spring Boot application with Spring Security, JWT authentication is implemented using a filter interceptor and a token utility class.\n\n"
                    "#### Architecture Flow:\n"
                    "1. **Login Request:** Client sends `POST /api/auth/login` with username and password.\n"
                    "2. **Authentication:** `AuthenticationManager` verifies credentials. If valid, `JwtService` creates a signed JWT.\n"
                    "3. **Token Transmission:** Server returns token in response payload.\n"
                    "4. **Per-Request Filter:** `JwtAuthenticationFilter` (extending `OncePerRequestFilter`) intercepts subsequent requests, extracts `Authorization: Bearer <token>`, validates the signature, and sets `SecurityContextHolder.getContext().setAuthentication(...)`.\n\n"
                    "#### Key Components:\n"
                    "- `JwtService`: Token creation (`Jwts.builder()`), claims extraction, signature validation (`Jwts.parserBuilder()`).\n"
                    "- `SecurityFilterChain`: Configures session management to `SessionCreationPolicy.STATELESS`.\n"
                    "- `OncePerRequestFilter`: Guarantees single execution per request dispatch."
                ),
                "citations": [],
                "suggested_next_topics": ["Spring Security Filter Chain", "JWT Refresh Token Rotation", "Why JWT is Stateless"]
            }

        # B. Why is JWT called stateless?
        if "stateless" in q or ("why" in q and ("called" in q or "is" in q or "stateless" in q)):
            return {
                "answer": (
                    "### Why JWT is Called Stateless Authentication\n\n"
                    "JWT authentication is **stateless** because the server **does not store session records** in memory or a database.\n\n"
                    "#### How Statelessness Works:\n"
                    "1. **Self-Contained Payload:** All necessary user identity details (user ID, roles, permissions, expiration) are stored directly inside the token's cryptographically signed payload.\n"
                    "2. **Cryptographic Verification:** When a request arrives, the server verifies the signature using its private secret key. If the signature is valid and the token has not expired, the user is authenticated instantly.\n"
                    "3. **Zero Database Lookups:** The backend does not need to query a session table (or Redis cache) on every incoming API request.\n\n"
                    "#### Key Advantages:\n"
                    "- **Horizontal Scalability:** Any backend instance in a cluster can validate the token without sharing session storage.\n"
                    "- **Decoupled Architecture:** Ideal for distributed microservices, mobile applications, and REST APIs."
                ),
                "citations": [],
                "suggested_next_topics": ["JWT Token Expiration & Refresh Tokens", "JWT vs Session Cookies", "OAuth 2.0 Flow"]
            }

        # C. What is JWT (Concept Definition)
        return {
            "answer": (
                "### JSON Web Token (JWT)\n\n"
                "A **JSON Web Token (JWT)** is an open standard (RFC 7519) for securely transmitting information between parties as a compact, self-contained JSON object.\n\n"
                "#### Structure of a JWT:\n"
                "A JWT consists of three parts separated by dots (`.`):\n"
                "`Header.Payload.Signature`\n\n"
                "1. **Header:** Specifies the token type (`JWT`) and signing algorithm (e.g., `HS256`, `RS256`).\n"
                "2. **Payload:** Contains the claims (e.g., `user_id`, `role`, `exp` expiration timestamp).\n"
                "3. **Signature:** Generated by hashing the encoded header, encoded payload, and a secret key (`HMACSHA256(base64Url(header) + \".\" + base64Url(payload), secret)`).\n\n"
                "#### Standard Flow:\n"
                "Client logs in => Server issues signed JWT => Client attaches token in `Authorization: Bearer <token>` header on subsequent requests."
            ),
            "citations": [],
            "suggested_next_topics": ["Why JWT is Called Stateless Authentication", "JWT Refresh Token Strategy", "JWT vs Session Cookies"]
        }

    # =========================================================================
    # 3. REACT USEEFFECT FAMILY
    # =========================================================================
    if "useeffect" in q or "use effect" in q:
        # A. Why infinite render loop?
        if "infinite" in q or "loop" in q or "re-render" in q or ("why" in q and ("cause" in q or "happen" in q)):
            return {
                "answer": (
                    "### Why React useEffect Can Cause an Infinite Render Loop\n\n"
                    "An infinite render loop occurs when state updates inside `useEffect` continuously trigger re-renders that cause the effect to execute again.\n\n"
                    "#### The Infinite Loop Cycle:\n"
                    "```text\n"
                    "Component Render => useEffect Runs => State Updated (setCount) => Component Re-renders => useEffect Runs Again...\n"
                    "```\n\n"
                    "#### Common Causes & Fixes:\n"
                    "1. **Missing Dependency Array:**\n"
                    "   - *Problem:* `useEffect(() => { setCount(count + 1); });` (runs on *every* render).\n"
                    "   - *Fix:* Provide an empty array for mount-only execution: `useEffect(() => { ... }, []);`.\n"
                    "2. **Updating State Included in Dependencies Without Guards:**\n"
                    "   - *Problem:* `useEffect(() => { setData(fetchData()); }, [data]);`.\n"
                    "   - *Fix:* Use functional state updates: `setCount(prev => prev + 1)` or guard state changes.\n"
                    "3. **Object or Array Dependency Re-creation:**\n"
                    "   - *Problem:* Passing an object/function declared in the component body creates a new memory reference on every render.\n"
                    "   - *Fix:* Wrap the object/function in `useMemo` or `useCallback`."
                ),
                "citations": [],
                "suggested_next_topics": ["React useCallback vs useMemo", "useEffect Cleanup Function", "React Component Lifecycle"]
            }

        # B. Explain React useEffect (Concept)
        return {
            "answer": (
                "### React useEffect Hook\n\n"
                "`useEffect` is a React Hook that allows functional components to perform **side effects** (data fetching, DOM subscriptions, timers, or manual DOM mutations) synchronized with React's rendering lifecycle.\n\n"
                "#### Syntax & Dependency Modes:\n"
                "```javascript\n"
                "useEffect(() => {\n"
                "  // Side effect code (e.g. fetch API, subscribe)\n\n"
                "  return () => {\n"
                "    // Optional cleanup function (e.g. unsubscribe, clearTimeout)\n"
                "  };\n"
                "}, [dependencies]);\n"
                "```\n\n"
                "#### 3 Execution Behaviors:\n"
                "1. **No Dependency Array (`useEffect(fn)`):** Runs after **every** render.\n"
                "2. **Empty Array (`useEffect(fn, [])`):** Runs **once** when the component mounts.\n"
                "3. **With Dependencies (`useEffect(fn, [propA, stateB])`):** Runs on mount and whenever `propA` or `stateB` values change."
            ),
            "citations": [],
            "suggested_next_topics": ["Why useEffect Causes Infinite Render Loops", "React useState Fundamentals", "useEffect vs useLayoutEffect"]
        }

    # =========================================================================
    # 4. RECURSION & SPACE COMPLEXITY
    # =========================================================================
    if "recursion" in q or "recursive" in q:
        # A. Space complexity of recursion
        if "space" in q or "complexity" in q:
            return {
                "answer": (
                    "### Space Complexity of Recursion\n\n"
                    "The space complexity of a recursive algorithm is determined by the **maximum depth of the recursion call stack**:\n\n"
                    "```text\n"
                    "Space Complexity = O(maximum recursion depth) * space per call frame\n"
                    "```\n\n"
                    "#### How Call Stack Memory Works:\n"
                    "1. Every recursive call pushes a new **stack frame** onto the memory call stack to store function parameters, return addresses, and local variables.\n"
                    "2. The stack frame remains allocated in memory until the base condition is reached and the function returns.\n\n"
                    "#### Examples:\n"
                    "- **Linear Recursion (e.g., Factorial, DFS on skewed tree):** Depth is `n` => **O(n)** space complexity.\n"
                    "- **Divide and Conquer (e.g., Recursive Binary Search, Balanced Tree Traversal):** Depth is `log2(n)` => **O(log n)** space complexity.\n"
                    "- **Tail Call Optimization (TCO):** In languages supporting TCO, tail-recursive calls reuse the existing stack frame, reducing space to **O(1)**."
                ),
                "citations": [],
                "suggested_next_topics": ["Tail Call Optimization", "Iterative vs Recursive Trade-offs", "Stack Overflow Prevention"]
            }

        # B. What is recursion (Concept)
        return {
            "answer": (
                "### Recursion in Computer Science\n\n"
                "**Recursion** is a programming technique in which a function calls itself directly or indirectly to solve a smaller subproblem of the original problem.\n\n"
                "#### 2 Essential Parts of Recursion:\n"
                "1. **Base Case:** The stopping condition that returns a direct result without making further recursive calls (prevents infinite recursion / stack overflow).\n"
                "2. **Recursive Step:** The logic that breaks the problem into smaller subproblems and calls the function with modified parameters."
            ),
            "citations": [],
            "suggested_next_topics": ["Space Complexity of Recursion", "Tail Call Optimization", "Recursion vs Iteration"]
        }

    # =========================================================================
    # 5. PROCESS VS THREAD
    # =========================================================================
    if ("process" in q and "thread" in q) or "process and thread" in q or "process vs thread" in q:
        return {
            "answer": (
                "### Process vs Thread in Operating Systems\n\n"
                "| Attribute | Process | Thread |\n"
                "| :--- | :--- | :--- |\n"
                "| **Definition** | An independent program in execution with its own address space. | A lightweight execution unit within a parent process. |\n"
                "| **Memory & Address Space** | Isolated address space (code, data, heap). Does not share memory directly. | Shares code, data, and heap with peer threads; has private stack and registers. |\n"
                "| **Creation & Termination** | Heavyweight. Requires OS process control block (PCB) creation. | Lightweight. Minimal overhead to create and destroy. |\n"
                "| **Context Switching** | Slower (requires switching memory space, page tables, and CPU state). | Faster (switches CPU registers and stack pointer only). |\n"
                "| **Communication** | Requires Inter-Process Communication (IPC: pipes, sockets, shared memory). | Direct communication via shared process memory. |\n"
                "| **Failure Impact** | Crash in one process does not crash other processes. | An unhandled crash in one thread can terminate the entire process. |"
            ),
            "citations": [],
            "suggested_next_topics": ["Concurrency vs Parallelism", "Deadlocks and Race Conditions", "CPU Scheduling Algorithms"]
        }

    # =========================================================================
    # 6. DATABASE INDEXES
    # =========================================================================
    if "index" in q or "indexes" in q or "indexing" in q:
        return {
            "answer": (
                "### Why Database Indexes are Needed\n\n"
                "A **Database Index** is a specialized data structure (typically a **B-Tree** or **B+Tree**) that allows the database engine to find specific rows in **O(log n)** time instead of scanning every row in the table in **O(n)** time.\n\n"
                "#### How Indexing Accelerates Queries:\n"
                "1. **Without Index (Full Table Scan):** To satisfy `WHERE user_id = 45000` on a 1,000,000-row table, the DB engine must read every single disk page from start to finish.\n"
                "2. **With Index (B-Tree Index Scan):** The DB traverses a balanced tree with branching factor ~100-500, locating the pointer to the target table row in just **3-4 disk I/O operations**.\n\n"
                "#### Trade-offs & Best Practices:\n"
                "- **Reads:** Dramatically faster `SELECT` queries with `WHERE`, `JOIN`, `ORDER BY`, and `GROUP BY`.\n"
                "- **Writes:** Slight write penalty on `INSERT`, `UPDATE`, and `DELETE` because the index tree must be updated in sync.\n"
                "- **Types:** **B-Tree** (default for range & equality), **Hash** (exact equality), **GIN** (full-text search and JSONB arrays in PostgreSQL)."
            ),
            "citations": [],
            "suggested_next_topics": ["B-Tree vs GIN Indexes in PostgreSQL", "Query Optimization with EXPLAIN ANALYZE", "Composite Indexes"]
        }

    # =========================================================================
    # 7. DOCKER & CONTAINERS
    # =========================================================================
    if "docker" in q or "container" in q:
        return {
            "answer": (
                "### Docker and Containerization\n\n"
                "**Docker** is an open platform for developing, shipping, and running applications inside lightweight, isolated packages called **containers**.\n\n"
                "#### Containers vs Virtual Machines (VMs):\n"
                "- **Virtual Machines:** Include a full Guest OS on top of a hypervisor, consuming significant RAM and taking minutes to boot.\n"
                "- **Docker Containers:** Share the host OS kernel and use Linux **cgroups** (resource limits) and **namespaces** (isolation) to run isolated user-space processes with near-instant boot times and negligible overhead.\n\n"
                "#### Key Docker Concepts:\n"
                "1. **Dockerfile:** Text recipe with build instructions (e.g. `FROM python:3.11`, `COPY . .`, `CMD [...]`).\n"
                "2. **Image:** Read-only snapshot of the application with its runtime dependencies.\n"
                "3. **Container:** A runnable, live instance of a Docker image."
            ),
            "citations": [],
            "suggested_next_topics": ["Docker Compose Multi-Container Setup", "Docker vs Kubernetes", "Dockerfile Multi-Stage Builds"]
        }

    # =========================================================================
    # 8. KUBERNETES & PODS
    # =========================================================================
    if "kubernetes" in q or "k8s" in q or "pod" in q or "pods" in q:
        return {
            "answer": (
                "### Kubernetes (K8s) Architecture & Pods\n\n"
                "**Kubernetes** is an open-source container orchestration system for automating application deployment, scaling, and management.\n\n"
                "#### What is a Kubernetes Pod?\n"
                "A **Pod** is the smallest and simplest deployable unit in Kubernetes:\n\n"
                "1. **Co-located Containers:** A Pod encapsulates one or more closely coupled containers (such as an application container and a sidecar logging proxy).\n"
                "2. **Shared Network:** All containers in a Pod share the same **IP address**, network namespace, and port space (they can communicate via `localhost`).\n"
                "3. **Shared Storage:** Containers inside a Pod can mount shared storage volumes.\n\n"
                "#### Core Kubernetes Resources:\n"
                "- **Deployment:** Manages declarative Pod scaling, rolling updates, and self-healing.\n"
                "- **Service:** Provides a stable IP, DNS name, and load balancing across dynamic ephemeral Pods (Service Discovery).\n"
                "- **Ingress:** Manages external HTTP/HTTPS routing into cluster services."
            ),
            "citations": [],
            "suggested_next_topics": ["Kubernetes Service Discovery", "Kubernetes Deployments vs StatefulSets", "Docker vs Kubernetes"]
        }

    # =========================================================================
    # 9. RAG (RETRIEVAL-AUGMENTED GENERATION)
    # =========================================================================
    if "rag" in q or "retrieval augmented" in q or "retrieval-augmented" in q:
        return {
            "answer": (
                "### Retrieval-Augmented Generation (RAG)\n\n"
                "**Retrieval-Augmented Generation (RAG)** is an AI framework that grounds Large Language Model (LLM) responses on external, verified knowledge retrieved dynamically at query time.\n\n"
                "#### RAG Architecture Pipeline:\n"
                "1. **Ingestion & Indexing:**\n"
                "   - Documents are split into semantic text chunks.\n"
                "   - Chunks are converted into vector representations using an **Embedding Model** and stored in a **Vector Database** (e.g. Chroma, FAISS, Pinecone).\n"
                "2. **Retrieval:**\n"
                "   - When the user asks a question, the query is embedded into vector space.\n"
                "   - A vector similarity search (cosine similarity / dot product) retrieves the **top-K most relevant chunks**.\n"
                "3. **Augmentation & Generation:**\n"
                "   - The original question and retrieved context chunks are combined in a prompt sent to the LLM.\n"
                "   - The LLM synthesizes an accurate, citation-backed response without hallucinating out-of-date facts."
            ),
            "citations": [],
            "suggested_next_topics": ["What are Vector Embeddings?", "Chunking Strategies in RAG", "Vector Search with Cosine Similarity"]
        }

    # =========================================================================
    # 10. EMBEDDINGS
    # =========================================================================
    if "embedding" in q or "embeddings" in q:
        return {
            "answer": (
                "### Vector Embeddings in AI & NLP\n\n"
                "An **Embedding** is a numerical, dense vector representation of data (text, images, or audio) in high-dimensional space where **geometric proximity reflects semantic similarity**.\n\n"
                "#### How Embeddings Work:\n"
                "1. Words or text chunks with similar meanings are mapped to vectors that point in similar directions in multi-dimensional space (e.g., 384, 768, or 1536 dimensions).\n"
                "2. For example, the vector distance between `\"king\"` and `\"queen\"` is very small, and `\"cat\"` is closer to `\"dog\"` than to `\"airplane\"`.\n\n"
                "#### Calculating Semantic Similarity:\n"
                "Similarity between two embedding vectors $\\vec{u}$ and $\\vec{v}$ is commonly computed using **Cosine Similarity**:\n"
                "```text\n"
                "Cosine Similarity = (u . v) / (||u|| * ||v||)\n"
                "```\n"
                "- A score of `1.0` indicates identical semantic direction, while `0.0` indicates orthogonal/unrelated concepts.\n\n"
                "#### Applications:\n"
                "- Semantic Search & RAG\n"
                "- Recommendation Systems\n"
                "- Clustering and Classification"
            ),
            "citations": [],
            "suggested_next_topics": ["Retrieval-Augmented Generation (RAG)", "Cosine Similarity vs Dot Product", "Transformer Architecture"]
        }

    # =========================================================================
    # 11. OVERFITTING IN MACHINE LEARNING
    # =========================================================================
    if "overfit" in q or "overfitting" in q:
        return {
            "answer": (
                "### Overfitting in Machine Learning\n\n"
                "**Overfitting** occurs when a machine learning model learns the training data too well—capturing noise, outliers, and random fluctuations instead of the underlying general distribution.\n\n"
                "#### Symptoms:\n"
                "- Very high accuracy / low loss on the **Training Set**.\n"
                "- Poor performance / high error on the **Validation / Test Set** (high variance).\n\n"
                "#### Techniques to Prevent Overfitting:\n"
                "1. **Cross-Validation:** Use k-fold cross-validation to tune hyperparameters reliably.\n"
                "2. **Regularization (L1 / L2):** Add penalty terms (Lasso L1 adds $\\lambda \\sum |w_i|$, Ridge L2 adds $\\lambda \\sum w_i^2$) to penalize large weights and simplify the model.\n"
                "3. **Dropout (Neural Networks):** Randomly deactivate a fraction of neurons during training to prevent co-adaptation.\n"
                "4. **Early Stopping:** Halt training when validation loss begins to increase.\n"
                "5. **Data Augmentation:** Increase training dataset size and diversity."
            ),
            "citations": [],
            "suggested_next_topics": ["Bias-Variance Tradeoff", "L1 vs L2 Regularization", "Gradient Descent Optimization"]
        }

    # =========================================================================
    # 12. GRADIENT DESCENT
    # =========================================================================
    if "gradient descent" in q or "gradient" in q:
        return {
            "answer": (
                "### Gradient Descent Optimization\n\n"
                "**Gradient Descent** is an iterative optimization algorithm used to minimize a model's cost / loss function by updating parameters (weights $w$ and biases $b$) in the direction of steepest descent (negative gradient).\n\n"
                "#### Mathematical Update Rule:\n"
                "```text\n"
                "w = w - alpha * (dL / dw)\n"
                "```\n"
                "Where `alpha` is the **learning rate** (step size) and `dL/dw` is the partial derivative of the loss function with respect to weight `w`.\n\n"
                "#### Variants of Gradient Descent:\n"
                "1. **Batch Gradient Descent:** Computes the gradient over the entire dataset at each step (stable convergence, but slow and memory-intensive).\n"
                "2. **Stochastic Gradient Descent (SGD):** Updates weights using one training sample at a time (faster, but noisy oscillations).\n"
                "3. **Mini-Batch Gradient Descent:** Updates weights using small batches (e.g. 32, 64 samples)—the standard practical default in deep learning.\n"
                "4. **Adaptive Optimizers (Adam, RMSprop):** Dynamically adjust the learning rate for each parameter using momentum and squared gradients."
            ),
            "citations": [],
            "suggested_next_topics": ["Learning Rate Tuning", "Adam Optimizer Mechanics", "Backpropagation in Neural Networks"]
        }

    # =========================================================================
    # 13. ARRAYLIST VS LINKEDLIST
    # =========================================================================
    if ("arraylist" in q and "linkedlist" in q) or ("array list" in q and "linked list" in q) or ("compare arraylist" in q):
        return {
            "answer": (
                "### ArrayList vs LinkedList in Java\n\n"
                "| Feature | `ArrayList` | `LinkedList` |\n"
                "| :--- | :--- | :--- |\n"
                "| **Underlying Structure** | Contiguous dynamic array | Doubly linked list of node objects |\n"
                "| **Random Access `get(i)`** | O(1) direct index access | O(n) sequential node traversal |\n"
                "| **Insertion / Deletion** | O(n) due to shifting elements | O(1) once node reference is located |\n"
                "| **Memory Overhead** | Low (contiguous array buffer) | High (stores `prev` and `next` pointers per node) |\n"
                "| **Cache Locality** | Excellent (CPU cache-friendly) | Poor (scattered heap node references) |\n\n"
                "**Recommendation:** `ArrayList` is preferred in almost all practical scenarios due to superior CPU cache locality."
            ),
            "citations": [],
            "suggested_next_topics": ["Java HashMap Internals", "Java CopyOnWriteArrayList", "Vector vs ArrayList"]
        }

    # =========================================================================
    # 14. POINTERS IN C
    # =========================================================================
    if "pointer" in q or "pointers" in q:
        return {
            "answer": (
                "### Pointers in C\n\n"
                "A **Pointer** in C is a variable that stores the **memory address** of another variable.\n\n"
                "#### Core Operators:\n"
                "- **`&` (Address-of Operator):** Retrieves the memory address of a variable (e.g., `&val`).\n"
                "- **`*` (Dereference Operator):** Accesses or modifies the value located at the stored memory address.\n\n"
                "#### Code Example:\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int x = 42;\n"
                "    int *ptr = &x; // ptr holds the memory address of x\n\n"
                "    printf(\"Value of x: %d\\n\", x);            // 42\n"
                "    printf(\"Address of x: %p\\n\", (void*)&x);   // Memory address\n"
                "    printf(\"Dereferenced *ptr: %d\\n\", *ptr);  // 42\n\n"
                "    *ptr = 100; // Modifies x directly through memory\n"
                "    printf(\"New value of x: %d\\n\", x);        // 100\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "**Key Applications:** Dynamic memory allocation (`malloc`/`free`), pointer arithmetic, data structures (linked lists, trees), and pass-by-reference."
            ),
            "citations": [],
            "suggested_next_topics": ["Dynamic Memory Allocation in C", "Pointer Arithmetic", "Dangling Pointers & Memory Leaks"]
        }

    # =========================================================================
    # 15. TCP VS UDP
    # =========================================================================
    if ("tcp" in q and "udp" in q) or "tcp vs udp" in q or "tcp and udp" in q:
        return {
            "answer": (
                "### TCP vs UDP in Computer Networks\n\n"
                "| Feature | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Connection Mode** | Connection-oriented (3-way handshake) | Connectionless (fire and forget) |\n"
                "| **Reliability** | Guaranteed delivery, ACK, retransmission | No delivery guarantee, no retransmissions |\n"
                "| **Ordering** | In-order delivery with sequence numbers | Out-of-order packet delivery possible |\n"
                "| **Speed / Overhead** | Higher overhead (20-60 byte header, congestion control) | Lower overhead (8-byte header, minimal latency) |\n"
                "| **Flow / Congestion Control** | Supported (Sliding window, Slow start) | None |\n"
                "| **Common Use Cases** | HTTP/HTTPS, WebSockets, SSH, File Transfer | Video streaming, VoIP, Gaming, DNS queries |"
            ),
            "citations": [],
            "suggested_next_topics": ["TCP 3-Way Handshake", "OSI Model Layers", "HTTP vs HTTPS Protocols"]
        }

    # =========================================================================
    # 16. POLYMORPHISM IN OOP
    # =========================================================================
    if "polymorphism" in q:
        return {
            "answer": (
                "### Polymorphism in Object-Oriented Programming\n\n"
                "**Polymorphism** (\"many forms\") is an OOP principle that allows entities (objects, methods, or operators) to behave differently based on the calling context or runtime object type.\n\n"
                "#### 2 Types of Polymorphism:\n"
                "1. **Compile-Time (Static) Polymorphism — Method Overloading:**\n"
                "   - Methods share the same name within the same class but have **different parameter signatures**.\n"
                "   - Resolved by the compiler at build time.\n"
                "2. **Runtime (Dynamic) Polymorphism — Method Overriding:**\n"
                "   - A subclass provides a specific implementation of a method declared in its parent class/interface.\n"
                "   - Resolved at runtime using dynamic method dispatch (`vtable`).\n\n"
                "#### Java Example:\n"
                "```java\n"
                "interface Shape {\n"
                "    void draw();\n"
                "}\n\n"
                "class Circle implements Shape {\n"
                "    public void draw() { System.out.println(\"Drawing Circle\"); }\n"
                "}\n\n"
                "class Square implements Shape {\n"
                "    public void draw() { System.out.println(\"Drawing Square\"); }\n"
                "}\n\n"
                "public class PolymorphismDemo {\n"
                "    public static void render(Shape s) {\n"
                "        s.draw(); // Dynamic method dispatch at runtime\n"
                "    }\n"
                "}\n"
                "```"
            ),
            "citations": [],
            "suggested_next_topics": ["Encapsulation vs Abstraction", "Abstract Classes vs Interfaces", "SOLID Principles in OOP"]
        }

    # =========================================================================
    # 17. GIT REBASE VS GIT MERGE
    # =========================================================================
    if ("git" in q and "rebase" in q) or ("rebase" in q and "merge" in q) or "git rebase" in q:
        return {
            "answer": (
                "### Git Rebase vs Git Merge\n\n"
                "Both `git merge` and `git rebase` integrate changes from one branch into another, but they create fundamentally different commit histories.\n\n"
                "| Feature | `git merge` | `git rebase` |\n"
                "| :--- | :--- | :--- |\n"
                "| **History Type** | Non-linear, preserves exact branch chronology. | Linear, flat commit history. |\n"
                "| **Merge Commits** | Creates a new **3-way merge commit**. | Replays feature commits onto the target branch tip (no merge commit). |\n"
                "| **Traceability** | Keeps original commit timestamps and branch context. | Rewrites commit hashes and dates. |\n"
                "| **Golden Rule** | Safe for public, shared branches. | **Never rebase public/shared branches**; only rebase local feature branches. |\n\n"
                "**When to Use:** Use `git merge` when merging a feature branch into `main` to preserve history; use `git rebase` on your local branch before opening a Pull Request to keep the history clean."
            ),
            "citations": [],
            "suggested_next_topics": ["Git Interactive Rebase (git rebase -i)", "Git Cherry-Pick", "Git Branching Strategies"]
        }

    # =========================================================================
    # 18. STACK CONCEPT & IMPLEMENTATION
    # =========================================================================
    if "stack" in q and "overflow" not in q and "full" not in q and "call stack" not in q:
        if "java" in q or "code" in q or "array" in q:
            return {
                "answer": (
                    "### Stack Implementation in Java (Array-Based)\n\n"
                    "A **Stack** is a Last-In, First-Out (LIFO) data structure.\n\n"
                    "```java\n"
                    "public class ArrayStack {\n"
                    "    private int[] arr;\n"
                    "    private int top;\n"
                    "    private int capacity;\n\n"
                    "    public ArrayStack(int size) {\n"
                    "        arr = new int[size];\n"
                    "        capacity = size;\n"
                    "        top = -1;\n"
                    "    }\n\n"
                    "    public void push(int x) {\n"
                    "        if (top == capacity - 1) throw new RuntimeException(\"Stack Overflow\");\n"
                    "        arr[++top] = x;\n"
                    "    }\n\n"
                    "    public int pop() {\n"
                    "        if (top == -1) throw new RuntimeException(\"Stack Underflow\");\n"
                    "        return arr[top--];\n"
                    "    }\n\n"
                    "    public int peek() {\n"
                    "        if (top == -1) throw new RuntimeException(\"Stack is Empty\");\n"
                    "        return arr[top];\n"
                    "    }\n\n"
                    "    public boolean isEmpty() {\n"
                    "        return top == -1;\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        ArrayStack s = new ArrayStack(5);\n"
                    "        s.push(10);\n"
                    "        s.push(20);\n"
                    "        System.out.println(\"Top: \" + s.peek()); // 20\n"
                    "        System.out.println(\"Popped: \" + s.pop()); // 20\n"
                    "    }\n"
                    "}\n"
                    "```\n\n"
                    "**Complexity:** All operations (`push`, `pop`, `peek`) execute in **O(1)** time."
                ),
                "citations": [],
                "suggested_next_topics": ["Stack using LinkedList", "Queue Implementation", "Monotonic Stack Problems"]
            }

        return {
            "answer": (
                "### Stack Data Structure\n\n"
                "A **Stack** is a linear data structure that follows the **Last-In, First-Out (LIFO)** principle.\n\n"
                "#### Core Operations:\n"
                "- **`push(item)`:** Inserts an element onto the top of the stack (O(1)).\n"
                "- **`pop()`:** Removes and returns the top element (O(1)).\n"
                "- **`peek()` / `top()`:** Views the top element without removing it (O(1)).\n"
                "- **`isEmpty()`:** Checks whether the stack contains elements (O(1)).\n\n"
                "#### Practical Applications:\n"
                "- Function call stack and recursion management\n"
                "- Undo/Redo operations in text editors\n"
                "- Expression evaluation and balanced parentheses checking"
            ),
            "citations": [],
            "suggested_next_topics": ["Stack Implementation in Java", "Queue Data Structure", "Monotonic Stack Patterns"]
        }

    # =========================================================================
    # 19. JAVA PROGRAMMING LANGUAGE & PLATFORM
    # =========================================================================
    if "java" in q and "binary search" not in q and "stack" not in q and "arraylist" not in q:
        if "jvm" in q or "jre" in q or "jdk" in q or "architecture" in q or "memory" in q:
            return {
                "answer": (
                    "### Java Platform Architecture: JDK, JRE, and JVM\n\n"
                    "Java's 'Write Once, Run Anywhere' (WORA) capability is enabled by its three-tier platform architecture:\n\n"
                    "1. **JVM (Java Virtual Machine):**\n"
                    "   - Executes platform-independent bytecode (`.class` files).\n"
                    "   - Manages runtime memory: **Heap** (objects), **Stack** (method call frames), and **Metaspace** (class metadata).\n"
                    "   - Performs **JIT (Just-In-Time) compilation** to translate bytecode into native machine instructions at runtime.\n"
                    "   - Manages automatic **Garbage Collection (GC)**.\n\n"
                    "2. **JRE (Java Runtime Environment):**\n"
                    "   - Bundles the JVM plus core Java class libraries (`java.lang`, `java.util`, `java.io`).\n"
                    "   - Required to run pre-compiled Java applications.\n\n"
                    "3. **JDK (Java Development Kit):**\n"
                    "   - Complete developer toolkit containing the JRE, compiler (`javac`), archiver (`jar`), and debugger (`jdb`)."
                ),
                "citations": [],
                "suggested_next_topics": ["Java Garbage Collection Mechanics", "ArrayList vs LinkedList in Java", "Polymorphism in Java"]
            }

        return {
            "answer": (
                "### Java\n\n"
                "Java is a high-level, object-oriented programming language built on the principle of **\"Write Once, Run Anywhere\"** (WORA).\n\n"
                "Code compiles into platform-independent bytecode that runs on any machine with a Java Virtual Machine (JVM).\n\n"
                "**Key features:**\n"
                "- **Object-Oriented:** Supports encapsulation, inheritance, polymorphism, and abstraction.\n"
                "- **Memory Management:** Automatic garbage collection prevents manual memory leaks.\n"
                "- **Ecosystem:** Widely used in enterprise backends (Spring Boot), Android development, and distributed systems."
            ),
            "citations": [],
            "suggested_next_topics": ["JDK vs JRE vs JVM", "ArrayList vs LinkedList in Java", "Spring Boot Architecture"]
        }

    # =========================================================================
    # 20. PYTHON PROGRAMMING LANGUAGE & RUNTIME
    # =========================================================================
    if "python" in q and "binary search" not in q:
        if "gil" in q or "memory" in q or "garbage" in q:
            return {
                "answer": (
                    "### Python Memory Management & Global Interpreter Lock (GIL)\n\n"
                    "CPython uses a hybrid memory management model:\n\n"
                    "1. **Reference Counting:** Every object tracks references pointing to it. When an object's reference count drops to zero, its memory is deallocated immediately.\n"
                    "2. **Generational Garbage Collector:** Periodically detects and collects reference cycles.\n"
                    "3. **Global Interpreter Lock (GIL):** A mutex lock ensuring only one native thread executes Python bytecode at a time.\n\n"
                    "**Tip:** Use `asyncio` for I/O-bound tasks and `multiprocessing` for CPU-bound computations."
                ),
                "citations": [],
                "suggested_next_topics": ["Python Asyncio vs Multithreading", "Python Generators & Iterators", "FastAPI Web Framework"]
            }

        return {
            "answer": (
                "### Python\n\n"
                "Python is a high-level, interpreted programming language known for its clean syntax, readability, and ease of use.\n\n"
                "It is dynamically typed and supports multiple paradigms including object-oriented, procedural, and functional programming.\n\n"
                "**Key features:**\n"
                "- **Readability:** Clean, indentation-based syntax that feels like pseudocode.\n"
                "- **Rich Ecosystem:** Widely used in AI/Machine Learning (PyTorch, TensorFlow, Scikit-learn), data analysis (Pandas, NumPy), and web development (FastAPI, Django).\n"
                "- **Interpreted:** Code executes line-by-line without an explicit compilation step."
            ),
            "citations": [],
            "suggested_next_topics": ["Python Memory Management & GIL", "FastAPI Framework", "Generators and Iterators in Python"]
        }

    # =========================================================================
    # 21. API (APPLICATION PROGRAMMING INTERFACE) & REST
    # =========================================================================
    if "api" in q or "apis" in q or "rest api" in q or "restful" in q:
        return {
            "answer": (
                "### API (Application Programming Interface)\n\n"
                "An API is a set of rules and protocols that allows two software applications to communicate and exchange data.\n\n"
                "For example, a frontend React application calls a backend REST API to retrieve user profiles or submit form data.\n\n"
                "**Common API styles:**\n"
                "- **REST:** Uses standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) with JSON payloads.\n"
                "- **GraphQL:** Lets clients query specifically the fields they need from a single endpoint.\n"
                "- **gRPC:** High-performance, binary RPC communication over HTTP/2 for microservices."
            ),
            "citations": [],
            "suggested_next_topics": ["RESTful API Best Practices", "JWT Authentication in APIs", "GraphQL vs REST APIs"]
        }

    # =========================================================================
    # 22. SQL & RELATIONAL DATABASES
    # =========================================================================
    if "sql" in q or ("database" in q and "index" not in q) or "join" in q or "tables" in q:
        if "join" in q or "tables" in q or "two tables" in q:
            return {
                "answer": (
                    "### SQL Joins: Combining Data from Multiple Tables\n\n"
                    "SQL **JOIN** clauses combine columns from two or more tables based on a related logical key.\n\n"
                    "| Join Type | Description | Result Set |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **`INNER JOIN`** | Returns rows where the join condition matches in **both** tables. | Matched records only |\n"
                    "| **`LEFT JOIN`** | Returns **all** rows from the left table and matched rows from the right table. | Left rows + matched right (NULL if none) |\n"
                    "| **`RIGHT JOIN`** | Returns **all** rows from the right table and matched rows from the left table. | Right rows + matched left (NULL if none) |\n"
                    "| **`FULL OUTER JOIN`** | Returns rows when there is a match in either table. | Union of all records |\n\n"
                    "#### Example:\n"
                    "```sql\n"
                    "SELECT u.name, o.order_id, o.total_amount\n"
                    "FROM users u\n"
                    "INNER JOIN orders o ON u.id = o.user_id\n"
                    "WHERE o.status = 'COMPLETED';\n"
                    "```"
                ),
                "citations": [],
                "suggested_next_topics": ["Database Indexing Strategies", "ACID Properties in Relational Databases", "Database Normalization (1NF, 2NF, 3NF)"]
            }

        return {
            "answer": (
                "### SQL (Structured Query Language)\n\n"
                "SQL is the standard language used to store, query, and manage data in relational database management systems (RDBMS) like PostgreSQL, MySQL, and SQLite.\n\n"
                "**Core operations:**\n"
                "- **Querying:** `SELECT * FROM users WHERE active = true;`\n"
                "- **Modifying:** `INSERT`, `UPDATE`, and `DELETE` to manage records.\n"
                "- **Schema:** `CREATE TABLE`, `ALTER TABLE` to structure data.\n\n"
                "Relational databases organize data into tables with rows and columns, enforce relationships via primary and foreign keys, and guarantee ACID transactions."
            ),
            "citations": [],
            "suggested_next_topics": ["SQL Joins (INNER, LEFT, RIGHT)", "Why Database Indexes are Needed", "ACID Properties in Databases"]
        }

    # =========================================================================
    # 23. FASTAPI BACKEND FRAMEWORK
    # =========================================================================
    if "fastapi" in q:
        return {
            "answer": (
                "### FastAPI Python Web Framework\n\n"
                "**FastAPI** is a modern, high-performance web framework for building REST APIs with Python 3.8+ based on standard Python type hints.\n\n"
                "#### Core Advantages:\n"
                "1. **High Performance:** Built on top of **Starlette** (ASGI toolkit) and **Uvicorn**, delivering performance on par with NodeJS and Go.\n"
                "2. **Automatic Data Validation:** Uses **Pydantic** models for strict schema validation, type casting, and serialization.\n"
                "3. **Native Asynchronous Support:** Built from the ground up for Python's `async` / `await` event loop.\n"
                "4. **Automatic Interactive Documentation:** Generates Swagger UI (`/docs`) and ReDoc (`/redoc`) OpenAPI specifications automatically.\n"
                "5. **Dependency Injection:** Elegant, built-in dependency injection system (`Depends`) for authentication, database sessions, and configuration."
            ),
            "citations": [],
            "suggested_next_topics": ["Pydantic Data Validation in FastAPI", "Asynchronous Programming with Asyncio", "JWT Authentication in FastAPI"]
        }

    # =========================================================================
    # 24. MICROSERVICES VS MONOLITH
    # =========================================================================
    if "microservice" in q or "microservices" in q or "monolith" in q:
        return {
            "answer": (
                "### Microservices Architecture vs Monolithic Architecture\n\n"
                "| Attribute | Monolithic Architecture | Microservices Architecture |\n"
                "| :--- | :--- | :--- |\n"
                "| **Codebase** | Single unified repository and deployment artifact. | Multiple independent repositories and services. |\n"
                "| **Deployment** | All-or-nothing deployment. | Independent, zero-downtime service deployments. |\n"
                "| **Scaling** | Horizontal scaling of the entire application. | Granular scaling of high-demand individual services. |\n"
                "| **Data Storage** | Single centralized database. | Database-per-service pattern for decoupling. |\n"
                "| **Complexity** | Simple debugging, testing, and local development. | Higher operational complexity (network latency, distributed tracing, eventual consistency). |\n"
                "| **Tech Stack** | Homogeneous technology stack. | Polyglot (each service can use the optimal language/database). |"
            ),
            "citations": [],
            "suggested_next_topics": ["API Gateway Pattern", "Event-Driven Architecture with Kafka", "Docker and Kubernetes in Microservices"]
        }

    # =========================================================================
    # 25. MACHINE LEARNING (ML)
    # =========================================================================
    if "machine learning" in q or (("what is ml" in q or q == "ml") and "html" not in q):
        return {
            "answer": (
                "### Machine Learning\n\n"
                "Machine Learning (ML) is a branch of artificial intelligence where algorithms learn patterns from data to make predictions or decisions without being explicitly programmed.\n\n"
                "**Three main types:**\n"
                "- **Supervised Learning:** Learns from labeled data (e.g. classification, regression, spam filters).\n"
                "- **Unsupervised Learning:** Discovers hidden patterns in unlabeled data (e.g. clustering, dimensionality reduction).\n"
                "- **Reinforcement Learning:** Learns by trial and error using rewards and penalties (e.g. robotics, game playing)."
            ),
            "citations": [],
            "suggested_next_topics": ["Overfitting in Machine Learning", "Gradient Descent Optimization", "Deep Learning vs Machine Learning"]
        }

    # =========================================================================
    # 26. NULLPOINTEREXCEPTION (JAVA DEBUGGING)
    # =========================================================================
    if "nullpointerexception" in q or "null pointer" in q or "npe" in q:
        return {
            "answer": (
                "### NullPointerException in Java\n\n"
                "A `NullPointerException` (NPE) occurs when code attempts to access a member or method of an object reference that is currently `null`.\n\n"
                "**Common causes:**\n"
                "- Calling a method on a `null` variable (`str.length()`).\n"
                "- Accessing a field of a `null` object (`user.name`).\n"
                "- Accessing an element of an uninitialized array (`arr[0]`).\n\n"
                "**How to fix it:**\n"
                "1. **Null check before use:**\n"
                "   ```java\n"
                "   if (str != null) {\n"
                "       int len = str.length();\n"
                "   }\n"
                "   ```\n"
                "2. **Use `Optional` in Java 8+:**\n"
                "   ```java\n"
                "   Optional.ofNullable(str).ifPresent(s -> System.out.println(s.length()));\n"
                "   ```\n"
                "3. **Initialize with safe defaults:** Use empty collections or empty strings instead of leaving references `null`."
            ),
            "citations": [],
            "suggested_next_topics": ["Java Optional Class", "Defensive Programming in Java", "Exception Handling in Java"]
        }

    # =========================================================================
    # 27. PYTHON TYPEERROR DEBUGGING
    # =========================================================================
    if "typeerror" in q or "type error" in q or ("python" in q and ("typeerror" in q or "type error" in q or ("fix" in q and ("type" in q or "error" in q)))):
        return {
            "answer": (
                "### How to Fix a Python TypeError\n\n"
                "A `TypeError` in Python is raised when an operation, function call, or expression is applied to an object of an inappropriate type.\n\n"
                "#### Common Causes & Fixes:\n\n"
                "1. **Unsupported Operand Types (Concatenating String and Integer):**\n"
                "   ```python\n"
                "   # Problematic: TypeError: can only concatenate str (not \"int\") to str\n"
                "   age = 25\n"
                "   # message = \"Age: \" + age  # Raises TypeError\n\n"
                "   # Fix 1: Use formatted string literals (f-strings) - Recommended\n"
                "   message = f\"Age: {age}\"\n\n"
                "   # Fix 2: Explicit type conversion with str()\n"
                "   message = \"Age: \" + str(age)\n"
                "   ```\n\n"
                "2. **Calling a Non-Callable Object:**\n"
                "   ```python\n"
                "   # Problematic: TypeError: 'int' object is not callable\n"
                "   total = 100\n"
                "   # result = total()  # Raises TypeError because total is an int, not a function\n\n"
                "   # Fix: Check for variable shadowing (avoid naming variables 'str', 'list', 'dict', 'int')\n"
                "   ```\n\n"
                "3. **Missing or Extra Positional Arguments:**\n"
                "   ```python\n"
                "   def calculate_tax(subtotal, rate):\n"
                "       return subtotal * rate\n\n"
                "   # Problematic: TypeError: calculate_tax() missing 1 required positional argument: 'rate'\n"
                "   # Fix: Provide all required arguments or configure default parameter values\n"
                "   tax = calculate_tax(100.0, 0.08)\n"
                "   ```\n\n"
                "4. **Indexing a Non-Subscriptable Object:**\n"
                "   ```python\n"
                "   # Problematic: TypeError: 'int' object is not subscriptable\n"
                "   number = 98765\n"
                "   # first = number[0]  # Raises TypeError\n\n"
                "   # Fix: Cast to string before indexing\n"
                "   first = str(number)[0]\n"
                "   ```\n\n"
                "#### Systematic Debugging Checklist:\n"
                "1. **Read the Traceback:** Look at the bottom line of the Python traceback to identify the exact file, line number, and operation that failed.\n"
                "2. **Verify Types at Runtime:** Add `print(type(variable))` or use `isinstance(variable, expected_type)` directly before the failing line.\n"
                "3. **Use Type Annotations:** Annotate functions with type hints (`def add(x: int, y: int) -> int:`) and use static checkers like `mypy` to catch type errors before execution."
            ),
            "citations": [],
            "suggested_next_topics": ["Python Traceback Analysis", "Python Type Hinting with Mypy", "Exception Handling with try-except in Python"]
        }

    # =========================================================================
    # 28. STRING REVERSAL (JAVA)
    # =========================================================================
    if "reverse" in q and "string" in q:
        return {
            "answer": (
                "### Reverse a String in Java\n\n"
                "The most concise and idiomatic way to reverse a string in Java is using `StringBuilder`:\n\n"
                "```java\n"
                "public class ReverseString {\n"
                "    public static String reverse(String input) {\n"
                "        if (input == null) return null;\n"
                "        return new StringBuilder(input).reverse().toString();\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        System.out.println(reverse(\"hello\")); // Output: \"olleh\"\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "**Two-Pointer Approach (In-place with char array):**\n"
                "```java\n"
                "public static String reverseTwoPointers(String s) {\n"
                "    if (s == null) return null;\n"
                "    char[] chars = s.toCharArray();\n"
                "    int left = 0, right = chars.length - 1;\n"
                "    while (left < right) {\n"
                "        char temp = chars[left];\n"
                "        chars[left++] = chars[right];\n"
                "        chars[right--] = temp;\n"
                "    }\n"
                "    return new String(chars);\n"
                "}\n"
                "```\n\n"
                "**Time:** O(n)  \n"
                "**Space:** O(n)"
            ),
            "citations": [],
            "suggested_next_topics": ["Palindrome String Check in Java", "StringBuilder vs StringBuffer", "Two Pointers Technique"]
        }

    return None


def get_technical_direct_answer(query: str, intent_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Legacy alias for get_intent_aware_fallback_answer."""
    return get_intent_aware_fallback_answer(query, intent_info or {})
