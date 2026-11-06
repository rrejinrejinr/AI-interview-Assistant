import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models_db import User, ResumeRecord, ResumeSkill, PracticeSession, SupportTicket
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_data():
    db = SessionLocal()
    # Create or retrieve test user
    test_email = "test_practice_user@example.com"
    user = db.query(User).filter(User.email == test_email).first()
    if not user:
        user = User(
            name="Practice Test Candidate",
            email=test_email,
            password_hash=get_password_hash("TestPassword123!"),
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create test resume
    resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
    if not resume:
        sample_text = (
            "Jane Doe\nEmail: jane.doe@example.com\nPhone: +1 555-0199\n"
            "Software Engineer with 4 years of experience specializing in Python, FastAPI, Docker, PostgreSQL, React, machine learning pipelines, scikit-learn, and PyTorch.\n"
            "Projects: Developed high-throughput REST API using FastAPI and PostgreSQL with redis caching. Built machine learning recommendation models using scikit-learn."
        )
        resume = ResumeRecord(
            user_id=user.id,
            filename="jane_doe_resume.pdf",
            extracted_text=sample_text,
            predicted_role="Python Developer",
            email="jane.doe@example.com",
            phone="+1 555-0199",
            years_of_experience="4 years"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Add skills
        skills = ["Python", "FastAPI", "Docker", "PostgreSQL", "React", "Machine Learning", "scikit-learn", "PyTorch"]
        for s in skills:
            db.add(ResumeSkill(resume_id=resume.id, skill_name=s, category="Technical"))
        db.commit()

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    yield {
        "user": user,
        "resume": resume,
        "headers": headers,
        "db": db
    }

    db.close()

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

def test_practice_10_questions(setup_test_data):
    headers = setup_test_data["headers"]
    resume_id = setup_test_data["resume"].id

    payload = {
        "resume_id": resume_id,
        "question_count": 10,
        "difficulty": "Medium",
        "practice_type": "Technical"
    }
    res = client.post("/api/practice/start", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["question_count"] == 10
    assert len(data["questions"]) == 10
    assert data["status"] == "in_progress"
    # Ensure ideal_answer and keywords are NOT leaked to candidate
    for q in data["questions"]:
        assert "ideal_answer" not in q
        assert "keywords" not in q
        assert "question_text" in q
        assert "id" in q

def test_practice_20_questions(setup_test_data):
    headers = setup_test_data["headers"]
    resume_id = setup_test_data["resume"].id

    payload = {
        "resume_id": resume_id,
        "question_count": 20,
        "difficulty": "Medium",
        "practice_type": "Technical"
    }
    res = client.post("/api/practice/start", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["question_count"] == 20
    assert len(data["questions"]) == 20

def test_practice_30_questions(setup_test_data):
    headers = setup_test_data["headers"]
    resume_id = setup_test_data["resume"].id

    payload = {
        "resume_id": resume_id,
        "question_count": 30,
        "difficulty": "Hard",
        "practice_type": "Mixed"
    }
    res = client.post("/api/practice/start", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["question_count"] == 30
    assert len(data["questions"]) == 30

def test_practice_session_answer_flow(setup_test_data):
    headers = setup_test_data["headers"]
    resume_id = setup_test_data["resume"].id

    # 1. Start 10-question session
    payload = {
        "resume_id": resume_id,
        "question_count": 10,
        "difficulty": "Medium",
        "practice_type": "Technical"
    }
    start_res = client.post("/api/practice/start", json=payload, headers=headers)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    first_q = session_data["questions"][0]

    # 2. Get session details
    get_res = client.get(f"/api/practice/{session_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["session_id"] == session_id

    # 3. Submit answer to first question
    ans_payload = {
        "question_id": first_q["id"],
        "user_answer": "In Python and FastAPI, we build asynchronous REST APIs with type safety using Pydantic schemas, dependency injection for database sessions, and asynchronous async/await endpoints for high throughput."
    }
    ans_res = client.post(f"/api/practice/{session_id}/answer", json=ans_payload, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert "combined_score" in ans_data
    assert "semantic_score" in ans_data
    assert "keyword_score" in ans_data
    assert "feedback" in ans_data
    assert ans_data["combined_score"] > 0

    # 4. Complete session
    comp_res = client.post(f"/api/practice/{session_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    report_data = comp_res.json()
    assert report_data["status"] == "completed"
    assert "overall_score" in report_data
    assert "strengths" in report_data
    assert "improvement_areas" in report_data
    assert len(report_data["questions_and_answers"]) == 10

    # 5. Retrieve past practice sessions
    history_res = client.get("/api/practice/sessions", headers=headers)
    assert history_res.status_code == 200
    sessions_list = history_res.json()
    assert len(sessions_list) >= 1
    assert any(s["session_id"] == session_id for s in sessions_list)

    # 6. Retrieve practice report directly
    report_res = client.get(f"/api/practice/{session_id}/report", headers=headers)
    assert report_res.status_code == 200
    assert report_res.json()["session_id"] == session_id

def test_support_ticket_and_chatbot(setup_test_data):
    headers = setup_test_data["headers"]

    # 1. Chatbot query
    chat_payload = {"query": "How does the practice voice input work?"}
    chat_res = client.post("/api/support/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "10, 20, or 30" in chat_data["answer"] or "voice" in chat_data["answer"].lower()

    # 2. Submit Support Ticket (Complaint)
    ticket_payload = {
        "name": "Jane Doe",
        "email": "janedoe@example.com",
        "category": "Practice & Voice Input",
        "subject": "Microphone permission assistance",
        "description": "Testing the complaint ticket submission flow. My microphone input is working smoothly with Web Speech API."
    }
    ticket_res = client.post("/api/support/ticket", json=ticket_payload, headers=headers)
    assert ticket_res.status_code == 200
    ticket_data = ticket_res.json()
    assert ticket_data["ticket_id"].startswith("TICK-")
    assert ticket_data["status"] == "Open"
    assert "email_dispatched" in ticket_data

    # 3. Retrieve user support tickets
    list_res = client.get("/api/support/tickets", headers=headers)
    assert list_res.status_code == 200
    tickets = list_res.json()
    assert len(tickets) >= 1
    assert any(t["ticket_id"] == ticket_data["ticket_id"] for t in tickets)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
