import os
import sys
import io
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models_db import User, ResumeRecord, JobDescription, AtsResult, InterviewSession
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app
import app_fastapi

RESUME_A_TEXT = """
Alice Walker - Full Stack Developer
Email: alice.walker@example.com | Phone: +1 555-0101 | New York, NY
Summary: Experienced Full Stack Engineer with 4 years of expertise in React, Node.js, TypeScript, PostgreSQL, and AWS cloud infrastructure.

Experience:
Senior Software Engineer - Tech Solutions (2021 - Present)
- Architected and deployed microservices using Node.js, Express, and PostgreSQL handling 50k daily active requests.
- Developed dynamic responsive single-page applications using React, TypeScript, Redux, and Tailwind CSS.
- Implemented CI/CD pipelines with GitHub Actions and Docker containerization on AWS ECS.

Education:
B.S. in Computer Science - New York University (2020)

Skills:
React, TypeScript, JavaScript, Node.js, Express, PostgreSQL, MongoDB, Docker, AWS, Git, REST APIs
"""

RESUME_B_TEXT = """
Bob Vance - Python Data Engineer & ML Developer
Email: bob.vance@example.com | Phone: +1 555-0202 | Austin, TX
Summary: Data Engineer and ML Specialist specializing in Python, PyTorch, Pandas, Apache Spark, and SQL.

Experience:
Lead Data Engineer - Data Corp (2022 - Present)
- Built distributed ETL data pipelines processing 2TB daily streaming data using Apache Spark, Kafka, and Python.
- Trained machine learning classification algorithms with Scikit-Learn and PyTorch achieving 94% accuracy.
- Managed snowflake data warehouse and optimized complex SQL queries reducing execution time by 45%.

Education:
M.S. in Data Science - University of Texas at Austin (2021)

Skills:
Python, PyTorch, Scikit-Learn, Pandas, NumPy, Apache Spark, SQL, Kafka, Docker, Kubernetes, GCP
"""

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

class TestResumeFeatureIntegrationV2:
    """
    Validates the 8 scenarios from the Centralized Resume-Based Feature Access specification:
    1. New user with no resume -> all 5 features return clean 400 empty state
    2. Upload Resume A -> all 5 features use Resume A
    3. Single source of truth (no duplicate upload endpoints required)
    4. Browser refresh -> active resume remains Resume A
    5. Upload Resume B -> all 5 features switch to Resume B
    6. ATS result provides percentage score without breaking scoring formula
    7. Interview history remains accessible after resume replacement
    8. User isolation enforced across all endpoints
    """

    def _get_or_create_user(self, db, email, name):
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                name=name,
                password_hash=get_password_hash("Password123!"),
                email_verified=True
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        return u

    def test_complete_resume_integration_flow(self, client, db_session, monkeypatch):
        # Setup test users
        user_main = self._get_or_create_user(db_session, "v2_test_main@example.com", "Main Candidate")
        user_main.active_resume_id = None
        db_session.query(ResumeRecord).filter(ResumeRecord.user_id == user_main.id).delete()
        db_session.commit()

        token_main = create_access_token({"sub": user_main.email, "id": user_main.id})
        headers_main = {"Authorization": f"Bearer {token_main}"}

        # Mock heavy dependencies
        current_text = {"text": RESUME_A_TEXT}
        monkeypatch.setattr(app_fastapi, "extract_resume_text", lambda path: current_text["text"])
        monkeypatch.setattr(
            app_fastapi,
            "generate_initial_hr_question",
            lambda resume_text, skills, predicted_role, force_fallback=False: {
                "step_index": 0,
                "stage": "introduction",
                "speaker": "ai_interviewer",
                "question": f"Welcome to your interview for {predicted_role}.",
                "message": f"Welcome to your interview for {predicted_role}."
            }
        )

        # =====================================================================
        # SCENARIO 1: New user with no resume -> all 5 features show empty state
        # =====================================================================
        # 1. Extracted Skills endpoint
        resp = client.get("/api/resume/active", headers=headers_main)
        assert resp.status_code == 400
        assert "upload your resume" in resp.json()["detail"].lower()

        # 2. ATS Analysis endpoint
        resp = client.post("/api/ats/analyze", json={}, headers=headers_main)
        assert resp.status_code == 400
        assert "upload your resume" in resp.json()["detail"].lower()

        # 3. AI Recommendations endpoint
        resp = client.post("/api/recommendations/analyze", json={}, headers=headers_main)
        assert resp.status_code == 400
        assert "upload your resume" in resp.json()["detail"].lower()

        # 4. Mock Interview endpoint
        resp = client.post("/api/mock-interview/start", json={"difficulty": "Medium"}, headers=headers_main)
        assert resp.status_code == 400
        assert "upload your resume" in resp.json()["detail"].lower()

        # 5. HR Interview endpoint
        resp = client.post("/api/ai-interview/start", json={}, headers=headers_main)
        assert resp.status_code == 400
        assert "upload your resume" in resp.json()["detail"].lower()

        # =====================================================================
        # SCENARIO 2: Upload Resume A -> all 5 features use Resume A
        # =====================================================================
        current_text["text"] = RESUME_A_TEXT
        file_a = io.BytesIO(b"%PDF-1.4 dummy pdf binary stream for Alice")
        resp_upload_a = client.post(
            "/api/resume/upload",
            files={"resume": ("Alice_Resume.pdf", file_a, "application/pdf")},
            headers=headers_main
        )
        assert resp_upload_a.status_code == 200
        data_a = resp_upload_a.json()
        resume_a_id = data_a["resume_id"]
        assert resume_a_id is not None
        assert data_a["filename"] == "Alice_Resume.pdf"
        assert data_a["active_resume_id"] == resume_a_id

        # 1. Extracted Skills uses Resume A
        resp_skills_a = client.get("/api/resume/active", headers=headers_main)
        assert resp_skills_a.status_code == 200
        assert resp_skills_a.json()["id"] == resume_a_id
        assert "React" in resp_skills_a.json()["skills_list"]

        # 2. ATS Analysis uses Resume A automatically
        resp_ats_a = client.post("/api/ats/analyze", json={"job_title": "Full Stack"}, headers=headers_main)
        assert resp_ats_a.status_code == 200
        assert resp_ats_a.json()["resume_id"] == resume_a_id
        assert resp_ats_a.json()["resume_filename"] == "Alice_Resume.pdf"
        assert resp_ats_a.json()["ats_score"] > 0

        # 3. AI Recommendations uses Resume A
        resp_rec_a = client.post("/api/recommendations/analyze", json={}, headers=headers_main)
        assert resp_rec_a.status_code == 200
        assert "React" in resp_rec_a.json().get("current_skills", [])

        # 4. Mock Interview uses Resume A
        resp_mock_a = client.post("/api/mock-interview/start", json={"difficulty": "Medium"}, headers=headers_main)
        assert resp_mock_a.status_code == 200
        mock_a = resp_mock_a.json()
        assert mock_a["resume_id"] == resume_a_id
        assert mock_a["num_questions"] == 30
        session_a_id = mock_a["session_id"]

        # 5. HR Interview uses Resume A
        resp_hr_a = client.post("/api/ai-interview/start", json={}, headers=headers_main)
        assert resp_hr_a.status_code == 200
        assert resp_hr_a.json()["resume_id"] == resume_a_id
        assert resp_hr_a.json()["resume_filename"] == "Alice_Resume.pdf"

        # =====================================================================
        # SCENARIO 4: Browser refresh -> Resume A remains active
        # =====================================================================
        resp_refresh = client.get("/api/auth/me", headers=headers_main)
        assert resp_refresh.status_code == 200
        assert resp_refresh.json()["active_resume_id"] == resume_a_id

        resp_active_refresh = client.get("/api/resume/active", headers=headers_main)
        assert resp_active_refresh.status_code == 200
        assert resp_active_refresh.json()["id"] == resume_a_id

        # =====================================================================
        # SCENARIO 5: Upload Resume B -> all 5 features switch to Resume B
        # =====================================================================
        current_text["text"] = RESUME_B_TEXT
        file_b = io.BytesIO(b"%PDF-1.4 dummy pdf binary stream for Bob")
        resp_upload_b = client.post(
            "/api/resume/upload",
            files={"resume": ("Bob_Resume.pdf", file_b, "application/pdf")},
            headers=headers_main
        )
        assert resp_upload_b.status_code == 200
        data_b = resp_upload_b.json()
        resume_b_id = data_b["resume_id"]
        assert resume_b_id != resume_a_id
        assert data_b["active_resume_id"] == resume_b_id

        # 1. Extracted Skills switches to Resume B
        resp_skills_b = client.get("/api/resume/active", headers=headers_main)
        assert resp_skills_b.status_code == 200
        assert resp_skills_b.json()["id"] == resume_b_id
        assert "Python" in resp_skills_b.json()["skills_list"]
        assert "PyTorch" in resp_skills_b.json()["skills_list"]

        # 2. ATS Analysis switches to Resume B
        resp_ats_b = client.post("/api/ats/analyze", json={"job_title": "Data Engineer"}, headers=headers_main)
        assert resp_ats_b.status_code == 200
        assert resp_ats_b.json()["resume_id"] == resume_b_id
        assert resp_ats_b.json()["resume_filename"] == "Bob_Resume.pdf"
        assert "Python" in resp_ats_b.json()["matched_skills"]

        # 3. AI Recommendations switches to Resume B
        resp_rec_b = client.post("/api/recommendations/analyze", json={}, headers=headers_main)
        assert resp_rec_b.status_code == 200
        assert "Python" in resp_rec_b.json().get("current_skills", [])

        # 4. Mock Interview switches to Resume B
        resp_mock_b = client.post("/api/mock-interview/start", json={"difficulty": "Hard"}, headers=headers_main)
        assert resp_mock_b.status_code == 200
        assert resp_mock_b.json()["resume_id"] == resume_b_id

        # 5. HR Interview switches to Resume B
        resp_hr_b = client.post("/api/ai-interview/start", json={}, headers=headers_main)
        assert resp_hr_b.status_code == 200
        assert resp_hr_b.json()["resume_id"] == resume_b_id
        assert resp_hr_b.json()["resume_filename"] == "Bob_Resume.pdf"

        # =====================================================================
        # SCENARIO 6: ATS result provides score percentage without breaking formula
        # =====================================================================
        assert isinstance(resp_ats_b.json()["ats_score"], (int, float))
        assert 0 <= resp_ats_b.json()["ats_score"] <= 100
        assert "matched_skills" in resp_ats_b.json()
        assert "missing_skills" in resp_ats_b.json()

        # =====================================================================
        # SCENARIO 7: Interview history remains accessible after replacement
        # =====================================================================
        resp_history = client.get("/api/mock-interview/sessions", headers=headers_main)
        assert resp_history.status_code == 200
        history_list = resp_history.json()
        # Session A started under Resume A is still present in history
        assert any(item["session_id"] == session_a_id for item in history_list)

        # =====================================================================
        # SCENARIO 8: User isolation enforced
        # =====================================================================
        user_isolated = self._get_or_create_user(db_session, "v2_isolated@example.com", "Isolated User")
        token_isolated = create_access_token({"sub": user_isolated.email, "id": user_isolated.id})
        headers_isolated = {"Authorization": f"Bearer {token_isolated}"}

        # Cannot access User Main's resume by ID
        resp_hijack = client.get(f"/api/resume/{resume_a_id}", headers=headers_isolated)
        assert resp_hijack.status_code == 404

        # Cannot run ATS analysis with User Main's resume ID
        resp_hijack_ats = client.post("/api/ats/analyze", json={"resume_id": resume_a_id}, headers=headers_isolated)
        assert resp_hijack_ats.status_code == 404

        # Cannot start mock interview with User Main's resume ID
        resp_hijack_mock = client.post(
            "/api/mock-interview/start",
            json={"resume_id": resume_a_id, "difficulty": "Medium"},
            headers=headers_isolated
        )
        assert resp_hijack_mock.status_code == 404
