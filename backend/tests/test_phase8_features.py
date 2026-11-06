import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models_db import User, ResumeRecord, ResumeSkill, InterviewSession, InterviewQuestion, InterviewAnswer, PracticeSession
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app
from models.mock_interview_engine import generate_mock_interview_30_questions, calculate_mock_interview_report
from models.ai_one_to_one_engine import generate_initial_hr_question, generate_next_hr_response, evaluate_one_to_one_interview
from models.practice_engine import generate_practice_questions

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_phase8_test_data():
    db = SessionLocal()
    
    # 1. Candidate User A
    user_a_email = "phase8_candidate_a@example.com"
    user_a = db.query(User).filter(User.email == user_a_email).first()
    if not user_a:
        user_a = User(
            name="Sarah Connor",
            email=user_a_email,
            password_hash=get_password_hash("Password123!"),
            email_verified=True
        )
        db.add(user_a)
        db.commit()
        db.refresh(user_a)

    # 2. Candidate User B (for cross-user isolation test)
    user_b_email = "phase8_candidate_b@example.com"
    user_b = db.query(User).filter(User.email == user_b_email).first()
    if not user_b:
        user_b = User(
            name="John Connor",
            email=user_b_email,
            password_hash=get_password_hash("Password123!"),
            email_verified=True
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

    # 3. Resume for User A
    resume_a = db.query(ResumeRecord).filter(ResumeRecord.user_id == user_a.id).first()
    if not resume_a:
        sample_text = (
            "Sarah Connor\nEmail: sarah.connor@example.com\nPhone: +1 555-0188\n"
            "Summary: Senior Backend and Cloud Systems Engineer with 5 years experience in Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, and Distributed Microservices.\n"
            "Experience: Built high-throughput API gateway processing 50k requests/sec using FastAPI and Redis caching. Designed relational database schemas in PostgreSQL.\n"
            "Projects: Project CyberShield Distributed Security Monitoring System using Python, WebSockets, and PyTorch for anomaly detection.\n"
            "Education: Bachelor of Science in Computer Science from Stanford University."
        )
        resume_a = ResumeRecord(
            user_id=user_a.id,
            filename="sarah_connor_resume.pdf",
            extracted_text=sample_text,
            predicted_role="Backend Developer",
            email="sarah.connor@example.com",
            phone="+1 555-0188",
            years_of_experience="5 years"
        )
        db.add(resume_a)
        db.commit()
        db.refresh(resume_a)

        skills = ["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "Redis", "WebSockets", "PyTorch"]
        for s in skills:
            db.add(ResumeSkill(resume_id=resume_a.id, skill_name=s, category="Technical"))
        db.commit()

    token_a = create_access_token(data={"sub": user_a.email, "user_id": user_a.id})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    token_b = create_access_token(data={"sub": user_b.email, "user_id": user_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    yield {
        "user_a": user_a,
        "user_b": user_b,
        "resume_a": resume_a,
        "headers_a": headers_a,
        "headers_b": headers_b,
        "db": db
    }

    db.close()

# 
# 1. Mock Interview Engine & API Tests
# 

def test_mock_interview_30_questions_generation(setup_phase8_test_data):
    resume = setup_phase8_test_data["resume_a"]
    skills = ["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL", "Redis", "WebSockets", "PyTorch"]
    
    for diff in ["Easy", "Medium", "Hard"]:
        questions = generate_mock_interview_30_questions(
            resume_text=resume.extracted_text,
            skills=skills,
            predicted_role="Backend Developer",
            difficulty=diff
        )
        assert len(questions) == 30
        for q in questions:
            assert "question" in q
            assert "category" in q
            assert "ideal_answer" in q
            assert "keywords" in q
            assert len(q["keywords"]) >= 1

def test_mock_interview_api_start_and_sanitization(setup_phase8_test_data):
    headers = setup_phase8_test_data["headers_a"]
    resume_id = setup_phase8_test_data["resume_a"].id

    payload = {
        "resume_id": resume_id,
        "difficulty": "Hard"
    }
    res = client.post("/api/mock-interview/start", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["num_questions"] == 30
    assert len(data["questions"]) == 30
    assert data["status"] == "pending"
    assert data["verification_completed"] is False

    # Security check: Ensure ideal_answer and keywords are NOT exposed to frontend
    for q in data["questions"]:
        assert "ideal_answer" not in q
        assert "keywords" not in q
        assert "id" in q
        assert "question_text" in q

def test_mock_interview_verification_and_flow(setup_phase8_test_data):
    headers = setup_phase8_test_data["headers_a"]
    resume_id = setup_phase8_test_data["resume_a"].id

    # 1. Start session
    start_res = client.post("/api/mock-interview/start", json={"resume_id": resume_id, "difficulty": "Medium"}, headers=headers)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    first_q = session_data["questions"][0]

    # 2. Verify Photo
    verify_res = client.post(f"/api/mock-interview/{session_id}/verify-photo", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_completed"] is True
    assert verify_res.json()["photo_verified"] is True
    assert verify_res.json()["status"] == "in_progress"

    # 3. Get session details
    get_res = client.get(f"/api/mock-interview/{session_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["verification_completed"] is True

    # 4. Submit Answer
    ans_res = client.post(f"/api/mock-interview/{session_id}/answer", json={
        "question_id": first_q["id"],
        "user_answer": "In Python and FastAPI, we design high-throughput microservices using asynchronous async/await endpoints, connection pools with asyncpg for PostgreSQL, and Redis clusters for distributed sub-millisecond caching."
    }, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert "combined_score" in ans_data
    assert "semantic_score" in ans_data
    assert "keyword_score" in ans_data
    assert ans_data["combined_score"] > 0

    # 5. Complete session
    comp_res = client.post(f"/api/mock-interview/{session_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    report = comp_res.json()
    assert report["status"] == "completed"
    assert report["num_questions"] == 30
    assert "overall_score" in report
    assert len(report["questions_and_answers"]) == 30

    # 6. Retrieve report
    rep_res = client.get(f"/api/mock-interview/{session_id}/report", headers=headers)
    assert rep_res.status_code == 200
    assert rep_res.json()["session_id"] == session_id

def test_mock_interview_malpractice_rejection(setup_phase8_test_data):
    headers = setup_phase8_test_data["headers_a"]
    resume_id = setup_phase8_test_data["resume_a"].id

    # 1. Start session
    start_res = client.post("/api/mock-interview/start", json={"resume_id": resume_id, "difficulty": "Medium"}, headers=headers)
    session_id = start_res.json()["session_id"]

    # 2. Trigger Malpractice Rejection
    rej_payload = {
        "reason": "Face was not continuously present in the camera frame for more than 15 seconds."
    }
    rej_res = client.post(f"/api/mock-interview/{session_id}/reject", json=rej_payload, headers=headers)
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    assert rej_data["status"] == "REJECTED_INTEGRITY_VIOLATION"
    assert rej_data["integrity_status"] == "REJECTED"
    assert "Face was not continuously present" in rej_data["rejection_reason"]
    assert "email_dispatched" in rej_data

    # 3. Submitting answers to rejected session should be blocked
    ans_res = client.post(f"/api/mock-interview/{session_id}/answer", json={
        "question_id": 1,
        "user_answer": "Testing blocked answer"
    }, headers=headers)
    assert ans_res.status_code == 400

# 
# 2. AI One-to-One Interview Tests
# 

def test_ai_one_to_one_interview_flow(setup_phase8_test_data):
    headers = setup_phase8_test_data["headers_a"]
    resume_id = setup_phase8_test_data["resume_a"].id

    # 1. Start AI interview
    start_res = client.post("/api/ai-interview/start", json={"resume_id": resume_id}, headers=headers)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert "first_message" in session_data
    assert len(session_data["conversation_transcript"]) == 1

    # 2. Send candidate response turn 1
    msg1_res = client.post(f"/api/ai-interview/{session_id}/message", json={
        "message": "I have over 5 years of experience architecting distributed backend services with FastAPI and PostgreSQL, specializing in high-throughput API gateways and Redis caching."
    }, headers=headers)
    assert msg1_res.status_code == 200
    data1 = msg1_res.json()
    assert "ai_message" in data1
    assert len(data1["conversation_transcript"]) == 3 # Initial AI + Candidate + Follow-up AI

    # 3. Send candidate response turn 2
    msg2_res = client.post(f"/api/ai-interview/{session_id}/message", json={
        "message": "In my CyberShield project, we mitigated latency bottlenecks by decoupling data ingestion with WebSockets and running PyTorch model inference in dedicated worker pools."
    }, headers=headers)
    assert msg2_res.status_code == 200
    data2 = msg2_res.json()
    assert len(data2["conversation_transcript"]) == 5

    # 4. Complete AI interview
    comp_res = client.post(f"/api/ai-interview/{session_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    report = comp_res.json()
    assert report["status"] == "completed"
    assert "overall_score" in report
    assert "communication_score" in report
    assert "response_clarity_score" in report
    assert len(report["strengths"]) >= 1

    # 5. List AI interview sessions
    list_res = client.get("/api/ai-interview/sessions", headers=headers)
    assert list_res.status_code == 200
    assert any(s["session_id"] == session_id for s in list_res.json())

# 
# 3. Practice Question Source Selection Tests
# 

def test_practice_sources(setup_phase8_test_data):
    headers = setup_phase8_test_data["headers_a"]
    resume_id = setup_phase8_test_data["resume_a"].id

    for src in ["fundamental_concepts", "problem_solving", "resume_based"]:
        payload = {
            "resume_id": resume_id,
            "question_source": src,
            "question_count": 10,
            "difficulty": "Medium",
            "practice_type": "Technical"
        }
        res = client.post("/api/practice/start", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["question_count"] == 10
        assert len(data["questions"]) == 10

# 
# 4. User Isolation & Security Tests
# 

def test_user_isolation_blocks_cross_user_access(setup_phase8_test_data):
    headers_a = setup_phase8_test_data["headers_a"]
    headers_b = setup_phase8_test_data["headers_b"]
    resume_id_a = setup_phase8_test_data["resume_a"].id

    # User A starts session
    res_a = client.post("/api/mock-interview/start", json={"resume_id": resume_id_a, "difficulty": "Medium"}, headers=headers_a)
    session_id = res_a.json()["session_id"]

    # User B tries to access User A's session -> should return 404
    res_b = client.get(f"/api/mock-interview/{session_id}", headers=headers_b)
    assert res_b.status_code == 404

    # User B tries to start session with User A's resume -> should return 404
    res_b_start = client.post("/api/mock-interview/start", json={"resume_id": resume_id_a, "difficulty": "Medium"}, headers=headers_b)
    assert res_b_start.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
