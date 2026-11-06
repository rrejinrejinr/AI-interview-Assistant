import os
import sys
import io
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models_db import User, ResumeRecord, JobDescription, AtsResult
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app

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

class TestCentralizedResumeAndAtsFlow:
    """
    Verifies the 8 required end-to-end test scenarios:
    1. Upload Resume A
    2. Open Extracted Skills -> skills from Resume A appear
    3. Open ATS Analysis -> Resume A analyzed successfully
    4. Upload Resume B
    5. Open Extracted Skills -> Resume B's skills appear
    6. Open ATS Analysis -> Resume B is analyzed
    7. Refresh the browser -> Resume B remains active
    8. Log in as another user -> verify user isolation
    """

    def _create_user(self, db, email, name):
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                name=name,
                password_hash=get_password_hash("SecretPassword123!"),
                email_verified=True
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        return u

    def test_end_to_end_resume_lifecycle(self, client, db_session, monkeypatch):
        # Setup User A
        user_a = self._create_user(db_session, "resume_flow_user_a@example.com", "Alice Candidate")
        token_a = create_access_token({"sub": user_a.email, "id": user_a.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Mock extract_resume_text so we can test with dummy bytes but real extracted text
        import app_fastapi
        current_text = {"text": RESUME_A_TEXT}
        monkeypatch.setattr(app_fastapi, "extract_resume_text", lambda path: current_text["text"])
        monkeypatch.setattr(
            app_fastapi,
            "generate_initial_hr_question",
            lambda resume_text, skills, predicted_role, force_fallback=False: {
                "step_index": 0,
                "stage": "introduction",
                "speaker": "ai_interviewer",
                "question": f"Hello! Welcome to your interview for {predicted_role}.",
                "message": f"Hello! Welcome to your interview for {predicted_role}."
            }
        )

        # ---------------------------------------------------------------------
        # STEP 1: Upload Resume A
        # ---------------------------------------------------------------------
        file_a = io.BytesIO(b"%PDF-1.4 dummy pdf binary stream for Resume A")
        resp_upload_a = client.post(
            "/api/resume/upload",
            files={"resume": ("Alice_Walker_Resume.pdf", file_a, "application/pdf")},
            headers=headers_a
        )
        assert resp_upload_a.status_code == 200, f"Upload A failed: {resp_upload_a.text}"
        data_a = resp_upload_a.json()
        resume_a_id = data_a["resume_id"]
        assert resume_a_id is not None
        assert data_a["filename"] == "Alice_Walker_Resume.pdf"
        assert data_a.get("active_resume_id") == resume_a_id

        # ---------------------------------------------------------------------
        # STEP 2: Open Extracted Skills -> verify skills from Resume A appear
        # ---------------------------------------------------------------------
        # Via active endpoint:
        resp_skills_active = client.get("/api/resume/active", headers=headers_a)
        assert resp_skills_active.status_code == 200
        skills_data_a = resp_skills_active.json()
        assert skills_data_a["id"] == resume_a_id
        assert skills_data_a["filename"] == "Alice_Walker_Resume.pdf"
        assert "React" in skills_data_a["skills_list"]
        assert "TypeScript" in skills_data_a["skills_list"]
        assert "Python" not in skills_data_a["skills_list"]

        # Also verify GET /api/user/active-resume returns Resume A
        resp_active_meta = client.get("/api/user/active-resume", headers=headers_a)
        assert resp_active_meta.status_code == 200
        assert resp_active_meta.json()["active_resume_id"] == resume_a_id

        # ---------------------------------------------------------------------
        # STEP 3: Open ATS Analysis -> verify Resume A can be analyzed
        # ---------------------------------------------------------------------
        # Call ATS without explicit resume_id (uses active resume automatically)
        resp_ats_a = client.post(
            "/api/ats/analyze",
            json={"job_title": "Full Stack Engineer"},
            headers=headers_a
        )
        assert resp_ats_a.status_code == 200, f"ATS Analysis A failed: {resp_ats_a.text}"
        ats_data_a = resp_ats_a.json()
        assert ats_data_a["resume_id"] == resume_a_id
        assert ats_data_a["resume_filename"] == "Alice_Walker_Resume.pdf"
        assert ats_data_a["ats_score"] > 0
        assert "React" in ats_data_a["matched_skills"]

        # ---------------------------------------------------------------------
        # STEP 3b: Mock Interview & HR Interview -> automatically use Resume A
        # ---------------------------------------------------------------------
        # Start Mock Interview without passing resume_id
        resp_mock_a = client.post(
            "/api/mock-interview/start",
            json={"difficulty": "Medium"},
            headers=headers_a
        )
        assert resp_mock_a.status_code == 200, f"Mock Interview A failed: {resp_mock_a.text}"
        mock_data_a = resp_mock_a.json()
        assert mock_data_a["resume_id"] == resume_a_id
        assert mock_data_a["num_questions"] == 30
        assert len(mock_data_a["questions"]) == 30

        # Start AI HR Interview without passing resume_id
        resp_ai_a = client.post(
            "/api/ai-interview/start",
            json={},
            headers=headers_a
        )
        assert resp_ai_a.status_code == 200, f"HR Interview A failed: {resp_ai_a.text}"
        ai_data_a = resp_ai_a.json()
        assert ai_data_a["resume_id"] == resume_a_id
        assert ai_data_a["resume_filename"] == "Alice_Walker_Resume.pdf"
        assert ai_data_a["status"] == "in_progress"
        assert len(ai_data_a["first_message"]) > 0
        assert len(ai_data_a["conversation_transcript"]) == 1

        # ---------------------------------------------------------------------
        # STEP 4: Upload Resume B
        # ---------------------------------------------------------------------
        current_text["text"] = RESUME_B_TEXT
        file_b = io.BytesIO(b"%PDF-1.4 dummy pdf binary stream for Resume B (different hash)")
        resp_upload_b = client.post(
            "/api/resume/upload",
            files={"resume": ("Bob_Vance_Resume.pdf", file_b, "application/pdf")},
            headers=headers_a
        )
        assert resp_upload_b.status_code == 200, f"Upload B failed: {resp_upload_b.text}"
        data_b = resp_upload_b.json()
        resume_b_id = data_b["resume_id"]
        assert resume_b_id is not None
        assert resume_b_id != resume_a_id
        assert data_b["filename"] == "Bob_Vance_Resume.pdf"
        assert data_b.get("active_resume_id") == resume_b_id

        # ---------------------------------------------------------------------
        # STEP 5: Open Extracted Skills -> verify Resume B's skills appear
        # ---------------------------------------------------------------------
        resp_skills_b = client.get("/api/resume/active", headers=headers_a)
        assert resp_skills_b.status_code == 200
        skills_data_b = resp_skills_b.json()
        assert skills_data_b["id"] == resume_b_id
        assert skills_data_b["filename"] == "Bob_Vance_Resume.pdf"
        assert "Python" in skills_data_b["skills_list"]
        assert "PyTorch" in skills_data_b["skills_list"]

        # ---------------------------------------------------------------------
        # STEP 6: Open ATS Analysis -> verify Resume B is analyzed
        # ---------------------------------------------------------------------
        resp_ats_b = client.post(
            "/api/ats/analyze",
            json={"job_title": "Data Engineer"},
            headers=headers_a
        )
        assert resp_ats_b.status_code == 200
        ats_data_b = resp_ats_b.json()
        assert ats_data_b["resume_id"] == resume_b_id
        assert ats_data_b["resume_filename"] == "Bob_Vance_Resume.pdf"
        assert "Python" in ats_data_b["matched_skills"]

        # ---------------------------------------------------------------------
        # STEP 6b: Mock Interview & HR Interview -> automatically switch to Resume B
        # ---------------------------------------------------------------------
        resp_mock_b = client.post(
            "/api/mock-interview/start",
            json={"difficulty": "Hard"},
            headers=headers_a
        )
        assert resp_mock_b.status_code == 200, f"Mock Interview B failed: {resp_mock_b.text}"
        mock_data_b = resp_mock_b.json()
        assert mock_data_b["resume_id"] == resume_b_id
        assert mock_data_b["num_questions"] == 30

        resp_ai_b = client.post(
            "/api/ai-interview/start",
            json={},
            headers=headers_a
        )
        assert resp_ai_b.status_code == 200, f"HR Interview B failed: {resp_ai_b.text}"
        ai_data_b = resp_ai_b.json()
        assert ai_data_b["resume_id"] == resume_b_id
        assert ai_data_b["resume_filename"] == "Bob_Vance_Resume.pdf"
        assert ai_data_b["status"] == "in_progress"
        assert len(ai_data_b["first_message"]) > 0

        # ---------------------------------------------------------------------
        # STEP 7: Refresh the browser -> verify Resume B remains active
        # ---------------------------------------------------------------------
        # Browser refresh invokes GET /api/auth/me to restore session
        resp_me = client.get("/api/auth/me", headers=headers_a)
        assert resp_me.status_code == 200
        me_data = resp_me.json()
        assert me_data["active_resume_id"] == resume_b_id

        # Both /api/resumes and /api/user/resumes return list of resumes
        resp_list1 = client.get("/api/resumes", headers=headers_a)
        assert resp_list1.status_code == 200
        assert any(r["id"] == resume_b_id for r in resp_list1.json())

        resp_list2 = client.get("/api/user/resumes", headers=headers_a)
        assert resp_list2.status_code == 200
        assert any(r["id"] == resume_b_id for r in resp_list2.json())

        # ---------------------------------------------------------------------
        # STEP 8: Log in as another user -> verify user resume isolation
        # ---------------------------------------------------------------------
        user_b = self._create_user(db_session, "resume_flow_user_b@example.com", "Different User")
        token_b = create_access_token({"sub": user_b.email, "id": user_b.id})
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B has uploaded no resume yet -> GET /api/resume/active must return 400 with upload prompt
        resp_user_b_skills = client.get("/api/resume/active", headers=headers_b)
        assert resp_user_b_skills.status_code == 400
        assert "upload your resume" in resp_user_b_skills.json()["detail"].lower()

        # User B cannot analyze User A's resume (Strict 404 security boundary)
        resp_forbidden_ats = client.post(
            "/api/ats/analyze",
            json={"resume_id": resume_a_id},
            headers=headers_b
        )
        assert resp_forbidden_ats.status_code == 404

        # User B cannot view User A's resume details
        resp_forbidden_details = client.get(f"/api/resume/{resume_a_id}", headers=headers_b)
        assert resp_forbidden_details.status_code == 404

        # User B cannot start Mock Interview without an active resume
        resp_b_mock = client.post(
            "/api/mock-interview/start",
            json={"difficulty": "Medium"},
            headers=headers_b
        )
        assert resp_b_mock.status_code == 400
        assert "upload your resume" in resp_b_mock.json()["detail"].lower()

        # User B cannot start HR Interview without an active resume
        resp_b_hr = client.post(
            "/api/ai-interview/start",
            json={},
            headers=headers_b
        )
        assert resp_b_hr.status_code == 400
        assert "upload your resume" in resp_b_hr.json()["detail"].lower()

        # User B cannot start an interview hijacking User A's resume_id (404)
        resp_hijack_mock = client.post(
            "/api/mock-interview/start",
            json={"resume_id": resume_a_id, "difficulty": "Medium"},
            headers=headers_b
        )
        assert resp_hijack_mock.status_code == 404

        resp_hijack_hr = client.post(
            "/api/ai-interview/start",
            json={"resume_id": resume_a_id},
            headers=headers_b
        )
        assert resp_hijack_hr.status_code == 404
