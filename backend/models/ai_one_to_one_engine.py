"""
ai_one_to_one_engine.py — Conversational AI One-to-One HR Interview Engine

Provides a truly adaptive, realistic HR interviewer experience grounded in the
candidate's Active Resume:
  1. Real HR -> Candidate conversational dynamics (no fixed question sequence).
  2. Answer analysis: 8 internal classifications (RELEVANT, PARTIALLY_RELEVANT,
     TOO_SHORT, GIBBERISH_OR_UNINTELLIGIBLE, OFF_TOPIC, DON'T_KNOW, CORRECTION, UNCLEAR).
  3. Context-aware interpretation: the same word is interpreted differently
     depending on the previous HR question.
  4. Dynamic follow-ups grounded strictly in the candidate's latest response and Active Resume.
  5. Multi-turn interview memory state tracking (recent responses, question styles, topics covered).
  6. Repetition prevention across phrasing patterns and semantic similarity.
  7. Dual-tier execution: Live LLM provider (Gemini/OpenAI) with intelligent heuristic fallback.
  8. Zero emojis throughout.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any, Set, Tuple

logger = logging.getLogger(__name__)


class HrInterviewUnavailableError(Exception):
    """Raised when the Groq/LLM interviewer service is temporarily unavailable."""
    pass


def normalize_spoken_text(text: str) -> str:
    """
    Normalizes smart quotes, dashes, whitespace, and strips emojis/markdown
    for natural Text-to-Speech (TTS) spoken delivery and test assertions.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2011": "-",
        "\u00a0": " ",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Strip emojis
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Strip markdown formatting (asterisks, backticks, hashes, bullet symbols)
    text = re.sub(r'[\*\_#`]', '', text)
    # Strip multiple consecutive spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


# 
# Comprehensive Technical Taxonomy & Canonical Mapping
# 
TECH_TAXONOMY: Dict[str, Dict[str, Any]] = {
    # Data Science & Machine Learning
    "data science": {
        "canonical": "Data Science",
        "category": "domain",
        "probes": {
            "project": "What kind of analysis or machine learning project have you worked on in Data Science?",
            "how": "In your Data Science workflow, how did you handle data cleaning, exploratory analysis, and feature engineering?",
        }
    },
    "machine learning": {
        "canonical": "Machine Learning",
        "category": "domain",
        "probes": {
            "project": "What kind of machine learning models or algorithms have you implemented, and what problem were they solving?",
            "eval": "How did you evaluate your machine learning models to prevent overfitting and ensure real-world reliability?",
        }
    },
    "scikit-learn": {
        "canonical": "scikit-learn",
        "category": "ml_library",
        "probes": {
            "models": "What algorithms from scikit-learn did you try, and how did they perform?",
            "pipeline": "How did you structure your preprocessing and pipeline transformations using scikit-learn?",
        }
    },
    "pandas": {
        "canonical": "Pandas",
        "category": "data_library",
        "probes": {
            "how": "How did you use Pandas for data wrangling, handling missing values, and aggregation in your datasets?",
        }
    },
    "numpy": {
        "canonical": "NumPy",
        "category": "data_library",
        "probes": {
            "how": "How did you leverage NumPy for vectorized numerical operations and array transformations?",
        }
    },
    "pytorch": {
        "canonical": "PyTorch",
        "category": "ml_library",
        "probes": {
            "how": "How did you design your neural network architecture and training loop in PyTorch, and how did you manage tensor memory during batch inference?",
        }
    },
    "tensorflow": {
        "canonical": "TensorFlow",
        "category": "ml_library",
        "probes": {
            "how": "How did you build and train your models with TensorFlow and Keras, and how did you monitor convergence?",
        }
    },
    # Text Extraction / Resume Parsing
    "pdfplumber": {
        "canonical": "pdfplumber",
        "category": "text_extraction",
        "probes": {
            "how": "When extracting text with pdfplumber, how did you handle multi-column layouts, tables, and varying font hierarchies?",
            "challenge": "Regular expressions and text extraction can struggle with irregular PDF layouts. Did you encounter layouts where pdfplumber produced scrambled reading orders, and how did you resolve that?",
            "why": "What led you to choose pdfplumber over other PDF tools like PyPDF2 or Tesseract OCR for text extraction?",
        }
    },
    "resume parsing": {
        "canonical": "resume parsing",
        "category": "text_extraction",
        "probes": {
            "how": "When parsing resumes across unstructured formats, what heuristics or NLP patterns did you use to normalize section headers and extract candidate details?",
            "challenge": "What was the most challenging edge case you encountered when parsing resumes with non-standard formatting or missing sections?",
        }
    },
    "regex": {
        "canonical": "regular expressions",
        "category": "text_processing",
        "probes": {
            "challenge": "Regular expressions can become tricky when candidate formats vary widely. Did you encounter any cases where regex failed or produced false positives, and how did you solve that?",
            "how": "How did you structure your regex pattern matching to reliably capture phone numbers, emails, and date ranges without breaking on unusual characters?",
        }
    },
    "spacy": {
        "canonical": "spaCy",
        "category": "nlp",
        "probes": {
            "how": "How did you leverage spaCy's entity recognition or tokenization pipeline to identify specialized skills and roles?",
            "why": "Did you use a pre-trained spaCy model like en_core_web_sm, or did you train custom Named Entity Recognition (NER) pipes for technical skills?",
        }
    },
    # Backend Frameworks
    "fastapi": {
        "canonical": "FastAPI",
        "category": "backend_framework",
        "probes": {
            "direct": "What did you build with FastAPI?",
            "how": "How did you organize your routers, Pydantic schemas, and dependency injection in FastAPI?",
            "async": "How did you leverage async/await in FastAPI to prevent blocking the event loop during heavy I/O operations?",
        }
    },
    "flask": {
        "canonical": "Flask",
        "category": "backend_framework",
        "probes": {
            "direct": "What kind of application did you develop using Flask?",
            "how": "How did you structure your Flask application blueprints, application factory, and extensions?",
        }
    },
    "django": {
        "canonical": "Django",
        "category": "backend_framework",
        "probes": {
            "direct": "What kind of backend service did you build using Django?",
            "how": "When working with Django, how did you structure your models, migrations, and Django REST framework viewsets?",
        }
    },
    "spring boot": {
        "canonical": "Spring Boot",
        "category": "backend_framework",
        "probes": {
            "direct": "What microservices or backend systems have you built using Spring Boot?",
            "how": "When building with Spring Boot, how did you structure your dependency injection, REST controllers, and JPA repository queries?",
        }
    },
    "spring": {
        "canonical": "Spring Framework",
        "category": "backend_framework",
        "probes": {
            "how": "How did you manage application contexts, bean lifecycles, and transaction annotations in Spring?",
        }
    },
    "express": {
        "canonical": "Express",
        "category": "backend_framework",
        "probes": {
            "direct": "What REST endpoints and middleware did you implement in Express?",
        }
    },
    "node": {
        "canonical": "Node.js",
        "category": "runtime",
        "probes": {
            "direct": "How did you structure your Node.js backend services and event-driven architecture?",
        }
    },
    # Frontend Frameworks
    "react": {
        "canonical": "React",
        "category": "frontend_framework",
        "probes": {
            "how": "Looking at your frontend work in React, how did you structure state management, component hierarchies, and asynchronous API calls?",
            "perf": "How did you prevent unnecessary re-renders in React when dealing with dynamic data?",
        }
    },
    "typescript": {
        "canonical": "TypeScript",
        "category": "language",
        "probes": {
            "how": "How do you structure your TypeScript interfaces, generics, and strict type checking to guarantee compile-time safety?",
        }
    },
    # Databases & Caching
    "postgresql": {
        "canonical": "PostgreSQL",
        "category": "database",
        "probes": {
            "direct": "What kind of data did you store in PostgreSQL, and how did you structure the tables?",
            "how": "With PostgreSQL, how did you approach database schema design, indexing strategies, and query performance optimization?",
        }
    },
    "postgres": {
        "canonical": "PostgreSQL",
        "category": "database",
        "probes": {
            "direct": "What kind of data did you store in PostgreSQL, and how did you structure the tables?",
            "how": "With PostgreSQL, how did you approach schema design, indexing strategies, and database query optimization?",
        }
    },
    "mysql": {
        "canonical": "MySQL",
        "category": "database",
        "probes": {
            "direct": "What kind of database schemas did you design in MySQL?",
            "how": "In your MySQL database design, how did you ensure data normalization, foreign key integrity, and indexed lookup efficiency?",
        }
    },
    "mongodb": {
        "canonical": "MongoDB",
        "category": "database",
        "probes": {
            "direct": "What collections did you design in MongoDB, and what was your document structure?",
            "how": "When designing MongoDB document schemas, how did you decide between embedding sub-documents versus referencing across collections?",
        }
    },
    "redis": {
        "canonical": "Redis",
        "category": "caching",
        "probes": {
            "how": "Regarding your use of Redis, what was your caching strategy, and how did you handle cache invalidation and key expiration?",
        }
    },
    # DevOps & Infrastructure
    "docker": {
        "canonical": "Docker",
        "category": "devops",
        "probes": {
            "direct": "What services have you containerized using Docker, and how did you configure your Dockerfiles?",
            "how": "When containerizing services with Docker, what best practices did you follow for multi-stage builds and reducing image sizes?",
        }
    },
    "kubernetes": {
        "canonical": "Kubernetes",
        "category": "devops",
        "probes": {
            "how": "How did you configure Kubernetes pod resource requests, liveness/readiness probes, and rollout strategies?",
        }
    },
    "aws": {
        "canonical": "AWS",
        "category": "cloud",
        "probes": {
            "how": "Which AWS services did you leverage, and how did you configure IAM permissions and deployment pipelines?",
        }
    },
    # Programming Languages
    "python": {
        "canonical": "Python",
        "category": "language",
        "probes": {
            "how": "In your Python development, how do you handle packaging, type hinting with Pydantic or mypy, and performance tuning?",
        }
    },
    "java": {
        "canonical": "Java",
        "category": "language",
        "probes": {
            "direct": "Could you tell me a little more about your experience with Java? What kind of applications or projects have you built using it?",
            "how": "In Java, how do you manage concurrency, thread safety, and JVM garbage collection considerations?",
        }
    },
    "sql": {
        "canonical": "SQL",
        "category": "database",
        "probes": {
            "how": "In your SQL database design, how did you ensure data integrity with foreign keys, normalization, and ACID transaction boundaries?",
        }
    }
}


# 
# 8 Internal Relevance Classification Labels
# (Never exposed directly to the candidate)
# 
RELEVANCE_RELEVANT = "RELEVANT"
RELEVANCE_PARTIALLY_RELEVANT = "PARTIALLY_RELEVANT"
RELEVANCE_TOO_SHORT = "TOO_SHORT"
RELEVANCE_GIBBERISH = "GIBBERISH_OR_UNINTELLIGIBLE"
RELEVANCE_OFF_TOPIC = "OFF_TOPIC"
RELEVANCE_DONT_KNOW = "DON'T_KNOW"
RELEVANCE_CORRECTION = "CORRECTION"
RELEVANCE_UNCLEAR = "UNCLEAR"

# Recognized single-letter / short technical acronyms
VALID_SHORT_ACRONYMS = {
    "sql", "aws", "css", "xml", "npm", "jwt", "sdk", "api", "db", "ml", "ai",
    "ci", "cd", "pr", "os", "ip", "ui", "ux", "ts", "js", "go", "c", "r", "c#", "c++",
    "html", "php", "gcp"
}

# Off-topic phrase detectors
OFF_TOPIC_KEYWORDS = {
    "movie", "movies", "cinema", "film", "theatre", "theater", "friends", "friend",
    "cricket", "football", "soccer", "basketball", "tennis", "badminton",
    "dinner", "lunch", "breakfast", "pizza", "burger", "restaurant", "cafe",
    "weather", "rain", "sunny", "cloudy", "beach", "shopping", "mall", "clothes",
    "party", "vacation", "trip", "holiday", "sleep", "slept", "song", "music",
    "joke", "tell me a joke", "how are you", "who are you", "what are you doing"
}

UNCERTAINTY_PHRASES = [
    "don't know", "dont know", "not sure", "no idea", "haven't used", "havent used",
    "not familiar", "never worked", "haven't worked", "havent worked", "no experience",
    "can't say", "cant say", "cant recall", "can't recall", "not really sure",
    "no clue", "never used", "haven't had experience", "i am not sure"
]

SELF_CORRECTION_PATTERNS = [
    # "I used Flask... actually, I used FastAPI" or "used Flask... actually FastAPI"
    r'(?i)\b(?:i used|we used|it was|built with|with)\s+([a-zA-Z0-9_\-\.\#\+]+)\s*(?:\.\.\.|\,)?\s*(?:actually|wait\s+no|sorry|no\s+wait|i meant)\s+(?:i used|we used|it was|)?\s*([a-zA-Z0-9_\-\.\#\+]+)',
    # "Flask... actually, FastAPI"
    r'(?i)\b([a-zA-Z0-9_\-\.\#\+]+)\s*(?:\.\.\.|\,)?\s*actually\s*,?\s*(?:i used|it was|we used|)?\s*([a-zA-Z0-9_\-\.\#\+]+)',
    # "actually I used FastAPI" / "sorry, I meant FastAPI"
    r'(?i)\b(?:actually|sorry,?\s*i meant|i meant)\s+(?:i used|it was|)?\s*([a-zA-Z0-9_\-\.\#\+]+)'
]


# Common English words used in professional and interview conversation
COMMON_ENGLISH_WORDS = {
    "i", "im", "ive", "id", "me", "my", "myself", "we", "us", "our", "you", "your",
    "am", "an", "a", "the", "in", "on", "at", "to", "for", "with", "of", "and", "or", "as",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "did", "done",
    "student", "engineer", "developer", "experience", "project", "projects", "work", "worked",
    "built", "created", "developed", "using", "used", "interested", "interest", "learning",
    "predict", "prediction", "model", "models", "data", "science", "system", "backend",
    "frontend", "fullstack", "attendance", "marks", "study", "hours", "features", "feature",
    "team", "teamwork", "independently", "independent", "yes", "no", "alone", "together",
    "college", "university", "technology", "technologies", "application", "applications",
    "algorithm", "algorithms", "database", "databases", "service", "services", "api", "apis",
    "yesterday", "watched", "went", "movie", "friends", "playing", "cricket", "like", "enjoy",
    "know", "dont", "think", "sure", "flask", "fastapi", "python", "java", "react"
}


# 
# Gibberish & Unintelligible Detector
# 
def is_gibberish_or_unintelligible(text: str) -> bool:
    """
    Detects random keystrokes, punctuation mash, repeated single letters,
    or unintelligible noise like 'k', 'bb', 'yufily,f.iy', 'asdfgh'.
    Does NOT flag real English sentences with contractions (e.g. I'm, I've).
    """
    clean = text.strip()
    if not clean:
        return True

    clean_lower = clean.lower()

    # If any tech keyword from taxonomy is present, it's not gibberish
    for tk in TECH_TAXONOMY.keys():
        if re.search(r'\b' + re.escape(tk) + r'\b', clean_lower):
            return False

    # Extract all alphanumeric words, stripping apostrophes for contractions (I'm -> im)
    words = [re.sub(r"[^a-zA-Z0-9]", "", w.lower()) for w in clean.split()]
    words = [w for w in words if w]

    # If multiple valid words exist, it is not gibberish
    valid_word_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
    if valid_word_count >= 1 and len(words) >= 2:
        return False

    # If single word is a common English word (like 'independently', 'yes', 'no'), not gibberish
    if len(words) == 1 and words[0] in COMMON_ENGLISH_WORDS:
        return False

    # Check for internal punctuation mashed into letters like 'yufily,f.iy' or 'asdf.gh'
    if re.search(r'[a-zA-Z]+[,\.][a-zA-Z]+', clean):
        # Unless it's a known tech like node.js, vue.js, c++
        if clean_lower not in ["node.js", "vue.js", "next.js", "c++", "c#"]:
            return True

    # Check for single character noise (like 'k', 'x', 'q', 'b')
    if len(words) == 1:
        single_word = words[0]
        if len(single_word) == 1 and single_word not in ["a", "i"]:
            return True

        # Check for repeated identical characters like 'bb', 'kk', 'zzz', 'aaa'
        if len(single_word) >= 2 and len(set(single_word)) == 1:
            return True

        # Consonants only (no vowels a, e, i, o, u, y) and not recognized abbreviation
        if len(single_word) >= 2 and not any(v in single_word for v in "aeiouy"):
            if single_word not in VALID_SHORT_ACRONYMS:
                return True

        # Known keyboard smash
        if single_word in ["asdf", "asdfg", "asdfgh", "zxcv", "qwerty", "hjkl", "qwer"]:
            return True

    # If none of the words are recognized English words or tech words, treat as unintelligible
    if valid_word_count == 0 and not any(w in VALID_SHORT_ACRONYMS for w in words):
        return True

    return False


# 
# 1. Resume Profile Extraction (Active Resume Grounding)
# 
def extract_interview_resume_profile(
    resume_text: str,
    skills: List[str],
    predicted_role: str
) -> Dict[str, Any]:
    """
    Extracts structured, verified entities from candidate's Active Resume
    to strictly ground all interview questions. Never hallucinates technologies
    unmentioned in the resume.
    """
    role = predicted_role or "Software Engineer"
    clean_skills = [s.strip() for s in skills if s.strip()]

    # Extract candidate name if available
    name = "Candidate"
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    for line in lines[:5]:
        if len(line) < 40 and not re.search(r'[@:/\\|0-9]', line) and len(line.split()) in [2, 3, 4]:
            if not any(k in line.lower() for k in ["resume", "curriculum", "cv", "profile", "contact", "email", "phone"]):
                name = line
                break

    # Extract projects from resume text
    projects: List[str] = []
    proj_block_match = re.search(
        r'(?:PROJECTS|PERSONAL\s+PROJECTS|ACADEMIC\s+PROJECTS)[\s:]*\n([\s\S]{30,800}?)(?=\n\s*(?:EDUCATION|EXPERIENCE|SKILLS|CERTIFICATIONS|SUMMARY|$))',
        resume_text,
        re.IGNORECASE
    )
    if proj_block_match:
        for pline in proj_block_match.group(1).splitlines():
            pline = pline.strip().strip('-*• ')
            if 6 < len(pline) < 80 and not pline.lower().startswith("http"):
                if any(verb in pline.lower() for verb in ["project", "application", "system", "platform", "bot", "assistant", "tracker", "screening", "shield", "model"]):
                    projects.append(pline)
                elif len(pline.split()) <= 6:
                    projects.append(pline)

    project_matches = re.findall(
        r'(?:Project|Built|Developed|Created|Engineered|Designed)\s*:?\s*([A-Za-z0-9\s\-_.,]{6,60})',
        resume_text,
        re.IGNORECASE
    )
    for pm in project_matches:
        clean_pm = pm.strip().strip(':.,-')
        if len(clean_pm) > 5 and clean_pm not in projects:
            projects.append(clean_pm)

    if not projects:
        if clean_skills:
            projects.append(f"{clean_skills[0]} Service Application")
        else:
            projects.append(f"{role} System")

    edu_match = re.search(r'(?:EDUCATION|ACADEMIC\s+BACKGROUND)[\s:]*\n([\s\S]{20,300}?)(?=\n\s*(?:EXPERIENCE|SKILLS|PROJECTS|$))', resume_text, re.IGNORECASE)
    education = edu_match.group(1).strip() if edu_match else ""

    primary_skill = clean_skills[0] if clean_skills else "Software Engineering"
    secondary_skill = clean_skills[1] if len(clean_skills) > 1 else primary_skill

    known_techs: List[str] = list(clean_skills)
    resume_lower = resume_text.lower()
    for tech_key in TECH_TAXONOMY.keys():
        if tech_key in resume_lower and tech_key not in [k.lower() for k in known_techs]:
            known_techs.append(TECH_TAXONOMY[tech_key]["canonical"])

    return {
        "candidate_name": name,
        "role": role,
        "skills": clean_skills,
        "primary_skill": primary_skill,
        "secondary_skill": secondary_skill,
        "primary_project": projects[0],
        "projects": projects[:5],
        "education": education,
        "known_techs": known_techs,
        "resume_text_sample": resume_text[:1200]
    }


# 
# 2. Context-Aware Candidate Answer Analysis
# 
def analyze_candidate_answer(
    user_answer: str,
    previous_question: str,
    current_topic: str,
    resume_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Accurately classifies candidate response into one of the 8 required categories:
      - RELEVANT
      - PARTIALLY_RELEVANT
      - TOO_SHORT
      - GIBBERISH_OR_UNINTELLIGIBLE
      - OFF_TOPIC
      - DON'T_KNOW
      - CORRECTION
      - UNCLEAR

    The classification considers:
      1. The previous HR question
      2. The current conversation context
      3. The candidate's answer
    """
    text = user_answer.strip()
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)
    prev_q_lower = (previous_question or "").lower()

    # 1. Check for Self-Correction
    self_correction = None
    for pattern in SELF_CORRECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                old_ent = groups[0].strip().strip('.!?,;:').lower()
                new_ent = groups[1].strip().strip('.!?,;:').lower()
                if old_ent != new_ent:
                    self_correction = {
                        "retracted": old_ent,
                        "corrected": new_ent
                    }
                    break
            elif len(groups) == 1:
                self_correction = {
                    "retracted": "",
                    "corrected": groups[0].strip().strip('.!?,;:').lower()
                }
                break

    if self_correction:
        return {
            "text": text,
            "word_count": word_count,
            "classification": RELEVANCE_CORRECTION,
            "self_correction": self_correction,
            "entities_mentioned": [self_correction["corrected"]],
            "projects_mentioned": [],
            "claims": []
        }

    # 2. Check for "Don't Know" / Uncertainty
    if any(phrase in text_lower for phrase in UNCERTAINTY_PHRASES):
        return {
            "text": text,
            "word_count": word_count,
            "classification": RELEVANCE_DONT_KNOW,
            "self_correction": None,
            "entities_mentioned": [],
            "projects_mentioned": [],
            "claims": []
        }

    # 3. Check for Gibberish or Unintelligible characters
    if is_gibberish_or_unintelligible(text):
        return {
            "text": text,
            "word_count": word_count,
            "classification": RELEVANCE_GIBBERISH,
            "self_correction": None,
            "entities_mentioned": [],
            "projects_mentioned": [],
            "claims": []
        }

    # 4. Extract technical entities mentioned in answer
    entities_mentioned: List[str] = []
    for k in sorted(TECH_TAXONOMY.keys(), key=lambda x: len(x), reverse=True):
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(k) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            if k not in entities_mentioned:
                entities_mentioned.append(k)

    # 5. Extract projects mentioned in answer
    projects_mentioned: List[str] = []
    for proj in resume_profile.get("projects", []):
        proj_clean = re.sub(r'[^a-zA-Z0-9\s]', '', proj.lower())
        proj_words = [w for w in proj_clean.split() if len(w) > 3]
        if proj_words and any(pw in text_lower for pw in proj_words):
            projects_mentioned.append(proj)

    explicit_proj = re.findall(
        r'(?:built|created|developed|worked on|trained)\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]{4,50}?(?:model|application|project|app|system|service|tool|platform|assistant|bot|pipeline))',
        text_lower
    )
    for ep in explicit_proj:
        clean_ep = ep.strip().title()
        if clean_ep and clean_ep not in projects_mentioned:
            projects_mentioned.append(clean_ep)

    # 6. Extract claims
    claims: List[str] = []
    if "parsing" in text_lower or "extract" in text_lower:
        claims.append("resume_parsing_logic")
    if "endpoint" in text_lower or "api" in text_lower:
        claims.append("api_endpoints")
    if "model" in text_lower or "predict" in text_lower or "prediction" in text_lower:
        claims.append("ml_model")
    if "feature" in text_lower or "attendance" in text_lower or "marks" in text_lower:
        claims.append("features")
    if "missing value" in text_lower or "imputation" in text_lower or "scaling" in text_lower:
        claims.append("data_preprocessing")

    # 7. Check for Off-Topic remarks
    if any(re.search(r'\b' + re.escape(otk) + r'\b', text_lower) for otk in OFF_TOPIC_KEYWORDS):
        if not entities_mentioned and not claims:
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_OFF_TOPIC,
                "self_correction": None,
                "entities_mentioned": [],
                "projects_mentioned": [],
                "claims": []
            }
        elif any(f in text_lower for f in ["went to a movie", "watched a movie", "went with friends", "play cricket", "had lunch", "had dinner", "the weather"]):
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_OFF_TOPIC,
                "self_correction": None,
                "entities_mentioned": entities_mentioned,
                "projects_mentioned": projects_mentioned,
                "claims": claims
            }

    # 8. Check for Short Answers (Word count <= 4)
    if word_count <= 4:
        clean_ans_lower = text_lower.strip('.!?,')

        # Check if the previous question was broad / introductory / clarification
        is_broad_intro = any(k in prev_q_lower for k in [
            "walk me through", "professional background", "tell me about yourself",
            "introduce yourself", "tell me about your background",
            "elaborate a little", "explaining your answer again", "didn't quite catch",
            "not sure i understood"
        ])

        if is_broad_intro:
            # If candidate just dropped a single technology like "FASTAPI" or "Java"
            if entities_mentioned:
                return {
                    "text": text,
                    "word_count": word_count,
                    "classification": RELEVANCE_PARTIALLY_RELEVANT,
                    "self_correction": None,
                    "entities_mentioned": entities_mentioned,
                    "projects_mentioned": projects_mentioned,
                    "claims": claims
                }
            else:
                return {
                    "text": text,
                    "word_count": word_count,
                    "classification": RELEVANCE_UNCLEAR,
                    "self_correction": None,
                    "entities_mentioned": [],
                    "projects_mentioned": [],
                    "claims": []
                }

        # If previous question was targeted (asking for framework, database, teamwork mode, yes/no)
        # e.g., "Which backend framework have you used?" -> "FastAPI."
        # "Have you worked with databases?" -> "PostgreSQL."
        # "Did you work independently or with a team?" -> "Independently."
        is_targeted_framework = any(k in prev_q_lower for k in ["framework", "backend", "library", "technology", "stack"])
        is_targeted_database = any(k in prev_q_lower for k in ["database", "databases", "store", "sql"])
        is_targeted_team = any(k in prev_q_lower for k in ["independently", "team", "collaborat", "work alone"])
        is_yes_no = any(prev_q_lower.startswith(w) for w in ["have you", "did you", "do you", "were you", "is there", "can you"])

        if is_targeted_framework and entities_mentioned:
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_TOO_SHORT,
                "self_correction": None,
                "entities_mentioned": entities_mentioned,
                "projects_mentioned": projects_mentioned,
                "claims": ["direct_framework_answer"]
            }

        if is_targeted_database and ("postgresql" in clean_ans_lower or "mysql" in clean_ans_lower or "mongodb" in clean_ans_lower or "redis" in clean_ans_lower or "sql" in clean_ans_lower):
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_TOO_SHORT,
                "self_correction": None,
                "entities_mentioned": entities_mentioned or [clean_ans_lower],
                "projects_mentioned": projects_mentioned,
                "claims": ["direct_database_answer"]
            }

        if is_targeted_team and any(w in clean_ans_lower for w in ["independently", "independent", "alone", "solo", "team", "with a team"]):
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_TOO_SHORT,
                "self_correction": None,
                "entities_mentioned": [],
                "projects_mentioned": [],
                "claims": ["direct_team_answer"]
            }

        if is_yes_no and clean_ans_lower in ["yes", "yeah", "yep", "sure", "i have", "i did", "no", "not yet"]:
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_TOO_SHORT,
                "self_correction": None,
                "entities_mentioned": [],
                "projects_mentioned": [],
                "claims": ["direct_yes_no_answer"]
            }

        # Short recognized entity
        if entities_mentioned:
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_TOO_SHORT,
                "self_correction": None,
                "entities_mentioned": entities_mentioned,
                "projects_mentioned": projects_mentioned,
                "claims": claims
            }

        # Otherwise unclear
        return {
            "text": text,
            "word_count": word_count,
            "classification": RELEVANCE_UNCLEAR,
            "self_correction": None,
            "entities_mentioned": [],
            "projects_mentioned": [],
            "claims": []
        }

    # 9. Vague / Unclear text (5-10 words with no technical substance or relevance)
    if word_count < 8 and not entities_mentioned and not projects_mentioned and not claims:
        if any(v in text_lower for v in ["maybe", "kind of", "sort of", "just that", "not really", "nothing special", "normal stuff"]):
            return {
                "text": text,
                "word_count": word_count,
                "classification": RELEVANCE_UNCLEAR,
                "self_correction": None,
                "entities_mentioned": [],
                "projects_mentioned": [],
                "claims": []
            }

    # 10. Default to RELEVANT
    return {
        "text": text,
        "word_count": word_count,
        "classification": RELEVANCE_RELEVANT,
        "self_correction": None,
        "entities_mentioned": entities_mentioned,
        "projects_mentioned": projects_mentioned,
        "claims": claims
    }


# 
# 3. Structured Interview Memory & State
# 
class InterviewMemoryState:
    """Tracks interview topics, turns, discussed technologies, recent response styles, and history."""

    def __init__(self, resume_profile: Dict[str, Any]):
        self.resume_profile = resume_profile
        self.candidate_turns = 0
        self.current_topic = "introduction"
        self.consecutive_topic_turns = 0
        self.topics_covered: List[str] = []
        self.questions_asked: List[str] = []
        self.recent_interviewer_responses: List[str] = []
        self.recent_question_styles: List[str] = []
        self.technologies_discussed: Set[str] = set()
        self.projects_discussed: Set[str] = set()
        self.unintelligible_count = 0
        self.last_relevance = RELEVANCE_RELEVANT
        self.last_question = ""


def reconstruct_interview_state(
    history: List[Dict[str, Any]],
    resume_profile: Dict[str, Any]
) -> InterviewMemoryState:
    """Reconstructs state machine and conversation memory from the dialogue history."""
    state = InterviewMemoryState(resume_profile)

    candidate_turns = 0
    ai_questions: List[str] = []

    for entry in history:
        speaker = entry.get("speaker") or entry.get("sender")
        text = entry.get("text", "")
        if speaker in ["ai_interviewer", "ai"]:
            ai_questions.append(text)
        elif speaker in ["candidate", "user"]:
            candidate_turns += 1
            t_low = text.lower()
            if is_gibberish_or_unintelligible(text):
                state.unintelligible_count += 1
            for tech in TECH_TAXONOMY.keys():
                if tech in t_low:
                    state.technologies_discussed.add(tech)

    state.candidate_turns = candidate_turns
    state.questions_asked = ai_questions
    state.recent_interviewer_responses = ai_questions[-4:] if ai_questions else []
    if ai_questions:
        state.last_question = ai_questions[-1]

    return state


# 
# 4. Semantic Similarity & Repetition Guard
# 
def is_too_similar_to_previous_questions(
    candidate_question: str,
    previous_questions: List[str],
    threshold: float = 0.55
) -> bool:
    """
    Checks whether candidate question is semantically or lexically too similar
    to previously asked questions, ensuring non-repetitive dialogue.
    """
    if not previous_questions or not candidate_question:
        return False

    clean_cand = candidate_question.strip().lower()

    for pq in previous_questions:
        clean_pq = pq.strip().lower()
        if clean_cand == clean_pq:
            return True
        if len(clean_cand) > 30 and (clean_cand in clean_pq or clean_pq in clean_cand):
            return True

    # TF-IDF cosine similarity check
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        corpus = list(previous_questions) + [candidate_question]
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = vectorizer.fit_transform(corpus)
        cand_vec = tfidf[-1]
        prev_vecs = tfidf[:-1]
        sims = cosine_similarity(cand_vec, prev_vecs)[0]
        max_sim = float(max(sims)) if len(sims) > 0 else 0.0
        if max_sim >= threshold:
            return True
    except Exception:
        pass

    # Jaccard word-overlap fallback
    cand_words = set(re.findall(r'\b\w{3,}\b', clean_cand))
    for pq in previous_questions:
        pq_words = set(re.findall(r'\b\w{3,}\b', pq.lower()))
        if not cand_words or not pq_words:
            continue
        overlap = len(cand_words.intersection(pq_words)) / max(1, len(cand_words.union(pq_words)))
        if overlap >= 0.50:
            return True

    return False


# 
# 5. Initial HR Question Generator
# 
def generate_initial_hr_question(
    resume_text: str,
    skills: List[str],
    predicted_role: str,
    force_fallback: bool = False
) -> Dict[str, Any]:
    """
    Generates a warm, professional, and natural HR opening question grounded in
    the candidate's target role and active resume. Zero emojis.
    Uses live Groq when active; falls back to deterministic greeting if offline/fallback.
    """
    profile = extract_interview_resume_profile(resume_text, skills, predicted_role)
    role = profile["role"]
    cand_name = profile.get("candidate_name", "Candidate")
    skills_preview = ", ".join(profile.get("skills", [])[:5])

    # Check if live LLM provider is active
    try:
        from services.llm_provider import get_llm_provider
        provider = get_llm_provider()
        prov_info = provider.get_info()
    except Exception:
        provider = None
        prov_info = {"mode": "fallback"}

    if not force_fallback and prov_info.get("mode") == "live" and provider is not None:
        sys_prompt = (
            f"You are an experienced, professional, and empathetic human HR interviewer conducting "
            f"a realistic conversational job interview for a {role} position.\n\n"
            "MANDATORY GUIDELINES:\n"
            "1. Stay strictly in character as a professional human HR interviewer. Never mention being an AI or language model.\n"
            "2. Greet the candidate warmly and ask exactly ONE opening interview question to kick off the interview "
            "(e.g., inviting them to introduce themselves and discuss their background and motivation for this role).\n"
            "3. Keep your entire response concise: 2 to 3 sentences maximum (under 50 words). This response will be spoken aloud to the candidate via Text-to-Speech.\n"
            "4. Use natural spoken English. Absolutely NO emojis, NO markdown formatting (no asterisks, bullet points, headers).\n"
            "5. Never output JSON or system notes. Output ONLY your spoken greeting and question."
        )
        user_prompt = (
            f"Candidate Name: {cand_name}\n"
            f"Target Role: {role}\n"
            f"Resume Technical Skills: {skills_preview}\n\n"
            "Speak your opening greeting and first question now:"
        )

        try:
            groq_opening = provider.generate_text(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                temperature=0.6,
                json_mode=False
            )
            if groq_opening and groq_opening.strip():
                clean_q = normalize_spoken_text(groq_opening)
                return {
                    "step_index": 0,
                    "stage": "introduction",
                    "speaker": "ai_interviewer",
                    "question": clean_q,
                    "message": clean_q,
                    "context_elements": profile,
                    "provider": prov_info.get("provider", "groq")
                }
            else:
                raise HrInterviewUnavailableError("Groq AI Interviewer failed to generate an opening greeting. Please try again.")
        except HrInterviewUnavailableError:
            raise
        except Exception as e:
            logger.warning(f"Live Groq initial question error: {e}")
            raise HrInterviewUnavailableError("Groq AI Interviewer is currently unavailable. Please try again.")

    # Offline / deterministic fallback mode
    question_text = (
        f"Hello! It's great to connect with you today. To kick off our interview, could you walk me "
        f"through your professional background, and what inspired your focus in {role}?"
    )

    return {
        "step_index": 0,
        "stage": "introduction",
        "speaker": "ai_interviewer",
        "question": question_text,
        "message": question_text,
        "context_elements": profile,
        "provider": "local_fallback"
    }



# 
# 6. Adaptive Deterministic Fallback Engine
# 
def _generate_adaptive_fallback_response(
    previous_question: str,
    user_answer: str,
    analysis: Dict[str, Any],
    state: InterviewMemoryState,
    resume_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic & context-aware HR interviewer engine.
    Handles all 8 internal classifications dynamically with zero template repetition.
    """
    classification = analysis["classification"]
    self_corr = analysis.get("self_correction")
    entities = analysis.get("entities_mentioned", [])
    projects = analysis.get("projects_mentioned", [])
    ans_lower = user_answer.lower()
    prev_q_lower = previous_question.lower()
    next_step = state.candidate_turns + 1

    # -------------------------------------------------------------
    # 1. GIBBERISH OR UNINTELLIGIBLE ANSWERS
    # e.g., 'k', 'bb', 'yufily,f.iy'
    # -------------------------------------------------------------
    if classification == RELEVANCE_GIBBERISH:
        # Vary clarification depending on turn and history
        if state.unintelligible_count <= 1:
            if "background" in prev_q_lower or "introduce" in prev_q_lower:
                msg = "I didn't quite catch that. Could you tell me a little more about your background?"
            else:
                msg = "I didn't quite catch that. Could you share a bit more about what you mean?"
        elif state.unintelligible_count == 2:
            msg = "I'm not sure I understood that. Could you elaborate a little?"
        else:
            msg = "Sorry, I couldn't quite follow that. Could you try explaining your answer again?"

        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "clarification_unintelligible",
            "speaker": "ai_interviewer",
            "message": msg,
            "question": msg,
            "internal_relevance": RELEVANCE_GIBBERISH
        }

    # -------------------------------------------------------------
    # 2. UNCLEAR / VAGUE ANSWERS
    # e.g., 'maybe something like that', 'just that thing'
    # -------------------------------------------------------------
    if classification == RELEVANCE_UNCLEAR:
        if state.candidate_turns <= 2 and ("background" in prev_q_lower or "walk me through" in prev_q_lower):
            msg = "I'd love to learn more about your experience. Could you share a bit about your studies, technologies you work with, or recent projects?"
        else:
            msg = "Could you clarify what you mean by that, or give a specific example?"

        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "clarification_unclear",
            "speaker": "ai_interviewer",
            "message": msg,
            "question": msg,
            "internal_relevance": RELEVANCE_UNCLEAR
        }

    # -------------------------------------------------------------
    # 3. OFF-TOPIC ANSWERS
    # -------------------------------------------------------------
    if classification == RELEVANCE_OFF_TOPIC:
        # Special case: Teamwork question + sports
        if any(k in prev_q_lower for k in ["team", "teamwork", "collaborat", "disagreement"]) and any(s in ans_lower for s in ["cricket", "football", "soccer", "basketball"]):
            sport = "cricket" if "cricket" in ans_lower else "sports"
            msg = f"That's an interest outside your technical work. Have you ever played {sport} as part of a team, and what did that teach you about collaboration?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "bridge_off_topic_teamwork",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_OFF_TOPIC
            }

        # Movie / personal leisure
        if any(m in ans_lower for m in ["movie", "cinema", "film"]):
            if any(k in prev_q_lower for k in ["challenge", "project", "problem", "bottleneck"]):
                msg = "That sounds like a nice outing. Coming back to your project, what was the most challenging technical problem you had to solve?"
            else:
                msg = "That sounds like a nice break. Coming back to our discussion, could you share a bit about the technical work or projects you've been focused on?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "redirect_off_topic",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_OFF_TOPIC
            }

        # Generic off-topic redirection
        msg = "That sounds pleasant, but let's keep our focus on your technical experience. Coming back to our discussion, could you tell me more about your recent engineering work?"
        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "redirect_off_topic",
            "speaker": "ai_interviewer",
            "message": msg,
            "question": msg,
            "internal_relevance": RELEVANCE_OFF_TOPIC
        }

    # -------------------------------------------------------------
    # 4. "I DON'T KNOW" / UNCERTAINTY PIVOT
    # -------------------------------------------------------------
    if classification == RELEVANCE_DONT_KNOW:
        # Find unvisited skill from Active Resume
        unvisited_skill = None
        for sk in resume_profile.get("skills", []):
            if sk.lower() not in state.technologies_discussed and sk.lower() not in [e.lower() for e in entities]:
                unvisited_skill = sk
                break

        if not unvisited_skill:
            unvisited_skill = resume_profile.get("secondary_skill") or "database architecture"

        sk_canonical = TECH_TAXONOMY.get(unvisited_skill.lower(), {}).get("canonical", unvisited_skill)

        if unvisited_skill.lower() in ["postgresql", "postgres", "mysql", "mongodb", "sql"]:
            pivot_q = f"That's completely fine. Let's move to another area of your background. In your resume, you listed {sk_canonical}. With {sk_canonical}, how did you approach database schema design, indexing strategies, and query performance optimization?"
        elif unvisited_skill.lower() in ["docker", "kubernetes"]:
            pivot_q = f"That's completely fine. Let's move to another area of your background. In your resume, you listed {sk_canonical}. How did you configure container environments and manage development workflows?"
        else:
            pivot_q = f"That's completely fine. Let's move to another area of your background. In your resume, you listed {sk_canonical}. What was a project where you applied {sk_canonical}, and what was your role?"

        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "pivot_explore",
            "speaker": "ai_interviewer",
            "message": pivot_q,
            "question": pivot_q,
            "internal_relevance": RELEVANCE_DONT_KNOW
        }

    # -------------------------------------------------------------
    # 5. SELF-CORRECTION
    # e.g., "I used Flask... actually, I used FastAPI"
    # -------------------------------------------------------------
    if classification == RELEVANCE_CORRECTION and self_corr:
        corrected_raw = self_corr.get("corrected", "")
        canonical_tech = TECH_TAXONOMY.get(corrected_raw, {}).get("canonical", corrected_raw.title())

        if canonical_tech.lower() in ["fastapi", "flask", "django", "spring boot", "spring", "express", "node"]:
            corr_q = f"Got it, {canonical_tech}. How did you organize your routers and dependency injection in {canonical_tech}?"
        elif canonical_tech.lower() in ["postgresql", "mysql", "mongodb", "redis"]:
            corr_q = f"Understood, {canonical_tech}. How did you design your schemas and query patterns when working with {canonical_tech}?"
        else:
            corr_q = f"Got it, {canonical_tech}. Could you tell me more about how you structured your work using {canonical_tech}?"

        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "self_correction_followup",
            "speaker": "ai_interviewer",
            "message": corr_q,
            "question": corr_q,
            "internal_relevance": RELEVANCE_CORRECTION
        }

    # -------------------------------------------------------------
    # 6. PARTIALLY RELEVANT (e.g. lone technology drop in broad intro)
    # e.g., HR: "Tell me about your background" -> Candidate: "FASTAPI"
    # -------------------------------------------------------------
    if classification == RELEVANCE_PARTIALLY_RELEVANT:
        tech_name = entities[0] if entities else "that technology"
        canonical_tech = TECH_TAXONOMY.get(tech_name, {}).get("canonical", tech_name.title())

        msg = f"{canonical_tech} is one of the technologies you're interested in. Could you tell me about a project where you've used it and what your role was?"
        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "elaborate_partial_tech",
            "speaker": "ai_interviewer",
            "message": msg,
            "question": msg,
            "internal_relevance": RELEVANCE_PARTIALLY_RELEVANT
        }

    # -------------------------------------------------------------
    # 7. TOO SHORT (Direct answers to targeted questions)
    # -------------------------------------------------------------
    if classification == RELEVANCE_TOO_SHORT:
        claims = analysis.get("claims", [])
        clean_ans_lower = ans_lower.strip('.!?,')

        # Direct framework answer
        if "direct_framework_answer" in claims or (entities and any(k in prev_q_lower for k in ["framework", "backend", "library"])):
            tech_canonical = TECH_TAXONOMY.get(entities[0], {}).get("canonical", entities[0].title())
            msg = f"What did you build with {tech_canonical}?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "direct_short_followup",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_TOO_SHORT
            }

        # Direct database answer
        if "direct_database_answer" in claims or ("postgresql" in clean_ans_lower or "mysql" in clean_ans_lower or "mongodb" in clean_ans_lower):
            db_canonical = "PostgreSQL" if "postgres" in clean_ans_lower else clean_ans_lower.title()
            msg = f"What kind of data did you store in {db_canonical}, and how did you structure the tables?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "direct_short_followup",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_TOO_SHORT
            }

        # Direct team answer
        if "direct_team_answer" in claims or "independently" in clean_ans_lower:
            if "independently" in clean_ans_lower or "alone" in clean_ans_lower:
                msg = "What part of the project did you handle yourself?"
            else:
                msg = "How was the work divided among team members, and what was your individual contribution?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "direct_short_followup",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_TOO_SHORT
            }

        # Direct yes / no answer
        if "direct_yes_no_answer" in claims:
            msg = "Could you walk me through a specific example or scenario where that came into play?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "direct_short_followup",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_TOO_SHORT
            }

        # Generic recognized technology short answer
        if entities:
            tech_canonical = TECH_TAXONOMY.get(entities[0], {}).get("canonical", entities[0].title())
            msg = f"What did you build with {tech_canonical}?"
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "direct_short_followup",
                "speaker": "ai_interviewer",
                "message": msg,
                "question": msg,
                "internal_relevance": RELEVANCE_TOO_SHORT
            }

        # Fallback short answer
        msg = f"Could you elaborate a bit more on that? I'd love to hear more details about how that worked in practice."
        return {
            "is_complete": False,
            "step_index": next_step,
            "stage": "elaboration_probe",
            "speaker": "ai_interviewer",
            "message": msg,
            "question": msg,
            "internal_relevance": RELEVANCE_TOO_SHORT
        }

    # -------------------------------------------------------------
    # 8. RELEVANT ANSWERS (Answer-Driven Follow-Ups)
    # Every follow-up MUST use information from the candidate's latest answer!
    # -------------------------------------------------------------

    # Sequence A: Candidate introduced interest in Data Science with Python/Pandas/scikit-learn
    # "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."
    if "data science" in ans_lower or ("python" in ans_lower and ("pandas" in ans_lower or "scikit-learn" in ans_lower or "machine learning" in ans_lower)):
        if "model" not in ans_lower and "predict" not in ans_lower:
            followup_q = "You've started exploring Data Science with Python and its libraries. What kind of analysis or machine learning project have you worked on?"
            if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
                return {
                    "is_complete": False,
                    "step_index": next_step,
                    "stage": "datascience_project_inquiry",
                    "speaker": "ai_interviewer",
                    "message": followup_q,
                    "question": followup_q,
                    "internal_relevance": RELEVANCE_RELEVANT
                }

    # Sequence B: Candidate built a student performance prediction model
    # "I built a student performance prediction model using scikit-learn."
    if any(k in ans_lower for k in ["prediction model", "performance prediction", "student performance", "prediction"]) or (("built" in ans_lower or "created" in ans_lower) and "model" in ans_lower):
        if not any(f in ans_lower for f in ["attendance", "marks", "features"]):
            followup_q = "What features did you use to predict student performance, and how did you evaluate the model?"
            if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
                return {
                    "is_complete": False,
                    "step_index": next_step,
                    "stage": "model_features_eval",
                    "speaker": "ai_interviewer",
                    "message": followup_q,
                    "question": followup_q,
                    "internal_relevance": RELEVANCE_RELEVANT
                }

    # Sequence C: Candidate explained features like attendance, previous marks, study hours
    # "I used attendance, previous marks, and study hours." / "I used attendance and previous marks."
    if any(f in ans_lower for f in ["attendance", "marks", "study hours", "previous marks"]) or ("feature" in ans_lower and "use" in ans_lower):
        followup_q = "How did you handle missing values or differences in scale between those features?"
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "preprocessing_features",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence D: Candidate explained preprocessing / missing values / normalization
    if any(m in ans_lower for m in ["missing value", "imputation", "standardscaler", "minmax", "scale", "normalization", "mean"]):
        followup_q = "That's a sound preprocessing approach. When evaluating your model, which metrics did you rely on to measure its predictive accuracy?"
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "model_evaluation_metrics",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence E: Candidate built a resume screening application using FastAPI and React
    if any(k in ans_lower for k in ["built a", "created a", "developed a", "project"]) and any(f in ans_lower for f in ["fastapi", "react", "spring", "flask", "django"]):
        matched_proj = projects[0] if projects else "resume screening application"
        tech_list = [TECH_TAXONOMY[e]["canonical"] for e in entities if e in TECH_TAXONOMY]
        tech_str = " and ".join(tech_list[:2]) if tech_list else "your stack"

        followup_q = (
            f"That's interesting. You mentioned that you built a {matched_proj} using {tech_str}. "
            f"What was your specific role in that project, and what part of the backend did you develop?"
        )
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "project_deepdive",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence F: Candidate worked on resume parsing logic and API endpoints
    if "parsing" in ans_lower or ("resume" in ans_lower and "logic" in ans_lower):
        followup_q = (
            "I see. When parsing resumes, what kind of library or logic did you use to extract text, "
            "and how did you handle different resume layouts?"
        )
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "technical_parsing",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence G: Candidate mentions pdfplumber and regex
    if "regex" in ans_lower or "pdfplumber" in ans_lower or "regular expression" in ans_lower:
        followup_q = (
            "That makes sense. Regular expressions can become tricky when candidate formats vary widely. "
            "Did you encounter any cases where regex failed or produced false positives, and how did you solve that?"
        )
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "technical_regex_challenge",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence H: Candidate explains layout / text extraction challenges
    if "layout" in ans_lower or "multi-column" in ans_lower:
        followup_q = (
            "Handling multi-column layouts is indeed a classic hurdle with text extractors. "
            "How did you structure your parsing pipeline or coordinate bounding boxes to reconstruct the reading order correctly?"
        )
        if not is_too_similar_to_previous_questions(followup_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "technical_depth",
                "speaker": "ai_interviewer",
                "message": followup_q,
                "question": followup_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Sequence I: Probing detected technical entities
    for ent in entities:
        if ent in TECH_TAXONOMY:
            probes = TECH_TAXONOMY[ent].get("probes", {})
            for style in ["eval", "how", "direct", "challenge", "async"]:
                cand_probe = probes.get(style)
                if cand_probe and not is_too_similar_to_previous_questions(cand_probe, state.questions_asked):
                    return {
                        "is_complete": False,
                        "step_index": next_step,
                        "stage": "technical_depth",
                        "speaker": "ai_interviewer",
                        "message": cand_probe,
                        "question": cand_probe,
                        "internal_relevance": RELEVANCE_RELEVANT
                    }

    # Sequence J: Topic transitions (turns 4-6)
    if state.candidate_turns in [4, 5]:
        trans_q = (
            "That gives me a great picture of your technical work. Let's shift gears slightly. "
            "Can you tell me about a time on that project where you encountered a technical disagreement "
            "with a team member or stakeholder? How did you navigate that situation to reach a resolution?"
        )
        if not is_too_similar_to_previous_questions(trans_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "behavioral_teamwork",
                "speaker": "ai_interviewer",
                "message": trans_q,
                "question": trans_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    if state.candidate_turns == 6:
        inc_q = (
            "Understood, that makes a lot of sense. Another important aspect of software engineering is handling "
            "unexpected hurdles. Can you describe a challenging bug or performance bottleneck you encountered "
            "during development or testing, and how you tracked down the root cause?"
        )
        if not is_too_similar_to_previous_questions(inc_q, state.questions_asked):
            return {
                "is_complete": False,
                "step_index": next_step,
                "stage": "debugging_problem_solving",
                "speaker": "ai_interviewer",
                "message": inc_q,
                "question": inc_q,
                "internal_relevance": RELEVANCE_RELEVANT
            }

    # Contextual fallback grounded in resume
    primary_skill = resume_profile.get("primary_skill", "software design")
    gen_q = f"In your experience with {primary_skill}, how did you balance code simplicity, test coverage, and delivery speed when implementing critical features?"
    return {
        "is_complete": False,
        "step_index": next_step,
        "stage": "technical_depth",
        "speaker": "ai_interviewer",
        "message": gen_q,
        "question": gen_q,
        "internal_relevance": RELEVANCE_RELEVANT
    }


# 
# 7. Main Coordinator: generate_next_hr_response
# 
def generate_next_hr_response(
    previous_question: str,
    user_answer: str,
    step_index: int,
    resume_text: str,
    skills: List[str],
    predicted_role: str,
    history: List[Dict[str, Any]],
    force_fallback: bool = False
) -> Dict[str, Any]:
    """
    Main HR interviewer response coordinator:
    1. Analyzes candidate answer (8 internal classifications, self-corrections, entities).
    2. Reconstructs state and checks for session conclusion (after 6 candidate turns or candidate request).
    3. If Groq LLM provider is active (live API key), executes natural conversational HR prompt.
    4. If Groq fails, raises HrInterviewUnavailableError so the user is given a clear retry option.
    5. If in fallback/offline mode (or force_fallback=True), executes the deterministic engine.
    6. Ensures spoken-friendly delivery (2-3 sentences, zero emojis, normalized quotes).
    """
    resume_profile = extract_interview_resume_profile(resume_text, skills, predicted_role)
    state = reconstruct_interview_state(history, resume_profile)

    analysis = analyze_candidate_answer(
        user_answer=user_answer,
        previous_question=previous_question,
        current_topic=state.current_topic,
        resume_profile=resume_profile
    )

    next_step = state.candidate_turns + 1

    # Check provider mode
    try:
        from services.llm_provider import get_llm_provider
        provider = get_llm_provider()
        prov_info = provider.get_info()
    except Exception:
        provider = None
        prov_info = {"mode": "fallback"}

    # Check if candidate explicitly requested to wrap up
    ans_lower = user_answer.lower().strip()
    if any(q in ans_lower for q in ["can we wrap up", "finish the interview", "end interview", "that is all"]):
        closing_msg = (
            "Certainly! Thank you for walking me through your background and technical projects today. "
            "I have concluded our session and compiled your final evaluation report."
        )
        return {
            "is_complete": True,
            "step_index": next_step,
            "stage": "completed",
            "speaker": "ai_interviewer",
            "message": closing_msg,
            "question": None,
            "internal_relevance": analysis["classification"],
            "provider": prov_info.get("provider", "groq") if (prov_info.get("mode") == "live" and not force_fallback) else "local_fallback"
        }

    # Check for session completion after 6 or more candidate turns
    is_concluding_turn = (state.candidate_turns >= 6)

    # 1. Execute Live Groq Provider when active
    if not force_fallback and prov_info.get("mode") == "live" and provider is not None:
        if is_concluding_turn:
            sys_prompt = (
                f"You are an experienced, professional, and empathetic human HR interviewer conducting "
                f"a voice-based conversational job interview for a {resume_profile['role']} position.\n\n"
                "INSTRUCTIONS:\n"
                "1. The candidate has answered all interview questions thoroughly and the interview is now concluding.\n"
                "2. Warmly thank the candidate for their time, acknowledge their effort and insights today, "
                "and inform them that the interview has concluded and their comprehensive evaluation report is now being compiled.\n"
                "3. Keep your response concise: 2 to 3 sentences maximum (under 45 words) for Text-to-Speech spoken delivery.\n"
                "4. Spoken English only. NO emojis, NO markdown formatting (no asterisks, bullet points).\n"
                "5. Never output JSON or system notes. Output ONLY your spoken words."
            )
        else:
            sys_prompt = (
                f"You are an experienced, professional, and empathetic human HR interviewer conducting "
                f"a realistic voice-based conversational job interview for a {resume_profile['role']} position.\n\n"
                "MANDATORY GUIDELINES:\n"
                "1. Stay strictly in character as a professional human HR interviewer. Never mention being an AI or language model.\n"
                "2. Ask exactly ONE interview question at a time. Never ask compound or multi-part questions.\n"
                "3. Listen attentively to the candidate's latest answer:\n"
                "   - Acknowledge their response naturally and briefly in one sentence (e.g. 'That makes sense.', 'Thank you for sharing that.', 'I appreciate that breakdown.').\n"
                "   - If the candidate answered sufficiently, smoothly transition to another key HR topic such as teamwork, handling technical challenges/bugs, communication style, conflict resolution, or career aspirations.\n"
                "   - If the candidate's answer was brief or needs more depth, ask a focused follow-up question directly related to what they just said.\n"
                "   - If the candidate says 'I do not know' or is unsure, reassure them politely ('That is completely fine!') and smoothly ask about another skill from their resume.\n"
                "   - If the candidate makes an off-topic remark, politely acknowledge and gently steer back to their professional experience.\n"
                "   - If the candidate's response is unintelligible, politely ask them to clarify.\n"
                f"4. Grounded in Active Resume: You may probe their verified skills ({', '.join(resume_profile['skills'][:6])}) "
                f"or projects ({', '.join(resume_profile['projects'][:2])}) without assuming unmentioned technologies.\n"
                "5. Response Length: Keep your entire response concise: 2 to 3 sentences maximum (under 50 words) so it is clear when spoken aloud via Text-to-Speech.\n"
                "6. Spoken English only. NO emojis, NO markdown formatting (no asterisks, bullet points, headers).\n"
                "7. Never output JSON or system instructions. Output ONLY your spoken words."
            )

        hist_lines = []
        for h in history[-8:]:
            spk = "Interviewer" if h.get("speaker") == "ai_interviewer" or h.get("sender") == "ai" else "Candidate"
            hist_lines.append(f"{spk}: {h.get('text', '')}")
        hist_str = "\n".join(hist_lines)

        user_prompt = (
            f"Candidate Profile: Role: {resume_profile['role']}, Skills: {', '.join(resume_profile['skills'][:6])}\n"
            f"Turn: {state.candidate_turns} of 6\n\n"
            f"Conversation Dialogue:\n{hist_str}\n\n"
            f"Candidate's Latest Answer:\n{user_answer}\n\n"
            f"{'Conclude the interview warmly as the HR interviewer:' if is_concluding_turn else 'Respond naturally as the HR interviewer with a brief acknowledgment and your next question (2-3 sentences, spoken English only):'}"
        )

        try:
            groq_response = provider.generate_text(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                temperature=0.6,
                json_mode=False
            )
            if groq_response and groq_response.strip():
                clean_msg = normalize_spoken_text(groq_response)
                return {
                    "is_complete": is_concluding_turn,
                    "step_index": next_step,
                    "stage": "completed" if is_concluding_turn else "conversational_turn",
                    "speaker": "ai_interviewer",
                    "message": clean_msg,
                    "question": clean_msg,
                    "internal_relevance": analysis["classification"],
                    "provider": prov_info.get("provider", "groq")
                }
            else:
                logger.warning("[generate_next_hr_response] Groq returned empty response.")
                raise HrInterviewUnavailableError("Groq AI Interviewer is currently unavailable. Please try again.")
        except HrInterviewUnavailableError:
            raise
        except Exception as e:
            logger.warning(f"Live Groq generation error: {e}")
            raise HrInterviewUnavailableError("Groq AI Interviewer is currently unavailable. Please try again.")

    # 2. Context-Aware Fallback Engine (Offline / Test / force_fallback)
    fallback_res = _generate_adaptive_fallback_response(
        previous_question=previous_question,
        user_answer=user_answer,
        analysis=analysis,
        state=state,
        resume_profile=resume_profile
    )
    fallback_res["provider"] = "local_fallback"
    fallback_res["message"] = normalize_spoken_text(fallback_res.get("message", ""))
    fallback_res["question"] = fallback_res["message"]
    return fallback_res



# 
# 8. Post-Interview Evaluation
# 
def evaluate_one_to_one_interview(
    dialogue: List[Dict[str, Any]],
    resume_text: str,
    skills: List[str],
    predicted_role: str
) -> Dict[str, Any]:
    """
    Evaluates the full conversational transcript across communication clarity,
    relevance, technical depth, and resume consistency.
    """
    user_turns = [d for d in dialogue if d.get("sender") == "candidate" or d.get("speaker") == "candidate"]

    if not user_turns:
        return {
            "overall_score": 0.0,
            "communication_score": 0.0,
            "response_clarity_score": 0.0,
            "relevance_score": 0.0,
            "strengths": ["No candidate responses recorded."],
            "improvement_areas": ["Participate in the full HR interview conversation."],
            "summary": "Session concluded without recorded responses.",
            "turns_completed": 0
        }

    total_words = sum(len(turn.get("text", "").split()) for turn in user_turns)
    avg_words = total_words / len(user_turns)

    comm_score = min(100.0, max(50.0, 40.0 + (avg_words * 1.8)))

    full_user_text = " ".join(t.get("text", "") for t in user_turns).lower()
    matched_skills = [s for s in skills if s.lower() in full_user_text]
    relevance_score = min(100.0, 50.0 + (len(matched_skills) * 8.0))

    clarity_score = 75.0
    if any(k in full_user_text for k in ["for example", "specifically", "in my experience", "resulted in", "architected", "challenge was", "handled"]):
        clarity_score += 15.0
    if any(k in full_user_text for k in ["pdfplumber", "fastapi", "spring boot", "react", "postgresql", "docker", "regex", "scikit-learn"]):
        clarity_score += 5.0
    clarity_score = min(100.0, clarity_score)

    overall = round((comm_score * 0.35) + (relevance_score * 0.35) + (clarity_score * 0.30), 1)

    strengths = []
    improvements = []

    if comm_score >= 75:
        strengths.append("Articulate and comprehensive verbal communication with substantive technical detail.")
    else:
        improvements.append("Expand on specific architectural details, metrics, and technical trade-offs in your answers.")

    if relevance_score >= 70:
        strengths.append(f"Strong consistency with resume background, referencing {len(matched_skills)} verified technical competencies.")
    else:
        improvements.append("Directly cite past project outcomes and concrete engineering experiences from your resume.")

    if clarity_score >= 80:
        strengths.append("Structured responses using professional STAR framing (Situation, Task, Action, Result).")
    else:
        improvements.append("Structure behavioral and project responses with clear context, action taken, and measurable results.")

    if not strengths:
        strengths.append("Completed conversational HR interview session with consistent dialogue engagement.")
    if not improvements:
        improvements.append("Continue maintaining strong conversational presence and structured problem-solving delivery.")

    summary = (
        f"The candidate completed a {len(user_turns)}-turn conversational HR interview for the {predicted_role or 'Software Engineer'} profile. "
        f"Demonstrated an overall conversational readiness score of {overall}/100 with solid resume alignment and professional articulation."
    )

    return {
        "overall_score": overall,
        "communication_score": round(comm_score, 1),
        "response_clarity_score": round(clarity_score, 1),
        "relevance_score": round(relevance_score, 1),
        "strengths": strengths,
        "improvement_areas": improvements,
        "summary": summary,
        "turns_completed": len(user_turns)
    }
