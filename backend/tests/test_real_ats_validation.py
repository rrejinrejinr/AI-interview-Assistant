import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models_db import User, ResumeRecord, JobDescription, AtsResult
from auth_utils import get_password_hash, create_access_token
from app_fastapi import app
from models.ats_score import calculate_ats_score, calculate_semantic_similarity, calculate_skill_overlap
from models.resume_parser import extract_candidate_info


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(db_session):
    email = "ats_validation_user@example.com"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=get_password_hash("TestPassword123!"),
            name="ATS Validation User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    token = create_access_token({"sub": user.email, "id": user.id})
    return {"Authorization": f"Bearer {token}"}, user


# -----------------------------------------------------------------------------
# Real-World Resume Texts
# -----------------------------------------------------------------------------

# 1. Strong Match Resume: Experienced Backend Engineer
RESUME_STRONG = """
John Doe - Senior Backend Engineer
Email: john.doe@example.com | Phone: +1 555-0199 | San Francisco, CA

Professional Summary:
Backend Engineer with 5 years of experience developing high-performance REST APIs and microservices using Python, FastAPI, and PostgreSQL. Experienced with Docker containerization, Redis caching, and CI/CD pipelines deployed to AWS cloud infrastructure.

Education:
Bachelor of Science in Computer Science, University of California, Berkeley, 2019

Technical Skills:
- Languages: Python, SQL, Bash
- Frameworks & Libraries: FastAPI, Flask, REST APIs
- Databases: PostgreSQL, Redis
- DevOps & Cloud: Docker, AWS, CI/CD, Linux, Git

Work Experience:
Senior Backend Developer at CloudScale Systems (2021 - Present)
- Architected and deployed microservices handling 15M daily requests using FastAPI and PostgreSQL.
- Implemented Redis caching layer reducing database latency by 45%.
- Containerized backend workloads using Docker and configured automated CI/CD deployment pipelines on AWS.

Key Projects:
- Distributed Task Orchestrator: Built a high-throughput job queue system using Python and Redis with comprehensive REST APIs and PostgreSQL persistence.
- Secure Auth Gateway: Designed OAuth2 authentication microservice with FastAPI and Docker.
"""

# 2. Partial Match Resume: Junior Developer transitioning
RESUME_PARTIAL = """
Alice Smith - Junior Developer
Email: alice.smith@example.com | Austin, TX

Summary:
Motivated junior software developer with foundational programming skills in Python and front-end basics. Eager to contribute to scalable web applications.

Education:
B.Tech in Information Technology, 2023

Skills:
Python, HTML, CSS, Git, SQL

Projects:
- Personal Portfolio Website: Created responsive personal website using HTML, CSS, and Git.
- Inventory Tracker: Built basic CRUD desktop tool using Python and SQLite database.
"""

# 3. Weak Match Resume: Creative Designer / Content Writer
RESUME_WEAK = """
Elena Rostova - Creative UI/UX Designer & Content Strategist
Email: elena@designstudio.org | New York, NY

Summary:
Passionate visual designer and content creator with expertise in typography, brand identity, Figma prototypes, Adobe Illustrator, and digital marketing copywriting.

Education:
Bachelor of Fine Arts in Graphic Design, Pratt Institute, 2021

Skills:
Figma, Adobe Photoshop, Adobe Illustrator, Copywriting, Typography, Content Strategy, Brand Design, Wireframing, Creative Direction

Experience:
Lead Visual Designer at Creative Agency (2021 - Present)
- Crafted marketing collateral, user personas, and branding guidelines for e-commerce clients.
- Produced high-fidelity interactive mockups in Figma and managed creative design sprints.
"""

# 4. Equivalent Skills Resume (Synonyms & Abbreviations)
RESUME_EQUIVALENT = """
Devon Miller - Platform Engineer
Email: devon.m@cloudtech.io | Seattle, WA

Summary:
Infrastructure and backend engineer with deep expertise in k8s orchestration, amazon web services, golang microservices, cicd automation, restapi integration, and postgres database scaling. Strong foundation in sklearn machine learning models and nodejs full-stack tooling.

Education:
B.S. in Computer Engineering, University of Washington, 2020

Skills:
golang, k8s, amazon web services, cicd, restapi, postgres, sklearn, nodejs, nextjs, linux, docker, git

Work Experience:
Site Reliability Engineer at Apex Systems (2020 - Present)
- Automated deployment workflows using cicd and k8s clusters on amazon web services.
- Developed backend microservices using golang and restapi endpoints backed by postgres.
- Built predictive resource scaling models using sklearn and python scripts.
"""

# 5. Repeated Keywords Resume (Keyword Stuffing with No Real Evidence)
RESUME_KEYWORD_STUFFING = """
Keyword Stuffer
Email: stuffer@spammer.net

python python python python python python python python python python
react react react react react react react react react react
sql sql sql sql sql sql sql sql sql sql sql sql sql sql
docker docker docker docker docker docker docker docker
fastapi fastapi fastapi fastapi fastapi fastapi fastapi
redis redis redis redis redis redis redis redis
"""

# -----------------------------------------------------------------------------
# Target Job Descriptions
# -----------------------------------------------------------------------------
JD_BACKEND = """
Backend Developer - Cloud Platform Team
We are seeking an experienced Backend Developer to design, build, and scale our core API services.
Requirements:
- Strong proficiency in Python, FastAPI, and building scalable REST APIs.
- Experience with relational databases, specifically PostgreSQL.
- In-depth knowledge of Redis for caching and message queuing.
- Hands-on experience with Docker containerization and AWS cloud infrastructure.
- Familiarity with CI/CD deployment pipelines, Linux, and Git version control.
"""

JD_FULLSTACK = """
Senior Full Stack Engineer
We are looking for a Full Stack Engineer to build next-generation web applications.
Required Qualifications:
- Expertise in React, TypeScript, Node.js, and modern CSS/HTML.
- Solid backend experience with PostgreSQL, Docker, and REST APIs.
- Strong understanding of state management, automated CI/CD, and Git.
"""

JD_ML_ENGINEER = """
Machine Learning Engineer
Looking for an experienced Machine Learning Engineer to deploy production AI systems.
Requirements:
- Deep expertise in Python, PyTorch, TensorFlow, and scikit-learn.
- Strong database skills in SQL and data manipulation with Pandas and NumPy.
- Solid background in deep learning, neural networks, and model evaluation.
"""

JD_EQUIVALENT_TARGET = """
Cloud Platform Engineer
Requirements:
- Production experience with Kubernetes, AWS, Go, CI/CD, REST APIs, and PostgreSQL.
- Familiarity with scikit-learn, Node.js, Next.js, and Docker containerization.
"""


# -----------------------------------------------------------------------------
# Test Suite
# -----------------------------------------------------------------------------
class TestRealDataAtsValidation:

    def _create_resume(self, db_session, user, filename, text):
        rec = ResumeRecord(
            user_id=user.id,
            filename=filename,
            extracted_text=text,
            file_hash=f"hash_{filename}_{len(text)}"
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)
        return rec

    # -------------------------------------------------------------------------
    # TEST 1: Case 1 - Strong Match Real-Data Evaluation
    # -------------------------------------------------------------------------
    def test_01_strong_match_all_modes(self):
        # Mode 1: Resume-only
        r1 = calculate_ats_score(RESUME_STRONG)
        assert 0.0 <= r1["ats_score"] <= 100.0
        assert r1["analysis_mode"] == "Resume-only analysis"
        assert "No job description was provided" in r1["scoring_note"]
        assert len(r1["matched_skills"]) >= 5
        assert len(r1["missing_skills"]) == 0
        assert any("technical skill" in s.lower() for s in r1["strengths"])

        # Mode 2: Resume + Target Role
        r2 = calculate_ats_score(RESUME_STRONG, job_title="Backend Developer")
        assert 0.0 <= r2["ats_score"] <= 100.0
        assert r2["analysis_mode"] == "Resume + Target Role"
        assert r2["ats_score"] == 70.0, f"Expected exact role-skill coverage 70.0%, got {r2['ats_score']}"
        assert r2["role_skill_coverage"] == 70.0
        assert r2["structure_score"] >= 70.0
        assert r2["benchmark_is_exact"] is True
        assert "Python" in r2["matched_skills"]
        assert "FastAPI" in r2["matched_skills"]
        assert "PostgreSQL" in r2["matched_skills"]
        assert len(r2["missing_skills"]) == 3
        assert set(r2["missing_skills"]) == {"Java", "Node.js", "Spring Boot"}

        # Mode 3: Resume + Job Description
        r3 = calculate_ats_score(RESUME_STRONG, job_description=JD_BACKEND)
        assert 0.0 <= r3["ats_score"] <= 100.0
        assert r3["analysis_mode"] == "Resume + Job Description"
        assert r3["ats_score"] >= 65.0, f"Expected strong match score >= 65, got {r3['ats_score']}"
        assert r3["skill_match_score"] >= 75.0
        assert "Docker" in r3["matched_skills"]
        assert "Redis" in r3["matched_skills"]
        assert "PostgreSQL" in r3["matched_skills"]

        # Mode 4: Resume + Target Role + Job Description
        r4 = calculate_ats_score(RESUME_STRONG, job_title="Backend Developer", job_description=JD_BACKEND)
        assert 0.0 <= r4["ats_score"] <= 100.0
        assert r4["analysis_mode"] == "Resume + Target Role + Job Description"
        assert r4["ats_score"] >= 65.0
        assert len(r4["strengths"]) >= 2
        assert any("Backend Developer" in s for s in r4["strengths"])

    # -------------------------------------------------------------------------
    # TEST 2: Case 2 - Partial Match Real-Data Evaluation
    # -------------------------------------------------------------------------
    def test_02_partial_match_evaluation(self):
        # Junior developer applying for Full Stack role requiring React, TS, Node, Postgres
        r = calculate_ats_score(RESUME_PARTIAL, job_title="Full Stack Developer", job_description=JD_FULLSTACK)
        assert 0.0 <= r["ats_score"] <= 100.0
        assert r["analysis_mode"] == "Resume + Target Role + Job Description"
        # Score must reflect partial match (clearly lower than strong match)
        assert 15.0 <= r["ats_score"] <= 55.0, f"Expected partial score 15-55, got {r['ats_score']}"
        # Missing skills must be genuinely required skills from JD/role
        assert "React" in r["missing_skills"]
        assert "TypeScript" in r["missing_skills"]
        assert "Node.js" in r["missing_skills"]
        # Matched skills should only be what the resume actually has
        assert "Python" in r["matched_skills"] or "HTML" in r["matched_skills"] or "SQL" in r["matched_skills"]
        assert "React" not in r["matched_skills"]
        assert "Docker" not in r["matched_skills"]
        # Areas to improve must explicitly call out the missing technologies
        assert any(any(m in imp for m in r["missing_skills"]) for imp in r["areas_to_improve"])

    # -------------------------------------------------------------------------
    # TEST 3: Case 3 - Weak Match Real-Data Evaluation
    # -------------------------------------------------------------------------
    def test_03_weak_match_evaluation(self):
        # Creative designer applying for Machine Learning Engineer
        r = calculate_ats_score(RESUME_WEAK, job_title="Machine Learning Engineer", job_description=JD_ML_ENGINEER)
        assert 0.0 <= r["ats_score"] <= 100.0
        assert r["ats_score"] <= 25.0, f"Expected weak match score <= 25, got {r['ats_score']}"
        # Matched skills should be essentially 0
        assert len(r["matched_skills"]) == 0
        # Missing skills must contain the core ML requirements
        assert "Python" in r["missing_skills"]
        assert "PyTorch" in r["missing_skills"]
        assert "TensorFlow" in r["missing_skills"]
        assert "scikit-learn" in r["missing_skills"]
        # Next steps must suggest adding skills relevant to the role
        assert any("skills section" in ns.lower() or "add" in ns.lower() for ns in r["recommended_next_steps"])

    # -------------------------------------------------------------------------
    # TEST 4: Case 4 - Equivalent Skills and Synonyms
    # -------------------------------------------------------------------------
    def test_04_equivalent_skills_and_synonyms(self):
        # Resume has: k8s, amazon web services, golang, cicd, restapi, postgres, sklearn, nodejs, nextjs
        # JD has: Kubernetes, AWS, Go, CI/CD, REST APIs, PostgreSQL, scikit-learn, Node.js, Next.js
        r = calculate_ats_score(RESUME_EQUIVALENT, job_title="Cloud Platform Engineer", job_description=JD_EQUIVALENT_TARGET)
        assert 0.0 <= r["ats_score"] <= 100.0
        assert r["skill_match_score"] >= 80.0, f"Expected skill match >= 80%, got {r['skill_match_score']}"
        
        # Verify canonical normalization matched the synonyms
        matched_set = set(r["matched_skills"])
        assert "Kubernetes" in matched_set, f"k8s should match Kubernetes. Matched: {matched_set}"
        assert "AWS" in matched_set, f"amazon web services should match AWS. Matched: {matched_set}"
        assert "Go" in matched_set, f"golang should match Go. Matched: {matched_set}"
        assert "CI/CD" in matched_set, f"cicd should match CI/CD. Matched: {matched_set}"
        assert "REST APIs" in matched_set, f"restapi should match REST APIs. Matched: {matched_set}"
        assert "PostgreSQL" in matched_set, f"postgres should match PostgreSQL. Matched: {matched_set}"
        assert "scikit-learn" in matched_set, f"sklearn should match scikit-learn. Matched: {matched_set}"
        assert "Node.js" in matched_set, f"nodejs should match Node.js. Matched: {matched_set}"
        assert "Next.js" in matched_set, f"nextjs should match Next.js. Matched: {matched_set}"

        # No duplicate entries in matched_skills
        assert len(r["matched_skills"]) == len(set(r["matched_skills"]))

    # -------------------------------------------------------------------------
    # TEST 5: Case 5 - Keyword Stuffing with No Relevant Evidence
    # -------------------------------------------------------------------------
    def test_05_keyword_stuffing_resilience(self):
        # Resume with repeated keywords and no project/experience sections
        r = calculate_ats_score(RESUME_KEYWORD_STUFFING, job_title="Backend Developer", job_description=JD_BACKEND)
        assert 0.0 <= r["ats_score"] <= 100.0
        # Because there are no sentences, no project evidence, and short word count,
        # semantic similarity must be significantly penalized, and improvements must warn about length/projects
        assert r["ats_score"] < 60.0, f"Expected keyword stuffing score < 60, got {r['ats_score']}"
        assert any("short" in imp.lower() or "project" in imp.lower() for imp in r["areas_to_improve"])
        # No skill should be counted more than once
        assert len(r["matched_skills"]) == len(set(r["matched_skills"]))

    # -------------------------------------------------------------------------
    # TEST 6: Error Handling for Empty or Invalid Inputs
    # -------------------------------------------------------------------------
    def test_06_empty_and_invalid_inputs(self):
        # Empty resume text
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            calculate_ats_score("")

        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            calculate_ats_score("   ")

        # Too short job description (< 5 words)
        with pytest.raises(ValueError, match="too short"):
            calculate_ats_score(RESUME_STRONG, job_description="hi there")

        with pytest.raises(ValueError, match="too short"):
            calculate_ats_score(RESUME_STRONG, job_title="Developer", job_description="Looking for developer.")

        # Whitespace-only job title with whitespace-only JD defaults cleanly to Resume-only mode
        r_blank = calculate_ats_score(RESUME_STRONG, job_title="   ", job_description="   ")
        assert r_blank["analysis_mode"] == "Resume-only analysis"

    # -------------------------------------------------------------------------
    # TEST 7: Full End-to-End FastAPI HTTP API Endpoint Verification
    # -------------------------------------------------------------------------
    def test_07_api_endpoint_real_http_request(self, test_client, auth_headers, db_session):
        headers, user = auth_headers
        resume_record = self._create_resume(db_session, user, "Real_Backend_Resume.pdf", RESUME_STRONG)

        # 1. API Call: Strong Match with JD
        payload = {
            "resume_id": resume_record.id,
            "job_title": "Backend Developer",
            "job_description": JD_BACKEND
        }
        res = test_client.post("/api/ats/analyze", json=payload, headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()

        assert "ats_result_id" in data
        assert data["resume_id"] == resume_record.id
        assert data["resume_filename"] == "Real_Backend_Resume.pdf"
        assert 0.0 <= data["ats_score"] <= 100.0
        assert data["analysis_mode"] == "Resume + Target Role + Job Description"
        assert isinstance(data["matched_skills"], list)
        assert isinstance(data["missing_skills"], list)
        assert isinstance(data["strengths"], list)
        assert isinstance(data["areas_to_improve"], list)
        assert isinstance(data["recommended_next_steps"], list)
        assert "scoring_note" in data
        assert len(data["strengths"]) > 0

        # Verify database record was persisted with correct JSON
        db_result = db_session.query(AtsResult).filter(AtsResult.id == data["ats_result_id"]).first()
        assert db_result is not None
        assert db_result.user_id == user.id
        assert db_result.ats_score == data["ats_score"]
        db_matched = json.loads(db_result.matched_skills)
        assert isinstance(db_matched, list)
        assert len(db_matched) == len(data["matched_skills"])

        # 2. API Call: Invalid input (< 5 words JD) must return 400 with clear message
        bad_payload = {
            "resume_id": resume_record.id,
            "job_description": "short"
        }
        bad_res = test_client.post("/api/ats/analyze", json=bad_payload, headers=headers)
        assert bad_res.status_code == 400
        assert "too short" in bad_res.json()["detail"].lower()

        # 3. API Call: History endpoint returns newly created ATS evaluation
        hist_res = test_client.get("/api/ats/history", headers=headers)
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert any(item["id"] == data["ats_result_id"] for item in hist_data)

    # -------------------------------------------------------------------------
    # TEST 8: Five Resumes for the Same Target Role (Weak to Strong Monotonic Gradient)
    # -------------------------------------------------------------------------
    def test_08_five_resumes_same_role_gradient(self):
        # Target Role: Backend Developer
        # Benchmark Skills: ["Python", "Java", "Node.js", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "Docker", "REST APIs", "Redis"] (10 skills)

        # 1. Weakest: Pure graphic designer (0/10 skills)
        res_weakest = "Visual Designer specializing in Figma, Adobe Illustrator, and copywriting."
        r1 = calculate_ats_score(res_weakest, job_title="Backend Developer")

        # 2. Minimal: Frontend dev with only Git/HTML/CSS (0 backend benchmark skills)
        res_minimal = "Frontend developer skilled in HTML, CSS, React, and Git."
        r2 = calculate_ats_score(res_minimal, job_title="Backend Developer")

        # 3. Partial: Junior backend dev with Python and SQL (2/10 skills = 20.0%)
        res_partial = "Junior backend programmer working with Python and SQL databases."
        r3 = calculate_ats_score(res_partial, job_title="Backend Developer")

        # 4. Strong: Senior Python backend dev with 7 skills (7/10 skills = 70.0%)
        # Skills: Python, FastAPI, SQL, PostgreSQL, Docker, Redis, REST APIs
        r4 = calculate_ats_score(RESUME_STRONG, job_title="Backend Developer")

        # 5. Strongest: Comprehensive backend engineer with all 10 benchmark skills (10/10 = 100.0%)
        res_expert = """
        Principal Backend Architect
        Expertise in Python, Java, Node.js, FastAPI, Spring Boot, SQL, PostgreSQL, Docker, REST APIs, and Redis.
        Experience architecting distributed backend services.
        """
        r5 = calculate_ats_score(res_expert, job_title="Backend Developer")

        # Confirm strictly monotonic progression
        assert r1["ats_score"] == 0.0, f"Expected 0.0, got {r1['ats_score']}"
        assert r2["ats_score"] == 0.0, f"Expected 0.0, got {r2['ats_score']}"
        assert r3["ats_score"] == 20.0, f"Expected 20.0, got {r3['ats_score']}"
        assert r4["ats_score"] == 70.0, f"Expected 70.0, got {r4['ats_score']}"
        assert r5["ats_score"] == 100.0, f"Expected 100.0, got {r5['ats_score']}"

        assert r1["ats_score"] <= r2["ats_score"] < r3["ats_score"] < r4["ats_score"] < r5["ats_score"]
        assert len(r5["missing_skills"]) == 0
        assert len(r1["missing_skills"]) == 10

    # -------------------------------------------------------------------------
    # TEST 9: Same Resume Across Multiple Different Target Roles
    # -------------------------------------------------------------------------
    def test_09_multiple_roles_same_resume(self):
        # RESUME_STRONG has Python, FastAPI, PostgreSQL, Docker, Redis, REST APIs, SQL

        # Role 1: Backend Developer -> 7/10 skills matched = 70.0%
        r_backend = calculate_ats_score(RESUME_STRONG, job_title="Backend Developer")
        assert r_backend["ats_score"] == 70.0
        assert "FastAPI" in r_backend["matched_skills"]
        assert "Java" in r_backend["missing_skills"]

        # Role 2: Frontend Developer -> 1/9 frontend benchmark skills matched (Git) = 11.1%
        r_frontend = calculate_ats_score(RESUME_STRONG, job_title="Frontend Developer")
        assert r_frontend["ats_score"] == 11.1
        assert "Git" in r_frontend["matched_skills"]
        assert "React" in r_frontend["missing_skills"]
        assert "TypeScript" in r_frontend["missing_skills"]
        assert "HTML" in r_frontend["missing_skills"]
        assert len(r_frontend["missing_skills"]) == 8

        # Role 3: Data Scientist -> 2/7 skills matched (Python, SQL) = 28.6%
        r_ds = calculate_ats_score(RESUME_STRONG, job_title="Data Scientist")
        assert r_ds["ats_score"] == 28.6
        assert "Python" in r_ds["matched_skills"]
        assert "SQL" in r_ds["matched_skills"]
        assert "Pandas" in r_ds["missing_skills"]
        assert "scikit-learn" in r_ds["missing_skills"]

        # Confirm scores change for evidence-based reasons
        assert r_backend["ats_score"] > r_ds["ats_score"] > r_frontend["ats_score"]

    # -------------------------------------------------------------------------
    # TEST 10: Unlisted Role Discloses Benchmark Limitations Honestly
    # -------------------------------------------------------------------------
    def test_10_unlisted_role_benchmark_disclosure(self):
        r_unlisted = calculate_ats_score(RESUME_STRONG, job_title="Quantum Robotics Architect")
        assert r_unlisted["benchmark_is_exact"] is False
        assert "not in our standardized role benchmark library" in r_unlisted["scoring_note"].lower()
        assert "general software engineering baseline" in r_unlisted["scoring_note"].lower()

    # -------------------------------------------------------------------------
    # TEST 11: General Resume Quality Formula Audit & User Case Study
    # -------------------------------------------------------------------------
    def test_11_general_quality_weights_and_components_transparency(self):
        # Case study from user: resume with C, Java, Python, Machine Learning, Deep Learning
        resume_user_case = """
        John Candidate
        Email: candidate@example.com | Phone: +1 555-0100 | San Francisco, CA

        Professional Summary:
        Dedicated software engineering graduate specializing in system-level programming and applied machine learning models.

        Education:
        Bachelor of Science in Computer Science, University of Technology, 2024

        Technical Skills:
        C, Java, Python, Machine Learning, Deep Learning

        Work Experience:
        Software Engineer Intern at Tech Corp (June 2023 - May 2024)
        - Developed backend microservices using Python and Java to ingest and normalize enterprise datasets.
        - Designed and trained supervised machine learning pipelines to detect abnormal network traffic patterns.
        - Partnered with senior engineers to implement automated testing suites and improve code review throughput.
        - Optimized database queries and memory allocation for low-latency operational workloads.

        Key Projects:
        - Deep Learning Image Classifier: Built and trained convolutional neural networks in Python using deep learning libraries, achieving 94% precision on multi-class image benchmarks.
        - Low-Level Systems Memory Allocator in C: Engineered custom slab allocation mechanisms and thread-safe data structures in C, reducing heap fragmentation by 35% in simulated stress environments.
        - Cross-Platform Task Scheduler in Java: Implemented concurrent worker pools and distributed task queues with Java synchronization primitives.
        - Analytical Dashboard: Generated statistical metrics and predictive visualizations using machine learning and Python.
        """

        result = calculate_ats_score(resume_user_case)

        # 1. Component score existence and transparency
        assert "structure_score" in result
        assert "skill_density_score" in result
        assert "length_score" in result
        assert "structure_weight" in result
        assert "skill_density_weight" in result
        assert "length_weight" in result

        # 2. Weights must strictly sum to 100%
        assert result["structure_weight"] == 30
        assert result["skill_density_weight"] == 30
        assert result["content_impact_weight"] == 25
        assert result["length_weight"] == 15
        assert (
            result["structure_weight"]
            + result["skill_density_weight"]
            + result["content_impact_weight"]
            + result["length_weight"]
        ) == 100

        # 3. Weighted calculation must be mathematically exact
        expected_score = round(
            (result["structure_score"] * 0.30)
            + (result["skill_density_score"] * 0.30)
            + (result["content_impact_score"] * 0.25)
            + (result["length_score"] * 0.15),
            1
        )
        assert result["ats_score"] == expected_score

        # 4. Verified skills extracted
        matched = set(result["matched_skills"])
        assert "Python" in matched
        assert "Java" in matched
        assert "C" in matched
        assert "Machine Learning" in matched
        assert "Deep Learning" in matched
        assert len(result["missing_skills"]) == 0

        # 5. Score is transparent, healthy, and not unfairly capped at 50 for a multi-section technical resume
        assert result["ats_score"] > 60.0, f"Expected calibrated ATS score > 60, got {result['ats_score']}"

        # 6. No role relevance claimed without JD or target role
        for s in result["strengths"]:
            assert "role" not in s.lower() or "target" not in s.lower()
        assert "No job description was provided" in result["scoring_note"]

    # -------------------------------------------------------------------------
    # TEST 12: Missing Sections Detection & Evidence-Based Feedback
    # -------------------------------------------------------------------------
    def test_12_missing_sections_detection(self):
        # Resume missing experience and summary
        sparse_resume = """
        Student Name
        Email: student@college.edu
        Education:
        B.Tech in Computer Engineering, 2025
        Skills:
        Python, SQL, Git
        Projects:
        Built a simple calculator in Python.
        """
        result = calculate_ats_score(sparse_resume)

        # Structure score should reflect missing experience and missing summary
        assert result["structure_score"] < 75.0
        # Areas to improve must explicitly recommend adding experience/project detail and summary
        areas = " ".join(result["areas_to_improve"]).lower()
        assert "summary" in areas or "objective" in areas

    # -------------------------------------------------------------------------
    # TEST 13: Deterministic Repeated Analysis Consistency
    # -------------------------------------------------------------------------
    def test_13_repeated_analysis_consistency(self):
        # Running calculation 3 times on the same input must yield identical results
        r1 = calculate_ats_score(RESUME_STRONG)
        r2 = calculate_ats_score(RESUME_STRONG)
        r3 = calculate_ats_score(RESUME_STRONG)

        assert r1["ats_score"] == r2["ats_score"] == r3["ats_score"]
        assert r1["structure_score"] == r2["structure_score"] == r3["structure_score"]
        assert r1["skill_density_score"] == r2["skill_density_score"] == r3["skill_density_score"]
        assert r1["matched_skills"] == r2["matched_skills"] == r3["matched_skills"]

    # -------------------------------------------------------------------------
    # TEST 14: Candidate Info Extraction With Missing Details (No Hallucinations)
    # -------------------------------------------------------------------------
    def test_14_candidate_info_extraction_missing_details(self):
        # 1. Complete details from strong resume
        info_strong = extract_candidate_info(RESUME_STRONG)
        assert info_strong["name"] == "John Doe" or "John Doe" in info_strong["name"]
        assert info_strong["email"] == "john.doe@example.com"
        assert info_strong["phone"] == "+1 555-0199"
        assert info_strong["degree"] == "Bachelor of Science in Computer Science"
        assert info_strong["college"] == "University of California, Berkeley"
        assert info_strong["graduation_year"] == "2019"
        assert "Senior Backend Engineer" in (info_strong["target_role"] or "")

        # 2. Sparse resume with missing phone, missing degree, missing college
        sparse_text = """
        Maya Lin
        Email: maya.lin@example.org
        Location: Seattle, WA

        Technical Skills:
        Python, Docker, SQL
        """
        info_sparse = extract_candidate_info(sparse_text)
        assert info_sparse["name"] == "Maya Lin"
        assert info_sparse["email"] == "maya.lin@example.org"
        assert info_sparse["location"] == "Seattle, WA"
        # Never invent missing details
        assert info_sparse["phone"] is None
        assert info_sparse["degree"] is None
        assert info_sparse["college"] is None
        assert info_sparse["graduation_year"] is None

        # 3. Empty text handling
        info_empty = extract_candidate_info("")
        assert info_empty["name"] is None
        assert info_empty["email"] is None
        assert info_empty["phone"] is None
        assert info_empty["degree"] is None
        assert info_empty["college"] is None

    # -------------------------------------------------------------------------
    # TEST 15: Two Different Users & Resumes Isolation (No Profile Substitution)
    # -------------------------------------------------------------------------
    def test_15_two_different_users_resumes_isolation(self, test_client, db_session):
        # User A setup (idempotent lookup/creation)
        user_a = db_session.query(User).filter(User.email == "user_a_isolation@test.com").first()
        if not user_a:
            user_a = User(
                email="user_a_isolation@test.com",
                password_hash=get_password_hash("Pass123!"),
                name="Alice Profile Name",
                phone="+1 111-222-3333",
                college="Stanford University",
                degree="M.S. Computer Science"
            )
            db_session.add(user_a)
            db_session.commit()
            db_session.refresh(user_a)

        # User B setup (idempotent lookup/creation)
        user_b = db_session.query(User).filter(User.email == "user_b_isolation@test.com").first()
        if not user_b:
            user_b = User(
                email="user_b_isolation@test.com",
                password_hash=get_password_hash("Pass123!"),
                name="Bob Profile Name",
                phone="+1 999-888-7777",
                college="MIT",
                degree="Ph.D. Robotics"
            )
            db_session.add(user_b)
            db_session.commit()
            db_session.refresh(user_b)

        token_a = create_access_token({"sub": user_a.email, "id": user_a.id})
        token_b = create_access_token({"sub": user_b.email, "id": user_b.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A uploads RESUME_STRONG (John Doe)
        rec_a = self._create_resume(db_session, user_a, "Resume_User_A.pdf", RESUME_STRONG)
        # User B uploads RESUME_WEAK (Elena Rostova)
        rec_b = self._create_resume(db_session, user_b, "Resume_User_B.pdf", RESUME_WEAK)

        # User A analyzes Resume A
        res_a = test_client.post("/api/ats/analyze", json={"resume_id": rec_a.id}, headers=headers_a)
        assert res_a.status_code == 200
        data_a = res_a.json()

        # User B analyzes Resume B
        res_b = test_client.post("/api/ats/analyze", json={"resume_id": rec_b.id}, headers=headers_b)
        assert res_b.status_code == 200
        data_b = res_b.json()

        # Check candidate_info in ATS responses
        cand_a = data_a.get("candidate_info", {})
        cand_b = data_b.get("candidate_info", {})

        # User A's report must show John Doe from the resume, NOT "Alice Profile Name" from User model
        assert "John Doe" in (cand_a.get("name") or "")
        assert cand_a.get("email") == "john.doe@example.com"
        assert cand_a.get("name") != user_a.name

        # User B's report must show Elena Rostova, NOT "Bob Profile Name" from User model
        assert "Elena Rostova" in (cand_b.get("name") or "")
        assert cand_b.get("email") == "elena@designstudio.org"
        assert cand_b.get("name") != user_b.name

        # Scores must be distinct and reflect actual resumes
        assert data_a["ats_score"] > data_b["ats_score"]

        # User A cannot analyze User B's resume (Strict 404 security boundary)
        forbidden_res = test_client.post("/api/ats/analyze", json={"resume_id": rec_b.id}, headers=headers_a)
        assert forbidden_res.status_code == 404

    # -------------------------------------------------------------------------
    # TEST 16: Non-Technical Buzzwords Rejection & Skill Deduplication
    # -------------------------------------------------------------------------
    def test_16_buzzwords_rejection_and_deduplication(self):
        buzzword_resume = """
        Buzzword Candidate
        Email: buzz@example.com

        Skills:
        Python, Python, Python, fast-paced, proactive team player, synergy, hard working, Docker, Docker
        """
        r = calculate_ats_score(buzzword_resume)
        matched = r["matched_skills"]

        # Only legitimate technical skills detected
        assert "Python" in matched
        assert "Docker" in matched

        # Non-technical buzzwords MUST NOT be classified as technical skills
        for word in ["synergy", "proactive", "team player", "hard working", "fast-paced", "player"]:
            assert word not in [m.lower() for m in matched]

        # Deduplication must be strictly enforced: exactly 1 entry per skill
        assert len(matched) == len(set(matched))
        assert matched.count("Python") == 1
        assert matched.count("Docker") == 1

    # -------------------------------------------------------------------------
    # TEST 17: Full API Response Contract for Frontend Score & Display
    # -------------------------------------------------------------------------
    def test_17_api_response_contract_for_frontend(self, test_client, auth_headers, db_session):
        headers, user = auth_headers
        resume_record = self._create_resume(db_session, user, "Contract_Test_Resume.pdf", RESUME_STRONG)

        res = test_client.post(
            "/api/ats/analyze",
            json={"resume_id": resume_record.id, "job_title": "Backend Developer", "job_description": JD_BACKEND},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()

        # 1. Overall score
        assert "ats_score" in data
        assert isinstance(data["ats_score"], (int, float))
        assert 0.0 <= data["ats_score"] <= 100.0

        # 2. Candidate profile dict
        assert "candidate_info" in data
        ci = data["candidate_info"]
        assert isinstance(ci, dict)
        for key in ["name", "email", "phone", "degree", "college", "graduation_year", "target_role", "location"]:
            assert key in ci

        # 3. Skills found & missing skills
        assert "matched_skills" in data
        assert isinstance(data["matched_skills"], list)
        assert "missing_skills" in data
        assert isinstance(data["missing_skills"], list)

        # 4. Minimal feedback
        assert "strengths" in data
        assert isinstance(data["strengths"], list)
        assert "areas_to_improve" in data
        assert isinstance(data["areas_to_improve"], list)

        # 5. Internal component scores preserved for audit/debugging
        assert "structure_score" in data
        assert "skill_density_score" in data
        assert "length_score" in data

    # -------------------------------------------------------------------------
    # TEST 18: Target Role & Assessment Mode Separation Regression
    # -------------------------------------------------------------------------
    def test_18_target_role_and_assessment_mode_separation_regression(self, test_client, auth_headers, db_session):
        headers, user = auth_headers

        # Resume without any role headline
        resume_no_role = """
        Jordan Lee
        Email: jordan.lee@example.com
        Location: Chicago, IL

        Summary:
        Skilled programmer with hands-on experience in cloud systems and databases.

        Education:
        B.S. in Computer Science, University of Illinois, 2022

        Skills:
        Python, PostgreSQL, Docker, Git

        Projects:
        - Data API: Built REST API in Python with PostgreSQL.
        """
        rec_no_role = self._create_resume(db_session, user, "Jordan_No_Role.pdf", resume_no_role)

        # 1. General Resume Quality mode with no target role -> target_role is None ("Not provided")
        res_general = test_client.post(
            "/api/ats/analyze",
            json={"resume_id": rec_no_role.id},
            headers=headers
        )
        assert res_general.status_code == 200
        data_general = res_general.json()

        assert data_general["assessment_mode"] == "General Resume Quality"
        assert data_general["target_role"] is None
        assert data_general["job_title"] is None
        assert data_general["candidate_info"]["target_role"] is None
        # Must NEVER be "Resume Baseline Assessment"
        assert data_general["target_role"] != "Resume Baseline Assessment"
        assert data_general["job_title"] != "Resume Baseline Assessment"

        # 2. An explicitly selected target role -> selected role is displayed
        res_explicit = test_client.post(
            "/api/ats/analyze",
            json={"resume_id": rec_no_role.id, "job_title": "Lead DevOps Architect"},
            headers=headers
        )
        assert res_explicit.status_code == 200
        data_explicit = res_explicit.json()
        assert data_explicit["target_role"] == "Lead DevOps Architect"
        assert data_explicit["job_title"] == "Lead DevOps Architect"
        assert data_explicit["assessment_mode"] == "Resume + Target Role"

        # 3. Target role extracted from resume -> displayed only when reliably identified
        rec_strong = self._create_resume(db_session, user, "John_Doe_Role.pdf", RESUME_STRONG)
        res_extracted = test_client.post(
            "/api/ats/analyze",
            json={"resume_id": rec_strong.id},
            headers=headers
        )
        assert res_extracted.status_code == 200
        data_extracted = res_extracted.json()
        # Extracted from "John Doe - Senior Backend Engineer"
        assert data_extracted["target_role"] == "Senior Backend Engineer"
        assert data_extracted["candidate_info"]["target_role"] == "Senior Backend Engineer"

        # 4. "Resume Baseline Assessment" NEVER appears as the target role in history or results
        hist_res = test_client.get("/api/ats/history", headers=headers)
        assert hist_res.status_code == 200
        for item in hist_res.json():
            assert item.get("target_role") != "Resume Baseline Assessment"
            assert item.get("target_role") != "General Resume Quality"
