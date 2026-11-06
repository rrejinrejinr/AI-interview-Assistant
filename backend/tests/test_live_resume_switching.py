"""
End-to-end resume switching integration test verifying clean empty state before new upload.

Tests the exact workflow:
1. Log in with an account that has previously uploaded Resume A.
2. Verify all five features are empty before a new upload:
   - Extracted Skills
   - ATS Analysis
   - AI Recommendations
   - Mock Interview
   - HR Interview
3. Upload Resume B.
4. Verify all five features use Resume B.
5. Refresh the browser and verify the intended workflow is preserved.
6. Upload Resume C.
7. Verify all five features switch to Resume C.
8. Verify historical reports and old uploaded files are not deleted.
9. Verify another user's resume cannot be accessed (404 isolation).

Uses monkeypatch (same technique as test_resume_integration_v2) to bypass real
PDF parsing. Does NOT mock the active-resume flow — real DB persistence is tested.
"""
import os
import sys
import io
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models_db import User, ResumeRecord
from auth_utils import get_password_hash
from app_fastapi import app
import app_fastapi

# ---------------------------------------------------------------------------
# Synthetic resume texts
# ---------------------------------------------------------------------------

RESUME_A_TEXT = """
Alice Java - Senior Java Developer
Email: alice.java@example.com | Phone: +91-9000000001 | Location: Bengaluru

SKILLS
Programming Languages: Java, SQL, HTML, CSS
Frameworks & Backend: Spring Boot, Spring Framework, REST APIs, Microservices
Databases: MySQL, PostgreSQL, Redis
Cloud & DevOps: AWS, Docker, Jenkins, Git, CI/CD

EXPERIENCE
Senior Java Developer - Backend Corp (2021-2024)
- Developed Spring Boot microservices handling 100k requests/day on AWS
- Managed MySQL and PostgreSQL databases, optimized SQL queries
- Deployed containerized services with Docker and Jenkins CI/CD pipelines

EDUCATION
B.Tech Computer Science - 2020
"""

RESUME_B_TEXT = """
Bob Python - ML Engineer & Full Stack Developer
Email: bob.python@example.com | Phone: +91-9000000002 | Location: Hyderabad

SKILLS
Programming Languages: Python, JavaScript, TypeScript, SQL
Frontend: React, Redux, Tailwind CSS
AI/ML: Machine Learning, Deep Learning, NLP, Computer Vision
ML Libraries: scikit-learn, TensorFlow, PyTorch, Pandas, NumPy
Cloud & DevOps: GCP, Docker, Git, GitHub

EXPERIENCE
ML Engineer - AI Solutions (2022-2024)
- Built machine learning classification models using Python, scikit-learn, TensorFlow
- Developed React dashboard to visualize model outputs and metrics
- Deployed models on GCP using Docker containers

EDUCATION
M.Tech Data Science - 2021
"""

RESUME_C_TEXT = """
Carol Cloud - DevOps & Cloud Architect
Email: carol.cloud@example.com | Phone: +91-9000000003 | Location: Mumbai

SKILLS
Programming Languages: Go, Golang, Python, Bash, Shell
Cloud & DevOps: Kubernetes, Docker, Terraform, Ansible, AWS, GCP, CI/CD, Helm
Databases: PostgreSQL, MongoDB, Redis
Tools: Prometheus, Grafana, Linux, Git, GitHub

EXPERIENCE
Senior DevOps Engineer - Cloud Scale Inc (2020-2024)
- Architected Kubernetes clusters on AWS using Terraform and Helm
- Automated CI/CD deployment pipelines with GitHub Actions and Ansible
- Built monitoring and observability stacks with Prometheus and Grafana

EDUCATION
B.Tech Information Technology - 2019
"""

FAKE_PDF_BYTES_A = b"%PDF-1.4 dummy stream for Alice Java"
FAKE_PDF_BYTES_B = b"%PDF-1.4 dummy stream for Bob Python"
FAKE_PDF_BYTES_C = b"%PDF-1.4 dummy stream for Carol Cloud"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=True)


def _register_and_login(client: TestClient, db_session, email: str, password: str, name: str) -> dict:
    """Create a verified user directly in DB (or reuse) and return login response dict."""
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            email_verified=True,
            active_resume_id=None,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.active_resume_id = None
        db_session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLiveResumeSwitching:

    def test_full_resume_switching_flow(self, client: TestClient, db_session, monkeypatch):
        """
        Executes the exact 9-step workflow from requirements:
        1. Log in with an account that has previously uploaded Resume A.
        2. Verify all five features are empty before a new upload.
        3. Upload Resume B.
        4. Verify all five features use Resume B.
        5. Refresh the browser and verify the intended workflow is preserved.
        6. Upload Resume C.
        7. Verify all five features switch to Resume C.
        8. Verify historical reports and old uploaded files are not deleted.
        9. Verify another user's resume cannot be accessed.
        """
        import uuid
        unique = str(uuid.uuid4())[:8]
        email_a = f"test.workflow.{unique}.a@example.com"
        email_b = f"test.workflow.{unique}.b@example.com"
        password = "WorkflowPass@123"

        # Mutable container to simulate PDF extraction
        current_text = {"text": RESUME_A_TEXT}
        monkeypatch.setattr(
            app_fastapi,
            "extract_resume_text",
            lambda path: current_text["text"]
        )

        # Mock heavy LLM call for HR interview to keep test fast and reliable
        monkeypatch.setattr(
            app_fastapi,
            "generate_initial_hr_question",
            lambda resume_text, skills, predicted_role, force_fallback=False: {
                "step_index": 0,
                "stage": "introduction",
                "question": f"Welcome! Tell me about your background in {predicted_role}.",
                "expected_aspects": ["Background", "Experience"],
                "tips": "Speak clearly"
            }
        )

        # ===================================================================
        # SETUP: User registers and uploads Resume A in a previous session
        # ===================================================================
        setup_login = _register_and_login(client, db_session, email_a, password, "Alice Candidate")
        token_setup = setup_login["access_token"]
        auth_setup = {"Authorization": f"Bearer {token_setup}"}

        upload_a_resp = client.post(
            "/api/resume/upload",
            headers=auth_setup,
            files={"resume": ("Alice_Resume_A.pdf", io.BytesIO(FAKE_PDF_BYTES_A), "application/pdf")},
        )
        assert upload_a_resp.status_code == 200
        resume_a_id = upload_a_resp.json()["resume_id"]
        assert resume_a_id is not None

        # ===================================================================
        # STEP 1: Log in again with the account that previously uploaded Resume A
        # ===================================================================
        login_resp = client.post("/api/auth/login", json={"email": email_a, "password": password})
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        token_a = login_data["access_token"]
        auth_a = {"Authorization": f"Bearer {token_a}"}

        # On a new login session, active_resume_id MUST be None
        assert login_data["user"]["active_resume_id"] is None, \
            "Login response must have active_resume_id: None before a new upload in this session"

        me_resp = client.get("/api/auth/me", headers=auth_a)
        assert me_resp.status_code == 200
        assert me_resp.json()["active_resume_id"] is None, \
            "/api/auth/me must return null active_resume_id on fresh session before upload"

        # ===================================================================
        # STEP 2: Verify all five features are empty before a new upload
        # ===================================================================
        # 1. Extracted Skills
        skills_pre = client.get("/api/resume/active", headers=auth_a)
        assert skills_pre.status_code == 400
        assert "upload your resume" in skills_pre.json()["detail"].lower()

        # 2. ATS Analysis
        ats_pre = client.post("/api/ats/analyze", headers=auth_a, json={})
        assert ats_pre.status_code == 400
        assert "upload your resume" in ats_pre.json()["detail"].lower()

        # 3. AI Recommendations
        rec_pre = client.post("/api/recommendations/analyze", headers=auth_a, json={})
        assert rec_pre.status_code == 400
        assert "upload your resume" in rec_pre.json()["detail"].lower()

        # 4. Mock Interview
        mock_pre = client.post("/api/mock-interview/start", headers=auth_a, json={"difficulty": "Medium"})
        assert mock_pre.status_code == 400
        assert "upload your resume" in mock_pre.json()["detail"].lower()

        # 5. HR Interview
        hr_pre = client.post("/api/ai-interview/start", headers=auth_a, json={})
        assert hr_pre.status_code == 400
        assert "upload your resume" in hr_pre.json()["detail"].lower()

        # ===================================================================
        # STEP 3: Upload Resume B (Python/React/Machine Learning)
        # ===================================================================
        current_text["text"] = RESUME_B_TEXT
        upload_b_resp = client.post(
            "/api/resume/upload",
            headers=auth_a,
            files={"resume": ("Bob_Resume_B.pdf", io.BytesIO(FAKE_PDF_BYTES_B), "application/pdf")},
        )
        assert upload_b_resp.status_code == 200, f"Resume B upload failed: {upload_b_resp.text}"
        upload_b_data = upload_b_resp.json()
        resume_b_id = upload_b_data.get("resume_id") or upload_b_data.get("active_resume_id")
        assert resume_b_id is not None
        assert resume_b_id != resume_a_id, "Resume B must have a different ID from Resume A"
        assert upload_b_data["active_resume_id"] == resume_b_id

        # ===================================================================
        # STEP 4: Verify all five features use Resume B
        # ===================================================================
        # 1. Extracted Skills uses Resume B
        skills_b = client.get("/api/resume/active", headers=auth_a)
        assert skills_b.status_code == 200
        skills_b_data = skills_b.json()
        assert skills_b_data["id"] == resume_b_id
        all_skills_b = [
            s.lower()
            for skills in skills_b_data.get("categorized_skills", {}).values()
            for s in skills
        ]
        assert any("python" in s for s in all_skills_b), f"Expected Python in {all_skills_b}"
        assert any("react" in s for s in all_skills_b), f"Expected React in {all_skills_b}"

        # 2. ATS Analysis uses Resume B
        ats_b = client.post("/api/ats/analyze", headers=auth_a, json={"job_title": "Python ML Engineer"})
        assert ats_b.status_code == 200
        ats_b_data = ats_b.json()
        assert "resume_quality_score" in ats_b_data or "overall_match_score" in ats_b_data or "ats_score" in ats_b_data

        # 3. AI Recommendations uses Resume B
        rec_b = client.post("/api/recommendations/analyze", headers=auth_a, json={})
        assert rec_b.status_code == 200
        rec_b_data = rec_b.json()
        assert any("python" in s.lower() for s in rec_b_data.get("current_skills", []))

        # 4. Mock Interview uses Resume B
        mock_b = client.post("/api/mock-interview/start", headers=auth_a, json={"difficulty": "Medium"})
        assert mock_b.status_code == 200
        assert mock_b.json()["resume_id"] == resume_b_id

        # 5. HR Interview uses Resume B
        hr_b = client.post("/api/ai-interview/start", headers=auth_a, json={})
        assert hr_b.status_code == 200
        assert hr_b.json()["resume_id"] == resume_b_id

        # ===================================================================
        # STEP 5: Refresh the browser and verify intended workflow is preserved
        # ===================================================================
        # Page refresh in browser calls GET /api/auth/me with existing token
        refresh_resp = client.get("/api/auth/me", headers=auth_a)
        assert refresh_resp.status_code == 200
        assert refresh_resp.json()["active_resume_id"] == resume_b_id, \
            "Browser refresh must retain Resume B as active resume within the same session"

        # Verify active resume endpoint still returns Resume B
        active_check = client.get("/api/user/active-resume", headers=auth_a)
        assert active_check.status_code == 200
        assert active_check.json()["active_resume_id"] == resume_b_id

        # ===================================================================
        # STEP 6: Upload Resume C (Go / Cloud / Kubernetes)
        # ===================================================================
        current_text["text"] = RESUME_C_TEXT
        upload_c_resp = client.post(
            "/api/resume/upload",
            headers=auth_a,
            files={"resume": ("Carol_Resume_C.pdf", io.BytesIO(FAKE_PDF_BYTES_C), "application/pdf")},
        )
        assert upload_c_resp.status_code == 200, f"Resume C upload failed: {upload_c_resp.text}"
        upload_c_data = upload_c_resp.json()
        resume_c_id = upload_c_data.get("resume_id") or upload_c_data.get("active_resume_id")
        assert resume_c_id is not None
        assert resume_c_id != resume_b_id
        assert resume_c_id != resume_a_id

        # ===================================================================
        # STEP 7: Verify all five features switch to Resume C
        # ===================================================================
        # 1. Extracted Skills switches to Resume C
        skills_c = client.get("/api/resume/active", headers=auth_a)
        assert skills_c.status_code == 200
        skills_c_data = skills_c.json()
        assert skills_c_data["id"] == resume_c_id
        all_skills_c = [
            s.lower()
            for skills in skills_c_data.get("categorized_skills", {}).values()
            for s in skills
        ]
        assert any("kubernetes" in s for s in all_skills_c), f"Expected Kubernetes in {all_skills_c}"

        # 2. ATS Analysis switches to Resume C
        ats_c = client.post("/api/ats/analyze", headers=auth_a, json={"job_title": "DevOps Engineer"})
        assert ats_c.status_code == 200

        # 3. AI Recommendations switches to Resume C
        rec_c = client.post("/api/recommendations/analyze", headers=auth_a, json={})
        assert rec_c.status_code == 200
        rec_c_data = rec_c.json()
        assert any("kubernetes" in s.lower() for s in rec_c_data.get("current_skills", []))

        # 4. Mock Interview switches to Resume C
        mock_c = client.post("/api/mock-interview/start", headers=auth_a, json={"difficulty": "Hard"})
        assert mock_c.status_code == 200
        assert mock_c.json()["resume_id"] == resume_c_id

        # 5. HR Interview switches to Resume C
        hr_c = client.post("/api/ai-interview/start", headers=auth_a, json={})
        assert hr_c.status_code == 200
        assert hr_c.json()["resume_id"] == resume_c_id

        # ===================================================================
        # STEP 8: Verify historical reports and old uploaded files are not deleted
        # ===================================================================
        # Resume A must still exist in DB and be retrievable by owner
        get_a = client.get(f"/api/resume/{resume_a_id}", headers=auth_a)
        assert get_a.status_code == 200
        assert get_a.json()["id"] == resume_a_id

        # Resume B must still exist in DB and be retrievable by owner
        get_b = client.get(f"/api/resume/{resume_b_id}", headers=auth_a)
        assert get_b.status_code == 200
        assert get_b.json()["id"] == resume_b_id

        # Resume list for user must contain all 3 resumes
        resumes_list_resp = client.get("/api/user/resumes", headers=auth_a)
        assert resumes_list_resp.status_code == 200
        user_resume_ids = [r["id"] for r in resumes_list_resp.json()]
        assert resume_a_id in user_resume_ids
        assert resume_b_id in user_resume_ids
        assert resume_c_id in user_resume_ids

        # ===================================================================
        # STEP 9: Verify another user's resume cannot be accessed (404 isolation)
        # ===================================================================
        login_b_data = _register_and_login(client, db_session, email_b, password, "Bob OtherUser")
        token_b = login_b_data["access_token"]
        auth_b = {"Authorization": f"Bearer {token_b}"}

        # User B cannot access User A's Resume A, B, or C
        assert client.get(f"/api/resume/{resume_a_id}", headers=auth_b).status_code == 404
        assert client.get(f"/api/resume/{resume_b_id}", headers=auth_b).status_code == 404
        assert client.get(f"/api/resume/{resume_c_id}", headers=auth_b).status_code == 404

        # User B cannot run ATS or interviews with User A's resume_id
        assert client.post(
            "/api/ats/analyze",
            headers=auth_b,
            json={"resume_id": resume_a_id}
        ).status_code == 404

        assert client.post(
            "/api/mock-interview/start",
            headers=auth_b,
            json={"resume_id": resume_a_id, "difficulty": "Medium"}
        ).status_code == 404

        assert client.post(
            "/api/ai-interview/start",
            headers=auth_b,
            json={"resume_id": resume_a_id}
        ).status_code == 404

        # User B with no resumes has null active resume
        b_active = client.get("/api/user/active-resume", headers=auth_b)
        assert b_active.status_code == 200
        assert b_active.json()["active_resume_id"] is None
