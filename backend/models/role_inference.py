"""
role_inference.py
=================
Transparent, rule-based target-role inference from resume text.

Returns a dict with:
  target_role          : str | None
  target_role_source   : "user_selected" | "resume_explicit" | "resume_inferred" | "not_found"
  target_role_confidence : float  (0.0 – 1.0)
  target_role_unclear  : bool     (True → show role selector in UI)

Design principles
-----------------
* No ML model / pickle required — purely keyword-weight scoring.
* Requires ≥ 2 distinct corroborating signals before committing to a role.
* Confidence threshold: ≥ 0.45 to emit a role; otherwise → unclear.
* Multiple signals: core skills (weight 3×), supporting skills (1.5×),
  project text (3×), education/domain keywords (2×).
* Never returns assessment-mode labels as a target role.
"""

import re
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Assessment-mode labels that must NEVER appear as target roles
ASSESSMENT_MODE_LABELS: frozenset = frozenset([
    "resume baseline assessment",
    "general resume quality",
    "resume-only analysis",
    "baseline assessment",
    "target position",
    "ats evaluation",
    "resume quality assessment",
])

# Explicit objective / desired-role patterns (checked first)
OBJECTIVE_PATTERNS: List[re.Pattern] = [
    # "Seeking a position as Software Engineer"
    re.compile(
        r'(?:seeking|looking for|applying for|interested in|aspiring to be|desire to work as?|'
        r'objective[:\s]+.*?(?:as|position as|role as|become))[:\s]+([A-Za-z][A-Za-z\s/]+)',
        re.IGNORECASE
    ),
    # "Career objective: Software Engineer"
    re.compile(
        r'(?:career objective|career goal|professional objective|job objective)[:\s]+([A-Za-z][A-Za-z\s/]+)',
        re.IGNORECASE
    ),
    # Headline "Name - Role" or "Name | Role" already handled in resume_parser but
    # we check summary/objective section text here too
    re.compile(
        r'(?:summary|profile|about me)[:\s]+.*?(?:experienced|skilled|passionate|motivated)\s+([A-Za-z\s]+(?:developer|engineer|analyst|scientist|architect|designer|specialist))',
        re.IGNORECASE
    ),
]

# Role taxonomy: role_id → display name
ROLE_DISPLAY: Dict[str, str] = {
    "ml_engineer":       "Machine Learning Engineer",
    "data_scientist":    "Data Scientist",
    "data_analyst":      "Data Analyst",
    "backend":           "Backend Developer",
    "frontend":          "Frontend Developer",
    "fullstack":         "Full Stack Developer",
    "devops":            "DevOps Engineer",
    "software_engineer": "Software Engineer",
    "android":           "Android Developer",
    "ios":               "iOS Developer",
    "nlp_engineer":      "NLP / AI Engineer",
}

# Signal definitions per role
# Format: (keyword_or_phrase, weight)
# Weights: core skill = 3, supporting skill = 1.5, education/domain = 2, project keyword = 3
ROLE_SIGNALS: Dict[str, List[Tuple[str, float]]] = {
    "ml_engineer": [
        # Core skills
        ("machine learning", 3.0), ("deep learning", 3.0), ("neural network", 3.0),
        ("pytorch", 3.0), ("tensorflow", 3.0), ("keras", 3.0),
        # Supporting skills
        ("scikit-learn", 1.5), ("sklearn", 1.5), ("numpy", 1.5), ("pandas", 1.5),
        ("xgboost", 1.5), ("lightgbm", 1.5), ("model training", 1.5),
        ("model deployment", 1.5), ("mlflow", 1.5), ("feature engineering", 1.5),
        ("hyperparameter", 1.5), ("gradient descent", 1.5),
        # Education/domain
        ("machine learning engineer", 2.0), ("ai engineer", 2.0),
        ("artificial intelligence", 2.0), ("computer vision", 2.0),
        # Project keywords
        ("trained a model", 3.0), ("built a classifier", 3.0), ("object detection", 3.0),
        ("image classification", 3.0), ("model accuracy", 3.0),
        ("convolutional", 3.0), ("lstm", 3.0), ("transformer", 3.0),
        ("fine-tuning", 3.0), ("inference pipeline", 3.0),
    ],
    "data_scientist": [
        ("data science", 3.0), ("statistical analysis", 3.0), ("hypothesis testing", 3.0),
        ("regression", 3.0), ("clustering", 3.0), ("dimensionality reduction", 3.0),
        ("pandas", 1.5), ("numpy", 1.5), ("matplotlib", 1.5), ("seaborn", 1.5),
        ("a/b testing", 2.0), ("exploratory data analysis", 2.0), ("eda", 2.0),
        ("data science", 2.0), ("statistics", 2.0), ("probability", 2.0),
        ("data analysis project", 3.0), ("customer segmentation", 3.0),
        ("churn prediction", 3.0), ("recommendation system", 3.0),
        ("correlation", 2.0), ("distribution", 2.0),
    ],
    "data_analyst": [
        ("data analyst", 3.0), ("sql", 3.0), ("power bi", 3.0), ("tableau", 3.0),
        ("excel", 1.5), ("pivot table", 1.5), ("data visualization", 1.5),
        ("business intelligence", 2.0), ("reporting", 2.0), ("dashboard", 2.0),
        ("kpi", 2.0), ("metrics", 1.5),
        ("sales analysis", 3.0), ("market analysis", 3.0), ("data reporting", 3.0),
        ("google analytics", 1.5), ("looker", 1.5),
    ],
    "backend": [
        ("rest api", 3.0), ("rest apis", 3.0), ("fastapi", 3.0), ("django", 3.0), ("flask", 3.0),
        ("spring boot", 3.0), ("node.js", 3.0), ("express", 2.0),
        ("postgresql", 1.5), ("mysql", 1.5), ("mongodb", 1.5), ("redis", 1.5),
        ("java", 1.5), ("jwt", 1.5),
        ("microservices", 2.0), ("api development", 2.0), ("backend", 2.0),
        ("server-side", 2.0), ("graphql", 1.5),
        ("built a rest api", 3.0), ("developed backend", 3.0), ("api endpoint", 3.0),
        ("authentication", 2.0), ("authorization", 2.0),
    ],
    "frontend": [
        ("react", 3.0), ("vue", 3.0), ("angular", 3.0), ("next.js", 3.0),
        ("html", 2.0), ("css", 2.0), ("javascript", 2.0), ("typescript", 2.0),
        ("tailwind", 1.5), ("sass", 1.5), ("webpack", 1.5), ("redux", 1.5),
        ("ui development", 2.0), ("web design", 2.0), ("frontend", 2.0),
        ("responsive design", 2.0), ("user interface", 2.0),
        ("built a ui", 3.0), ("designed the frontend", 3.0), ("component library", 3.0),
    ],
    "fullstack": [
        ("full stack", 3.0), ("fullstack", 3.0), ("mern", 3.0), ("mean", 3.0),
        ("react", 1.5), ("node.js", 1.5), ("fastapi", 1.5),
        ("postgresql", 1.5), ("mongodb", 1.5),
        ("full-stack developer", 2.0), ("end-to-end development", 2.0),
        ("built the frontend and backend", 3.0), ("full-stack project", 3.0),
        ("both frontend and backend", 3.0),
    ],
    "devops": [
        ("docker", 3.0), ("kubernetes", 3.0), ("ci/cd", 3.0), ("jenkins", 3.0),
        ("aws", 2.0), ("gcp", 2.0), ("azure", 2.0), ("terraform", 3.0),
        ("ansible", 2.0), ("helm", 2.0), ("linux", 1.5), ("bash", 1.5),
        ("devops", 2.0), ("site reliability", 2.0), ("sre", 2.0),
        ("infrastructure as code", 3.0), ("deployment pipeline", 3.0),
        ("container orchestration", 3.0), ("monitoring", 2.0), ("prometheus", 2.0),
    ],
    "software_engineer": [
        ("data structures", 3.0), ("algorithms", 3.0), ("object-oriented", 2.0),
        ("oop", 2.0), ("system design", 2.0), ("software development", 2.0),
        ("java", 2.0), ("c++", 2.0), ("python", 1.5), ("go", 1.5),
        ("competitive programming", 3.0), ("leetcode", 3.0), ("problem solving", 2.0),
        ("software engineer", 2.0), ("sde", 2.0),
        ("implemented an algorithm", 3.0), ("optimized performance", 3.0),
    ],
    "android": [
        ("android", 3.0), ("kotlin", 3.0), ("jetpack compose", 3.0),
        ("android studio", 3.0), ("java android", 2.0),
        ("retrofit", 2.0), ("room database", 2.0), ("mvvm android", 2.0),
        ("google play", 2.0), ("mobile app", 2.0),
        ("built an android app", 3.0), ("published on play store", 3.0),
    ],
    "ios": [
        ("ios", 3.0), ("swift", 3.0), ("swiftui", 3.0), ("xcode", 3.0),
        ("uikit", 2.0), ("core data", 2.0), ("app store", 2.0),
        ("built an ios app", 3.0), ("published on app store", 3.0),
    ],
    "nlp_engineer": [
        ("nlp", 3.0), ("natural language processing", 3.0),
        ("llm", 3.0), ("large language model", 3.0), ("gpt", 3.0),
        ("bert", 3.0), ("transformer", 2.0), ("hugging face", 3.0),
        ("rag", 3.0), ("retrieval augmented generation", 3.0),
        ("text classification", 3.0), ("sentiment analysis", 3.0),
        ("named entity recognition", 3.0), ("ner", 2.0),
        ("langchain", 2.0), ("openai api", 2.0),
        ("chatbot", 2.0), ("question answering", 3.0),
        ("generative ai", 2.0), ("fine-tuning llm", 3.0),
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Lowercase, collapse whitespace, keep printable chars."""
    return re.sub(r'\s+', ' ', text.lower()).strip()


def _is_valid_explicit_role(role_str: str) -> bool:
    """Returns True if the string is a meaningful job title and not an assessment label."""
    if not role_str or not role_str.strip():
        return False
    stripped = role_str.strip()
    if stripped.lower() in ASSESSMENT_MODE_LABELS:
        return False
    # Must be 2-6 words, no email/URL/digits
    words = stripped.split()
    if not (2 <= len(words) <= 7):
        return False
    if re.search(r'[@:/\\0-9]', stripped):
        return False
    return True


def _extract_explicit_role(text: str) -> Optional[str]:
    """
    Try to extract an explicitly stated desired role from objective/summary text.
    Returns the role string if found, else None.
    """
    for pattern in OBJECTIVE_PATTERNS:
        m = pattern.search(text)
        if m:
            candidate = m.group(1).strip().rstrip('.,;')
            # Trim to first 6 words
            candidate = ' '.join(candidate.split()[:6])
            if _is_valid_explicit_role(candidate):
                return candidate
    return None


def _score_roles(text_lower: str) -> Dict[str, Tuple[float, int]]:
    """
    Score each role by summing weights of matching keywords.
    Returns {role_id: (raw_score, distinct_signal_count)}
    """
    scores: Dict[str, Tuple[float, int]] = {}
    for role_id, signals in ROLE_SIGNALS.items():
        raw_score = 0.0
        matched_count = 0
        for keyword, weight in signals:
            if keyword in text_lower:
                raw_score += weight
                matched_count += 1
        scores[role_id] = (raw_score, matched_count)
    return scores


def _normalize_confidence(raw_score: float, max_possible: float = 30.0) -> float:
    """
    Normalize raw score to 0–1 scale using a soft cap.
    max_possible is an approximate upper bound for a well-signalled resume.
    """
    if raw_score <= 0:
        return 0.0
    normalized = raw_score / max_possible
    return round(min(normalized, 1.0), 3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def infer_target_role(
    resume_text: str,
    explicit_role: Optional[str] = None,
) -> Dict:
    """
    Infer target role from resume text.

    Parameters
    ----------
    resume_text  : Full extracted text from the resume.
    explicit_role: Role explicitly selected by the user in the UI (highest priority).

    Returns
    -------
    {
      "target_role":           str | None,
      "target_role_source":    "user_selected" | "resume_explicit" | "resume_inferred" | "not_found",
      "target_role_confidence": float,   # 0.0 – 1.0
      "target_role_unclear":   bool,
    }
    """
    # ── Priority 1: User-selected role ──────────────────────────────────────
    if explicit_role and _is_valid_explicit_role(explicit_role):
        return {
            "target_role":            explicit_role.strip(),
            "target_role_source":     "user_selected",
            "target_role_confidence": 1.0,
            "target_role_unclear":    False,
        }

    if not resume_text or not resume_text.strip():
        return {
            "target_role":            None,
            "target_role_source":     "not_found",
            "target_role_confidence": 0.0,
            "target_role_unclear":    True,
        }

    text_lower = _clean_text(resume_text)

    # ── Priority 2: Explicit statement in resume ─────────────────────────────
    explicit = _extract_explicit_role(text_lower)
    if explicit and _is_valid_explicit_role(explicit):
        # Compute a confidence based on how well a role is signalled in the rest
        scores = _score_roles(text_lower)
        best_score = max((v[0] for v in scores.values()), default=0.0)
        conf = max(0.85, _normalize_confidence(best_score))
        return {
            "target_role":            explicit.title(),
            "target_role_source":     "resume_explicit",
            "target_role_confidence": min(conf, 0.98),
            "target_role_unclear":    False,
        }

    # ── Priority 3: Signal-based inference ──────────────────────────────────
    scores = _score_roles(text_lower)

    # Filter to roles with ≥ 2 distinct matching signals
    candidates = {
        role_id: (raw, cnt)
        for role_id, (raw, cnt) in scores.items()
        if cnt >= 2
    }

    if not candidates:
        return {
            "target_role":            None,
            "target_role_source":     "not_found",
            "target_role_confidence": 0.0,
            "target_role_unclear":    True,
        }

    # Pick the top-scoring candidate
    best_role_id = max(candidates, key=lambda r: candidates[r][0])
    best_raw, best_cnt = candidates[best_role_id]

    # Dynamic confidence normalization:
    # A role with ≥5 distinct signals and a clear lead is treated as high-confidence.
    # We use a dynamic soft cap: max(20.0, best_raw * 1.5) to avoid penalising
    # focused resumes that lack keyword redundancy.
    dynamic_cap = max(20.0, best_raw * 1.5)
    confidence = _normalize_confidence(best_raw, max_possible=dynamic_cap)

    if confidence < 0.45:
        return {
            "target_role":            None,
            "target_role_source":     "not_found",
            "target_role_confidence": confidence,
            "target_role_unclear":    True,
        }

    # Secondary check: if another competing specialized role is within 80% of best, flag as ambiguous
    sorted_items = sorted(candidates.items(), key=lambda x: x[1][0], reverse=True)
    if best_role_id != "software_engineer":
        competitors = [item for item in sorted_items[1:] if item[0] != "software_engineer"]
    else:
        competitors = sorted_items[1:]

    if competitors:
        second_role_id, (second_raw, second_cnt) = competitors[0]
        # Ambiguity triggers when competing specialized role is within 80% and lead isn't dominant
        if second_raw >= best_raw * 0.80 and confidence < 0.75 and best_cnt < 6:
            return {
                "target_role":            ROLE_DISPLAY[best_role_id],
                "target_role_source":     "resume_inferred",
                "target_role_confidence": round(confidence * 0.85, 3),
                "target_role_unclear":    True,
            }

    return {
        "target_role":            ROLE_DISPLAY[best_role_id],
        "target_role_source":     "resume_inferred",
        "target_role_confidence": confidence,
        "target_role_unclear":    False,
    }
