"""
interview_engine.py — Phase 6 Mock Interview Engine

Responsibilities:
  1. Generate personalized question set for a session
  2. Evaluate user answers with semantic similarity + keyword coverage
  3. Generate deterministic AI feedback text
  4. Calculate final report (overall score, strengths, improvement areas)
"""

import os
import random
import logging
from typing import List, Dict, Optional, Tuple

import numpy as np

from models.question_bank import (
    ROLE_QUESTION_BANK,
    SKILL_QUESTION_BANK,
    GENERAL_QUESTION_BANK,
    normalize_keyword,
)

logger = logging.getLogger(__name__)

# 
# Configurable weights (overridable via environment variables)
# 
SEMANTIC_WEIGHT = float(os.getenv("INTERVIEW_SEMANTIC_WEIGHT", "0.65"))
KEYWORD_WEIGHT = float(os.getenv("INTERVIEW_KEYWORD_WEIGHT", "0.35"))

# 
# Sentence-Transformer Model Loading
# 
_model = None
MODEL_STATUS = "not_loaded"
MODEL_ERROR: Optional[str] = None

def get_model():
    global _model, MODEL_STATUS, MODEL_ERROR
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            MODEL_STATUS = "loaded"
            MODEL_ERROR = None
            logger.info("sentence-transformers model 'all-MiniLM-L6-v2' loaded successfully.")
        except Exception as e:
            MODEL_STATUS = "error"
            MODEL_ERROR = str(e)
            logger.error(f"Failed to load sentence-transformers model: {e}")
            _model = None
    return _model
def get_model_status() -> Dict:
    return {
        "status": MODEL_STATUS,
        "model": "all-MiniLM-L6-v2",
        "error": MODEL_ERROR,
        "available": _model is not None,
    }

# 
# Question Generation
# 

def _normalize_interview_type(interview_type: str) -> str:
    mapping = {
        "technical": "Technical",
        "behavioral": "Behavioral",
        "hr": "HR",
        "mixed": "Mixed",
    }
    return mapping.get(interview_type.lower(), "Mixed")


def _normalize_difficulty(difficulty: str) -> str:
    mapping = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    return mapping.get(difficulty.lower(), "Medium")


def _get_role_questions(
    predicted_role: str,
    interview_type: str,
    difficulty: str,
) -> List[Dict]:
    """Pull questions from ROLE_QUESTION_BANK for the predicted role."""
    # Try exact role match, then fuzzy match, then empty
    role_bank = ROLE_QUESTION_BANK.get(predicted_role, {})
    if not role_bank:
        # Try partial match
        for role_key in ROLE_QUESTION_BANK:
            if role_key.lower() in predicted_role.lower() or predicted_role.lower() in role_key.lower():
                role_bank = ROLE_QUESTION_BANK[role_key]
                break
    if not role_bank:
        return []

    type_bank = role_bank.get(interview_type, {})
    if not type_bank:
        return []

    # For Mixed: pull from all types
    if interview_type == "Mixed":
        questions = []
        for t in ["Technical", "Behavioral", "HR"]:
            for diff in ["Easy", "Medium", "Hard"]:
                questions.extend(role_bank.get(t, {}).get(diff, []))
        return questions

    # Exact difficulty + adjacent difficulties
    questions = list(type_bank.get(difficulty, []))
    # Pull from adjacent difficulties if we have few
    if len(questions) < 3:
        for d in ["Easy", "Medium", "Hard"]:
            if d != difficulty:
                questions.extend(type_bank.get(d, []))
    return questions


def _get_skill_questions(skills: List[str]) -> List[Dict]:
    """Pull skill-specific questions for each skill extracted from the resume."""
    questions = []
    for skill in skills:
        normalized = normalize_keyword(skill)
        # Try original, normalized, lowercase
        for key in [skill, normalized, skill.lower()]:
            if key in SKILL_QUESTION_BANK:
                questions.extend(SKILL_QUESTION_BANK[key])
                break
    return questions


def _get_general_questions(interview_type: str) -> List[Dict]:
    """Pull general fallback questions."""
    qs = list(GENERAL_QUESTION_BANK.get(interview_type, []))
    # Always include some HR and behavioral for Mixed
    if interview_type == "Mixed":
        qs.extend(GENERAL_QUESTION_BANK.get("Behavioral", []))
        qs.extend(GENERAL_QUESTION_BANK.get("HR", []))
    return qs


def _extract_jd_skills(job_description: Optional[str]) -> List[str]:
    """Extract known skill keywords from a JD text."""
    if not job_description:
        return []
    jd_lower = job_description.lower()
    found = []
    # Check against all skill question bank keys (and their aliases)
    all_skill_keys = list(SKILL_QUESTION_BANK.keys())
    for skill in all_skill_keys:
        if skill.lower() in jd_lower:
            found.append(skill)
    return found


def _deduplicate_questions(questions: List[Dict]) -> List[Dict]:
    """Remove duplicate questions by text (case-insensitive)."""
    seen = set()
    unique = []
    for q in questions:
        key = q["question"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


def _distribute_questions(
    role_qs: List[Dict],
    skill_qs: List[Dict],
    general_qs: List[Dict],
    jd_skill_qs: List[Dict],
    resume_skills: List[str],
    jd_skills: List[str],
    num_questions: int,
    interview_type: str,
) -> List[Dict]:
    """
    Distribute questions for variety:
    - Prefer role questions (~30-40%)
    - Prefer resume skill questions (~30-40%)
    - Prefer JD-overlap skill questions (prioritized if JD provided)
    - General as filler (~20-30%)

    Avoid 5 Python questions for a 5-question session.
    """
    selected = []
    used_skills = set()

    # Normalize resume skills for tracking
    norm_resume_skills = [normalize_keyword(s) for s in resume_skills]

    # Build JD-overlap skill questions first (highest priority)
    jd_overlap_skills = set(normalize_keyword(s) for s in resume_skills) & set(normalize_keyword(s) for s in jd_skills)
    jd_overlap_qs = [q for q in jd_skill_qs if any(
        normalize_keyword(s) in q["question"].lower() or normalize_keyword(s) in q.get("category", "").lower()
        for s in jd_overlap_skills
    )]

    # Budgets: aim for variety
    if num_questions <= 5:
        budget = {"role": 2, "skill": 2, "jd": 1, "general": 1}
    elif num_questions <= 7:
        budget = {"role": 2, "skill": 3, "jd": 1, "general": 2}
    else:
        budget = {"role": 3, "skill": 4, "jd": 2, "general": 3}

    # 1. JD-overlap skill questions
    random.shuffle(jd_overlap_qs)
    for q in jd_overlap_qs[:budget["jd"]]:
        if q not in selected:
            selected.append(q)

    # 2. Role questions
    random.shuffle(role_qs)
    for q in role_qs[:budget["role"]]:
        if q not in selected:
            selected.append(q)

    # 3. Resume skill questions (one per distinct skill to avoid repetition)
    random.shuffle(skill_qs)
    for q in skill_qs:
        if len([s for s in selected if s.get("category") == "skill"]) >= budget["skill"]:
            break
        if q not in selected:
            selected.append(q)

    # 4. General questions as filler
    random.shuffle(general_qs)
    for q in general_qs:
        if len(selected) >= num_questions:
            break
        if q not in selected:
            selected.append(q)

    # 5. If still not enough, fill from any pool
    all_remaining = _deduplicate_questions(role_qs + skill_qs + general_qs + jd_skill_qs)
    for q in all_remaining:
        if len(selected) >= num_questions:
            break
        if q not in selected:
            selected.append(q)

    # Final shuffle for natural order, then trim
    random.shuffle(selected)
    return selected[:num_questions]


def generate_interview_questions(
    predicted_role: str,
    resume_skills: List[str],
    interview_type: str,
    difficulty: str,
    num_questions: int = 5,
    job_description: Optional[str] = None,
) -> List[Dict]:
    """
    Generate a personalized, deduplicated, distributed set of interview questions.
    Returns list of question dicts with question, ideal_answer, keywords, category.
    """
    interview_type = _normalize_interview_type(interview_type)
    difficulty = _normalize_difficulty(difficulty)

    # Pull from each pool
    role_qs = _get_role_questions(predicted_role, interview_type, difficulty)
    skill_qs = _get_skill_questions(resume_skills)
    general_qs = _get_general_questions(interview_type)
    jd_skills = _extract_jd_skills(job_description)
    jd_skill_qs = _get_skill_questions(jd_skills) if jd_skills else []

    # Deduplicate each pool
    role_qs = _deduplicate_questions(role_qs)
    skill_qs = _deduplicate_questions(skill_qs)
    general_qs = _deduplicate_questions(general_qs)
    jd_skill_qs = _deduplicate_questions(jd_skill_qs)

    # Distribute for variety
    selected = _distribute_questions(
        role_qs, skill_qs, general_qs, jd_skill_qs,
        resume_skills, jd_skills, num_questions, interview_type
    )

    # If we still don't have enough, add any deduplicated
    if len(selected) < num_questions:
        all_pool = _deduplicate_questions(role_qs + skill_qs + general_qs + jd_skill_qs)
        random.shuffle(all_pool)
        for q in all_pool:
            if len(selected) >= num_questions:
                break
            if q not in selected:
                selected.append(q)

    logger.info(
        f"Generated {len(selected)} questions for role='{predicted_role}', "
        f"type='{interview_type}', difficulty='{difficulty}', "
        f"skills={resume_skills[:5]}, jd_skills={jd_skills[:5]}"
    )
    return selected


# 
# Answer Evaluation
# 

def _semantic_similarity(answer: str, ideal_answer: str) -> float:
    """
    Compute cosine similarity between answer and ideal_answer embeddings.
    Returns score 0–100. Raises RuntimeError if model unavailable.
    """
    model = get_model()
    if model is None:
        raise RuntimeError(
            f"Sentence-transformer model unavailable ({MODEL_ERROR}). "
            "Cannot compute semantic similarity scores. "
            "Ensure 'all-MiniLM-L6-v2' is cached or the internet is available."
        )
    embeddings = model.encode([answer, ideal_answer])
    from sklearn.metrics.pairwise import cosine_similarity
    sim = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    # Clamp to [0, 1]
    sim = max(0.0, min(1.0, sim))
    return round(sim * 100, 2)


def _keyword_coverage(answer: str, keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Compute keyword coverage score.
    Returns (score 0-100, matched_keywords, missing_keywords).
    """
    if not keywords:
        return 100.0, [], []
    answer_lower = answer.lower()
    matched = []
    missing = []
    for kw in keywords:
        norm_kw = normalize_keyword(kw)
        # Check normalized keyword and original in answer
        if norm_kw in answer_lower or kw.lower() in answer_lower:
            if norm_kw not in [normalize_keyword(m) for m in matched]:
                matched.append(kw)
        else:
            if norm_kw not in [normalize_keyword(m) for m in missing]:
                missing.append(kw)
    score = round(len(matched) / len(keywords) * 100, 2)
    return score, matched, missing


def _generate_feedback(
    combined_score: float,
    semantic_score: float,
    keyword_score: float,
    matched_keywords: List[str],
    missing_keywords: List[str],
) -> str:
    """Generate deterministic textual feedback based on score bands and missing keywords."""
    if combined_score >= 80:
        base = "Excellent answer! Your response closely aligns with the expected answer and covers key concepts well."
        if matched_keywords:
            base += f" You covered: {', '.join(matched_keywords[:5])}."
        if missing_keywords:
            base += f" You could further strengthen your answer by mentioning: {', '.join(missing_keywords[:3])}."
    elif combined_score >= 60:
        base = "Good answer. Your response captures the main idea."
        if missing_keywords:
            base += f" To make it stronger, consider expanding on: {', '.join(missing_keywords[:4])}."
        if keyword_score < 50:
            base += " Try to include more domain-specific terminology in your explanation."
    elif combined_score >= 40:
        base = "Partial answer. The core concept was addressed but important details are missing."
        if missing_keywords:
            base += f" Key concepts to include next time: {', '.join(missing_keywords[:5])}."
        if semantic_score < 40:
            base += " Try to restructure your answer to more directly address the question asked."
    else:
        base = "This answer needs significant improvement."
        if missing_keywords:
            base += f" Revisit these concepts: {', '.join(missing_keywords[:6])}."
        base += " Consider reviewing the topic and practice explaining it in your own words."

    base += (
        f" [Evaluation: semantic match {semantic_score:.0f}%, keyword coverage {keyword_score:.0f}%]"
    )
    return base


def evaluate_answer(
    user_answer: str,
    ideal_answer: str,
    keywords: List[str],
) -> Dict:
    """
    Evaluate a user's interview answer.
    Returns dict with:
      - semantic_score (0-100)
      - keyword_score (0-100)
      - combined_score (0-100)
      - matched_keywords
      - missing_keywords
      - feedback (string)
    Raises RuntimeError if the model is unavailable.
    """
    if not user_answer or not user_answer.strip():
        return {
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "combined_score": 0.0,
            "matched_keywords": [],
            "missing_keywords": keywords,
            "feedback": "No answer provided. Please provide a response to be evaluated."
        }

    # Semantic similarity (may raise RuntimeError)
    semantic_score = _semantic_similarity(user_answer, ideal_answer)

    # Keyword coverage
    keyword_score, matched_kws, missing_kws = _keyword_coverage(user_answer, keywords)

    # Combined weighted score
    combined_score = round(
        SEMANTIC_WEIGHT * semantic_score + KEYWORD_WEIGHT * keyword_score, 2
    )
    combined_score = max(0.0, min(100.0, combined_score))

    feedback = _generate_feedback(
        combined_score, semantic_score, keyword_score, matched_kws, missing_kws
    )

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "combined_score": combined_score,
        "matched_keywords": matched_kws,
        "missing_keywords": missing_kws,
        "feedback": feedback,
    }


# 
# Final Report Generation
# 

def generate_final_report(answer_records: List[Dict]) -> Dict:
    """
    Generate the final interview performance report from completed answer records.
    Each record: {question_text, category, combined_score, semantic_score, keyword_score, feedback}
    """
    if not answer_records:
        return {
            "overall_score": 0.0,
            "questions_answered": 0,
            "avg_semantic_score": 0.0,
            "avg_keyword_score": 0.0,
            "strengths": [],
            "improvement_areas": [],
        }

    scores = [r["combined_score"] for r in answer_records]
    semantic_scores = [r["semantic_score"] for r in answer_records]
    keyword_scores = [r["keyword_score"] for r in answer_records]

    overall_score = round(float(np.mean(scores)), 2)
    avg_semantic = round(float(np.mean(semantic_scores)), 2)
    avg_keyword = round(float(np.mean(keyword_scores)), 2)

    # Derive strengths from high-scoring answers
    strengths = []
    improvement_areas = []
    for r in answer_records:
        q_preview = r["question_text"][:60] + "..." if len(r["question_text"]) > 60 else r["question_text"]
        if r["combined_score"] >= 75:
            strengths.append(f"Strong on: \"{q_preview}\" (Score: {r['combined_score']:.0f})")
        elif r["combined_score"] < 50:
            improvement_areas.append(f"Needs work: \"{q_preview}\" (Score: {r['combined_score']:.0f})")

    # Add category-level insights
    categories = {}
    for r in answer_records:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["combined_score"])

    for cat, cat_scores in categories.items():
        avg_cat = np.mean(cat_scores)
        if avg_cat >= 75 and cat not in ["general"]:
            strengths.append(f"Good grasp of {cat} concepts (avg: {avg_cat:.0f})")
        elif avg_cat < 50 and cat not in ["general"]:
            improvement_areas.append(f"Review {cat} fundamentals (avg: {avg_cat:.0f})")

    return {
        "overall_score": overall_score,
        "questions_answered": len(answer_records),
        "avg_semantic_score": avg_semantic,
        "avg_keyword_score": avg_keyword,
        "strengths": strengths[:5],
        "improvement_areas": improvement_areas[:5],
    }
