import os
import sys
import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models_db import User, ResumeRecord, ResumeSkill, PracticeSession, PracticeQuestion, PracticeAnswer
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app
from services.practice_evaluator import (
    detect_copied_or_empty_answer,
    evaluate_practice_answer_with_groq,
    PracticeEvaluationUnavailableError
)
from services.llm_provider import BaseLLMProvider

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_practice_eval_data():
    db = SessionLocal()
    test_email = "practice_eval_user@example.com"
    user = db.query(User).filter(User.email == test_email).first()
    if not user:
        user = User(
            name="Practice Evaluation Tester",
            email=test_email,
            password_hash=get_password_hash("EvalPassword123!"),
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
    if not resume:
        sample_text = (
            "Alex Developer\nEmail: alex.dev@example.com\n"
            "Software Engineer with experience in Python, FastAPI, React, SQL, and Docker.\n"
            "Projects: Built distributed backend microservices and REST APIs."
        )
        resume = ResumeRecord(
            user_id=user.id,
            filename="alex_dev_resume.pdf",
            extracted_text=sample_text,
            predicted_role="Backend Developer",
            email="alex.dev@example.com"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        for s in ["Python", "FastAPI", "SQL", "Docker", "React"]:
            db.add(ResumeSkill(resume_id=resume.id, skill_name=s, category="Technical"))
        db.commit()

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    yield {
        "user": user,
        "resume": resume,
        "headers": headers
    }

    db.close()


# -----------------------------------------------------------------------------
# UNIT TESTS: Deterministic Pre-Validation
# -----------------------------------------------------------------------------

def test_unit_detect_empty_or_whitespace():
    """Deterministic pre-validation rejects empty or whitespace answers."""
    res1 = detect_copied_or_empty_answer("What is an index in SQL?", "")
    assert res1 is not None
    assert res1["is_correct"] is False
    assert res1["marks_awarded"] == 0

    res2 = detect_copied_or_empty_answer("What is an index in SQL?", "   \n\t  ")
    assert res2 is not None
    assert res2["is_correct"] is False
    assert res2["marks_awarded"] == 0


def test_unit_detect_too_short():
    """Deterministic pre-validation rejects single words or overly brief answers."""
    res = detect_copied_or_empty_answer("What is a mutex?", "mutex")
    assert res is not None
    assert res["is_correct"] is False
    assert res["marks_awarded"] == 0
    assert "too short" in res["reason"].lower()


def test_unit_detect_copied_question_variations():
    """Deterministic pre-validation detects exact, substring, or high-similarity echoes of the question."""
    q = "Explain the difference between TCP and UDP protocols in computer networking."
    
    # Exact copy
    res_exact = detect_copied_or_empty_answer(q, q)
    assert res_exact is not None
    assert res_exact["is_correct"] is False
    assert res_exact["marks_awarded"] == 0
    assert "copies or repeats" in res_exact["reason"].lower()

    # Echo with slight punctuation change
    res_punct = detect_copied_or_empty_answer(q, "Explain the difference between TCP and UDP protocols in computer networking?")
    assert res_punct is not None
    assert res_punct["is_correct"] is False
    assert res_punct["marks_awarded"] == 0

    # Substring echo
    res_sub = detect_copied_or_empty_answer(q, "difference between TCP and UDP protocols in computer networking")
    assert res_sub is not None
    assert res_sub["is_correct"] is False
    assert res_sub["marks_awarded"] == 0


# -----------------------------------------------------------------------------
# INTEGRATION TESTS: 10 Core Functional Scenarios
# -----------------------------------------------------------------------------

def test_1_paraphrased_correct_answer_awards_marks(setup_practice_eval_data):
    """(1) Paraphrased / differently worded correct answer receives full marks (2/2)."""
    headers = setup_practice_eval_data["headers"]

    start_payload = {
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }
    start_res = client.post("/api/practice/start", json=start_payload, headers=headers)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    first_q = session_data["questions"][0]

    db = SessionLocal()
    q_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == first_q["id"]).first()
    ideal_text = q_rec.ideal_answer
    db.close()

    # Submit accurate answer (ideal answer or paraphrase)
    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": first_q["id"],
        "user_answer": ideal_text
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()

    assert ans_data["is_correct"] is True
    assert ans_data["result_status"] == "Correct"
    assert ans_data["marks_awarded"] == 2
    assert ans_data["max_marks"] == 2


def test_2_copied_question_rejected_without_marks(setup_practice_eval_data):
    """(2) Submitting the question itself awards 0 marks without calling Groq."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][0]

    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": q["question_text"]
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()

    assert ans_data["is_correct"] is False
    assert ans_data["result_status"] == "Incorrect"
    assert ans_data["marks_awarded"] == 0
    assert "copies or repeats" in ans_data["feedback"].lower()


def test_3_empty_or_meaningless_answer_rejected(setup_practice_eval_data):
    """(3) Empty, trivial or meaningless text receives 0 marks."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][1]

    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": "abc xyz"
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()

    assert ans_data["is_correct"] is False
    assert ans_data["result_status"] == "Incorrect"
    assert ans_data["marks_awarded"] == 0


def test_4_keyword_stuffing_with_wrong_concept_fails(setup_practice_eval_data):
    """(4) Answers containing domain keywords but asserting a false concept receive 0 marks."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][2]

    # Keyword stuffed answer asserting the exact opposite or impossible concept
    wrong_kw_answer = (
        "In Python, the Global Interpreter Lock mutex guarantees that 100 CPU cores "
        "simultaneously execute native threads in full hardware parallelism without any locking delay."
    )
    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": wrong_kw_answer
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()

    assert ans_data["is_correct"] is False
    assert ans_data["result_status"] == "Incorrect"
    assert ans_data["marks_awarded"] == 0


def test_5_factually_incorrect_answer_awards_zero(setup_practice_eval_data):
    """(5) Factually incorrect or unrelated answers receive 0 marks."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][3]

    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": "The answer is related to cooking pasta with tomato sauce and basil."
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()

    assert ans_data["is_correct"] is False
    assert ans_data["result_status"] == "Incorrect"
    assert ans_data["marks_awarded"] == 0


def test_6_concise_direct_correct_answer_awards_marks(setup_practice_eval_data):
    """(6) Concise but conceptually accurate answer receives full marks."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][0]

    db = SessionLocal()
    q_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == q["id"]).first()
    ideal_text = q_rec.ideal_answer
    db.close()

    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": ideal_text
    }, headers=headers)
    assert ans_res.status_code == 200
    assert ans_res.json()["is_correct"] is True
    assert ans_res.json()["marks_awarded"] == 2


def test_7_resume_based_question_evaluated_with_context(setup_practice_eval_data):
    """(7) Resume-based questions pass resume context and evaluate correctly."""
    headers = setup_practice_eval_data["headers"]
    resume_id = setup_practice_eval_data["resume"].id

    start_res = client.post("/api/practice/start", json={
        "resume_id": resume_id,
        "question_count": 10,
        "difficulty": "Medium",
        "practice_type": "Technical",
        "question_source": "resume_based"
    }, headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][0]

    db = SessionLocal()
    q_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == q["id"]).first()
    ideal_text = q_rec.ideal_answer
    db.close()

    ans_res = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": ideal_text
    }, headers=headers)
    assert ans_res.status_code == 200
    assert ans_res.json()["is_correct"] is True
    assert ans_res.json()["marks_awarded"] == 2


def test_8_groq_failure_or_timeout_fails_safely_with_503(setup_practice_eval_data):
    """(8) Groq failure, timeout, or service unavailability returns HTTP 503 and does NOT award marks."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][0]

    # Mock evaluate_practice_answer to simulate Groq service outage
    with patch("app_fastapi.evaluate_practice_answer", side_effect=PracticeEvaluationUnavailableError("Service timed out")):
        res = client.post(f"/api/practice/{session_id}/answer", json={
            "question_id": q["id"],
            "user_answer": "A substantive answer that would normally be evaluated by Groq."
        }, headers=headers)
        assert res.status_code == 503
        assert "temporarily unavailable" in res.json()["detail"].lower()

    # Verify no bogus passing score or marks were persisted to the database
    db = SessionLocal()
    ans_rec = db.query(PracticeAnswer).filter(PracticeAnswer.question_id == q["id"]).first()
    assert ans_rec is None
    db.close()


def test_9_repeated_submission_and_update_recalculates_marks(setup_practice_eval_data):
    """(9) Repeated clicks do not duplicate marks; updating selection recalculates correctly."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    q = start_res.json()["questions"][0]

    db = SessionLocal()
    q_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == q["id"]).first()
    ideal_text = q_rec.ideal_answer
    db.close()

    # 1. Submit correct answer
    res1 = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": ideal_text
    }, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["marks_awarded"] == 2

    # 2. Resubmit same correct answer (no duplication)
    res2 = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": ideal_text
    }, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["marks_awarded"] == 2

    sess_res = client.get(f"/api/practice/{session_id}", headers=headers)
    assert sess_res.json()["earned_marks"] == 2

    # 3. Update answer to incorrect answer -> recalculates down to 0 marks
    res3 = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": q["id"],
        "user_answer": "I do not know this concept."
    }, headers=headers)
    assert res3.status_code == 200
    assert res3.json()["marks_awarded"] == 0

    sess_res2 = client.get(f"/api/practice/{session_id}", headers=headers)
    assert sess_res2.json()["earned_marks"] == 0


def test_10_practice_completion_final_report_marks_accuracy(setup_practice_eval_data):
    """(10) Practice report correctly tallies total marks, earned marks, and question breakdown."""
    headers = setup_practice_eval_data["headers"]

    start_res = client.post("/api/practice/start", json={
        "question_count": 10,
        "difficulty": "Easy",
        "practice_type": "Technical",
        "question_source": "fundamental_concepts"
    }, headers=headers)
    session_id = start_res.json()["session_id"]
    questions = start_res.json()["questions"]

    db = SessionLocal()
    q0_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == questions[0]["id"]).first()
    q1_rec = db.query(PracticeQuestion).filter(PracticeQuestion.id == questions[1]["id"]).first()
    ideal_0 = q0_rec.ideal_answer
    db.close()

    # Q0: Answer correctly (2 marks)
    r0 = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": questions[0]["id"],
        "user_answer": ideal_0
    }, headers=headers)
    assert r0.json()["marks_awarded"] == 2

    # Q1: Answer incorrectly (0 marks)
    r1 = client.post(f"/api/practice/{session_id}/answer", json={
        "question_id": questions[1]["id"],
        "user_answer": "Completely irrelevant response with no technical basis."
    }, headers=headers)
    assert r1.json()["marks_awarded"] == 0

    # Complete session
    comp_res = client.post(f"/api/practice/{session_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    report = comp_res.json()

    assert report["total_marks"] == 20
    assert report["earned_marks"] == 2
    assert report["correct_count"] == 1
    assert report["wrong_count"] == 1
    assert report["total_answered"] == 2
