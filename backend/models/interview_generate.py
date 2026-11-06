"""
LEGACY FILE — NOT USED IN PRODUCTION

Replaced in Phase 6 by:
  - backend/models/question_bank.py
  - backend/models/interview_engine.py
  - backend/services/llm_service.py

Preserved for reference only.
"""

def generate_questions(skills):
    return [f"Explain {s}" for s in (skills or [])]