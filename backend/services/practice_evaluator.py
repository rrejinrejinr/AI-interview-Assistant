import re
import json
import difflib
import logging
from typing import Dict, Any, Optional

from services.llm_provider import get_llm_provider, BaseLLMProvider, FallbackProvider

logger = logging.getLogger("practice_evaluator")
logger.setLevel(logging.INFO)


class PracticeEvaluationUnavailableError(Exception):
    """
    Raised when Groq API evaluation fails, times out, is unconfigured,
    or produces an invalid response.
    """
    pass


def normalize_eval_text(text: str) -> str:
    """
    Normalize text for deterministic similarity comparisons:
    lowercase, replace punctuation with spaces, collapse multiple spaces.
    """
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def detect_copied_or_empty_answer(
    question_text: str,
    user_answer: str,
    max_marks: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Deterministically detects:
      - Empty or whitespace-only answers.
      - Excessively short or meaningless answers (< 2 words or < 4 characters).
      - Answers that merely copy, echo, or repeat the question itself without explanation.

    Returns a dict awarding 0 marks if detected, or None if the answer passes
    pre-validation and should proceed to semantic Groq evaluation.
    """
    if not user_answer or not user_answer.strip():
        return {
            "is_correct": False,
            "confidence": 1.0,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "reason": "No answer was provided."
        }

    raw_ans = user_answer.strip()
    words = raw_ans.split()

    if len(words) < 2 or len(raw_ans) < 4:
        return {
            "is_correct": False,
            "confidence": 1.0,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "reason": "Answer is too short or incomplete to evaluate."
        }

    norm_q = normalize_eval_text(question_text)
    norm_a = normalize_eval_text(raw_ans)

    if not norm_a:
        return {
            "is_correct": False,
            "confidence": 1.0,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "reason": "Answer does not contain substantive text."
        }

    # 1. Exact match after normalization
    if norm_a == norm_q:
        return {
            "is_correct": False,
            "confidence": 1.0,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "reason": "Answer merely copies or repeats the question without providing an explanation."
        }

    # 2. Substring matching for answers of substantial length (>= 15 characters)
    if len(norm_a) >= 15:
        if norm_a in norm_q:
            return {
                "is_correct": False,
                "confidence": 1.0,
                "marks_awarded": 0,
                "max_marks": max_marks,
                "reason": "Answer merely copies or repeats the question without providing an explanation."
            }
        if norm_q in norm_a and len(norm_a) <= len(norm_q) + 20:
            return {
                "is_correct": False,
                "confidence": 1.0,
                "marks_awarded": 0,
                "max_marks": max_marks,
                "reason": "Answer merely copies or repeats the question without providing an explanation."
            }

    # 3. Sequence similarity ratio (Levenshtein / gestalt pattern matching)
    ratio = difflib.SequenceMatcher(None, norm_q, norm_a).ratio()
    if ratio >= 0.82:
        return {
            "is_correct": False,
            "confidence": 1.0,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "reason": "Answer merely copies or repeats the question without providing an explanation."
        }

    # 4. Token overlap check: if >= 88% of user's tokens come from the question and no significant extra content
    q_tokens = set(norm_q.split())
    a_tokens = set(norm_a.split())
    if len(a_tokens) > 0 and len(q_tokens) > 0:
        overlap = len(a_tokens & q_tokens) / len(a_tokens)
        if overlap >= 0.88 and len(a_tokens) <= len(q_tokens) + 2 and len(words) >= 4:
            return {
                "is_correct": False,
                "confidence": 1.0,
                "marks_awarded": 0,
                "max_marks": max_marks,
                "reason": "Answer merely copies or repeats the question without providing an explanation."
            }

    return None


def evaluate_practice_answer_with_groq(
    question_text: str,
    ideal_answer: str,
    user_answer: str,
    max_marks: int = 2,
    context: str = "",
    provider: Optional[BaseLLMProvider] = None
) -> Dict[str, Any]:
    """
    Evaluates a candidate's descriptive answer using Groq LLM.
    Strictly verifies factual correctness and conceptual understanding.
    Paraphrasing is awarded full marks if conceptually correct.
    Keyword stuffing with incorrect concepts or factually wrong claims receive 0 marks.
    Raises PracticeEvaluationUnavailableError if Groq is unavailable, times out, or fails.
    """
    if provider is None:
        provider = get_llm_provider()

    # Fail safely if no provider or fallback provider is active
    if isinstance(provider, FallbackProvider) or not getattr(provider, "api_key", None):
        logger.warning("[PracticeEvaluator] Groq provider is unconfigured or in fallback mode.")
        raise PracticeEvaluationUnavailableError(
            "Answer evaluation service is temporarily unavailable. Please try submitting again."
        )

    system_prompt = f"""You are a strict, fair, and authoritative technical interview evaluator.
Your role is to evaluate a candidate's answer to a technical practice or resume-based question.

EVALUATION CRITERIA:
1. Conceptual & Factual Correctness:
   - Compare the candidate's answer with the Reference / Ideal Answer.
   - Paraphrasing, alternative wording, or different explanations MUST BE AWARDED FULL MARKS ({max_marks}/{max_marks}) if the candidate demonstrates correct understanding of the core concept.
2. Award Zero Marks (0/{max_marks}):
   - The answer merely echoes, quotes, or rephrases the question without answering it.
   - The answer is irrelevant, nonsense, or avoids the question.
   - The answer includes keywords or jargon from the topic but asserts an incorrect, contradictory, or flawed concept (e.g. claiming Python GIL allows 100 threads to run Python bytecode concurrently across 100 cores).
   - The answer is factually wrong or demonstrates a fundamental misunderstanding.
3. Strict Marks Rule:
   - Marks are binary: either {max_marks} (if correct and conceptually sound) or 0 (if incorrect or invalid).
   - If "is_correct" is true: "marks_awarded" MUST equal {max_marks}.
   - If "is_correct" is false: "marks_awarded" MUST equal 0.
4. Response Format:
   You MUST return a valid JSON object only with NO markdown fences and no extra commentary:
   {{
     "is_correct": true,
     "confidence": 0.95,
     "marks_awarded": {max_marks},
     "max_marks": {max_marks},
     "reason": "Concise 1-2 sentence explanation of why the answer is correct or what makes it incorrect."
   }}"""

    context_block = f"\nRELEVANT CONTEXT (Resume / Role):\n{context.strip()}\n" if context and context.strip() else ""

    user_prompt = f"""QUESTION:
{question_text.strip()}

REFERENCE / IDEAL ANSWER:
{ideal_answer.strip()}
{context_block}
CANDIDATE SUBMITTED ANSWER:
{user_answer.strip()}

MAX MARKS: {max_marks}

Evaluate the candidate's answer strictly and respond with the JSON object."""

    try:
        raw_res = provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            json_mode=True
        )
    except Exception as e:
        logger.error(f"[PracticeEvaluator] Groq call raised exception: {e}")
        raise PracticeEvaluationUnavailableError(
            "Answer evaluation service is temporarily unavailable. Please try submitting again."
        )

    if not raw_res or not raw_res.strip():
        logger.error("[PracticeEvaluator] Groq returned an empty response or timed out.")
        raise PracticeEvaluationUnavailableError(
            "Answer evaluation service is temporarily unavailable. Please try submitting again."
        )

    cleaned = raw_res.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                logger.error(f"[PracticeEvaluator] Failed to parse JSON from Groq output: {raw_res[:200]}")
                raise PracticeEvaluationUnavailableError(
                    "Answer evaluation service returned an invalid response format."
                )
        else:
            logger.error(f"[PracticeEvaluator] No JSON object found in Groq output: {raw_res[:200]}")
            raise PracticeEvaluationUnavailableError(
                "Answer evaluation service returned an invalid response format."
            )

    if not isinstance(data, dict):
        raise PracticeEvaluationUnavailableError(
            "Answer evaluation service returned invalid JSON structure."
        )

    raw_is_correct = data.get("is_correct")
    if isinstance(raw_is_correct, bool):
        is_correct = raw_is_correct
    elif isinstance(raw_is_correct, str):
        is_correct = raw_is_correct.strip().lower() in ("true", "yes", "1")
    else:
        is_correct = False

    marks_awarded = max_marks if is_correct else 0
    raw_reason = str(data.get("reason", "")).strip()
    # Normalize unicode non-breaking hyphens / smart characters
    reason = raw_reason.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    if not reason:
        reason = "Correct answer demonstrated." if is_correct else "Answer did not demonstrate the required technical understanding."

    try:
        confidence = float(data.get("confidence", 0.95 if is_correct else 0.9))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.9

    return {
        "is_correct": is_correct,
        "confidence": confidence,
        "marks_awarded": marks_awarded,
        "max_marks": max_marks,
        "reason": reason
    }


def evaluate_practice_answer(
    question_text: str,
    ideal_answer: str,
    user_answer: str,
    max_marks: int = 2,
    context: str = "",
    provider: Optional[BaseLLMProvider] = None
) -> Dict[str, Any]:
    """
    Main evaluation pipeline for Fundamental Concepts and Resume-Based practice:
    1. Deterministic pre-validation (catches empty, too short, or copied questions without calling Groq).
    2. Deep semantic evaluation via Groq LLM.
    3. Returns validated evaluation dict.
    """
    pre = detect_copied_or_empty_answer(question_text, user_answer, max_marks=max_marks)
    if pre is not None:
        return pre

    return evaluate_practice_answer_with_groq(
        question_text=question_text,
        ideal_answer=ideal_answer,
        user_answer=user_answer,
        max_marks=max_marks,
        context=context,
        provider=provider
    )
