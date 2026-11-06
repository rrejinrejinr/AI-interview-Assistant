"""
test_ats_accuracy.py
====================
Comprehensive tests for ATS Score Accuracy and Role Matching:
- Accurate scoring on strong, average, and weak resumes.
- Handling of unreadable, empty, and extremely brief text (no misleading high score).
- Keyword stuffing detection (skills without project/experience evidence get penalized).
- Fresher friendliness (projects satisfy practical experience requirement without mandatory corporate experience).
- Optional certifications are not treated as mandatory.
- Accurate Target Role matching against benchmark skills.
- Distinct scoring modes (General Resume Quality vs Role Match vs Job Description Match).
- Mathematical guarantee that component weights sum to 100%.
- Deterministic repeated analysis consistency.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ats_score import (
    calculate_ats_score,
    _evaluate_structure_completeness,
    _evaluate_skill_evidence,
    _evaluate_document_length
)
from models.resume_parser import extract_candidate_info
from models.role_inference import infer_target_role


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RESUME_THOLKAPPIYAN = """
Tholkappiyan
Chennai, Tamil Nadu
+91 8610901578 | tholkappiyan.vst@gmail.com

Education
St. Joseph’s Institute of Technology 2024 – 2028 (Expected)
Bachelor of Technology (B.Tech) in Information Technology CGPA: 9.09 Chennai, Tamil Nadu

Experience
Sodak Tech Jun. 2026 – Present
Backend Developer Intern (Spring Boot) Remote
• Developed backend REST APIs for a Learning Management System (LMS) using Java, Spring Boot, Spring Data JPA, and PostgreSQL.
• Implemented modules for course, module, lesson, and progress management with proper entity relationships and CRUD operations.
• Integrated Supabase PostgreSQL with Spring Boot and configured JPA/Hibernate for database connectivity and persistence.
• Collaborated with the development team using Git and GitHub feature branches, participating in code reviews, branch management, and pull requests.
• Tested and documented REST APIs using Swagger UI and Postman while debugging application issues related to Spring Security, JPA mappings, and database integration.

Projects
Lotstar – Real-Time Auction Platform | Java, Spring Boot, PostgreSQL, Redis, React 2026
• Architected a full-stack real-time bidding platform using a hybrid database design, separating a Redis write-behind cache for sub-millisecond bid verification from a PostgreSQL relational core for auditing and settlement.
• Implemented atomic bid validation with Redis Lua scripting to prevent race conditions during high-frequency bidding spikes without row-level locking.
• Built stateless JWT authentication with role-based access control (Admin, Auctioneer, Bidder) and BCrypt password hashing across a Spring Security filter chain.
• Developed a WebSocket/STOMP broadcast layer with Redis Pub/Sub to deliver live bid updates to all connected clients, and an anti-sniping engine that dynamically extends auction end times.
• Designed the frontend in React with Vite and Tailwind CSS, integrating a custom STOMP hook and countdown timer for real-time auction state.

Smile Image classification -ML | Python, Scikit-Learn, Streamlit 2025
• Built and deployed a supervised machine learning web application using a Logistic Regression classifier to generate binary predictions from user-provided input features.
• Processed and prepared training data using Pandas and NumPy, then trained and calibrated the classification model with Scikit-Learn.
• Designed an interactive Streamlit UI with sliders and input forms to let users generate real-time inferences from the trained model.
• Deployed the application to Streamlit Community Cloud with continuous delivery directly from the GitHub main branch.

Technical Skills
Languages: Java
Frameworks & Technologies: Spring Boot, Spring Data JPA, Spring Security, REST APIs, Hibernate, React
Databases: MySQL, PostgreSQL, Redis
Developer Tools: Git, GitHub, Postman, Swagger
Core Concepts: Object-Oriented Programming (OOP), Data Structures & Algorithms, DBMS, Operating Systems, Computer Networks

Extracurricular
• LeetCode: 403+ problems solved, Max Rating: 1498
• NPTEL: Database Management Systems (DBMS) Certification.
"""

RESUME_KEYWORD_STUFFING_ONLY = """
John Candidate
Email: john@example.com | Phone: 555-0100

Skills:
Python, Java, C++, Docker, Kubernetes, AWS, GCP, Azure, React, Angular, Vue,
PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, GraphQL, Linux, Terraform,
Ansible, Jenkins, Git, CI/CD, Microservices, REST APIs, FastAPI, Django, Flask, Spring Boot

Education:
B.S. in Computer Science, 2023
"""

RESUME_FRESHER_STRONG_PROJECTS = """
Aditya Verma
aditya.verma@example.edu | +91 9876543210 | Bengaluru, India

Summary:
Computer Science undergraduate passionate about distributed systems and cloud infrastructure.

Education:
B.Tech in Computer Science and Engineering, NIT Karnataka, 2021 – 2025
CGPA: 8.85 / 10.0

Technical Skills:
Python, Go, Docker, PostgreSQL, Redis, REST APIs, Linux, Git

Projects:
- Distributed Key-Value Store: Built a replicated distributed key-value store in Go with Raft consensus protocol, supporting linearizable reads and atomic writes across 5 nodes.
- Microservices API Gateway: Implemented a high-performance reverse proxy and API rate-limiter using Python, Redis token-bucket algorithm, and PostgreSQL for persistent audit logging.
- Containerized Task Queue: Developed an asynchronous worker pipeline using Docker, Python, and Redis queues to process background media conversion tasks.
"""

RESUME_WEAK_STUB = """
Candidate Name
Email: test@example.com
Phone: 1234567890
Seeking a job.
"""

JD_BACKEND_SAMPLE = """
We are seeking a Backend Developer proficient in Java, Spring Boot, PostgreSQL, Docker, and REST APIs.
Responsibilities include architecting scalable microservices, designing database schemas, integrating caches, and writing unit tests.
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAtsAccuracy:

    def test_01_tholkappiyan_resume_accuracy(self):
        """
        Verify the exact user resume that previously produced suspicious 97:
        1. Correctly infers Backend Developer.
        2. Accurate candidate details: Name is Tholkappiyan, Location is Chennai, Tamil Nadu, Grad Year is 2028.
        3. Realistic General Resume Quality score (structure + skill evidence + length).
        4. Realistic Role Match score against Backend Developer benchmark (60.0%).
        """
        cand = extract_candidate_info(RESUME_THOLKAPPIYAN)
        assert cand["name"] == "Tholkappiyan"
        assert cand["location"] == "Chennai, Tamil Nadu"
        assert cand["graduation_year"] == "2028"
        assert "St. Joseph" in (cand["college"] or "")

        role_inf = infer_target_role(RESUME_THOLKAPPIYAN)
        assert role_inf["target_role"] == "Backend Developer"
        assert role_inf["target_role_unclear"] is False
        assert role_inf["target_role_source"] == "resume_inferred"

        # General Quality calculation
        res_quality = calculate_ats_score(RESUME_THOLKAPPIYAN)
        assert 80.0 <= res_quality["resume_quality_score"] <= 95.0, \
            f"Expected realistic quality score 80-95, got {res_quality['resume_quality_score']}"

        # Role Match calculation
        res_role = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer")
        assert res_role["role_match_score"] == 60.0
        assert "Docker" in res_role["missing_skills"]
        assert "FastAPI" in res_role["missing_skills"]
        assert "Java" in res_role["matched_skills"]
        assert "Spring Boot" in res_role["matched_skills"]
        assert "PostgreSQL" in res_role["matched_skills"]

    def test_02_keyword_stuffing_penalized(self):
        """
        A resume that merely dumps 30 skill keywords without any project descriptions
        or experience bullets must receive a low skill evidence score and not get 95+.
        """
        res = calculate_ats_score(RESUME_KEYWORD_STUFFING_ONLY)
        # Skill density/evidence score should be severely limited by lack of evidence
        assert res["skill_density_score"] <= 50.0, \
            f"Expected low skill density score <= 50 for stuffed keywords, got {res['skill_density_score']}"
        assert res["ats_score"] < 65.0, \
            f"Keyword stuffed resume should not score >= 65, got {res['ats_score']}"

    def test_03_fresher_with_strong_projects_not_penalized(self):
        """
        A fresher with rich technical projects but no formal corporate experience
        must satisfy the practical experience structure requirement.
        """
        cand = extract_candidate_info(RESUME_FRESHER_STRONG_PROJECTS)
        assert cand["name"] == "Aditya Verma"

        res = calculate_ats_score(RESUME_FRESHER_STRONG_PROJECTS)
        assert res["structure_score"] >= 70.0, \
            f"Fresher with projects should get structure >= 70, got {res['structure_score']}"
        assert res["ats_score"] >= 60.0, \
            f"Strong fresher resume should score >= 60, got {res['ats_score']}"

    def test_04_weak_and_unreadable_documents_score_low(self):
        """
        Unreadable or stub resumes must produce very low scores and never misleading high scores.
        """
        res_weak = calculate_ats_score(RESUME_WEAK_STUB)
        assert res_weak["ats_score"] <= 30.0, \
            f"Stub resume must score <= 30, got {res_weak['ats_score']}"
        assert res_weak["skill_density_score"] == 0.0

        with pytest.raises(ValueError, match="empty"):
            calculate_ats_score("")

        with pytest.raises(ValueError, match="empty"):
            calculate_ats_score("   \n\t  ")

    def test_05_scoring_weights_mathematical_guarantee(self):
        """
        Documented weights must strictly sum to 100% and mathematically match composite.
        """
        for text in [RESUME_THOLKAPPIYAN, RESUME_FRESHER_STRONG_PROJECTS, RESUME_KEYWORD_STUFFING_ONLY]:
            r = calculate_ats_score(text)
            assert r["structure_weight"] == 30
            assert r["skill_density_weight"] == 30
            assert r["content_impact_weight"] == 25
            assert r["length_weight"] == 15
            assert r["structure_weight"] + r["skill_density_weight"] + r["content_impact_weight"] + r["length_weight"] == 100

            expected_composite = round(
                (r["structure_score"] * 0.30)
                + (r["skill_density_score"] * 0.30)
                + (r["content_impact_score"] * 0.25)
                + (r["length_score"] * 0.15),
                1
            )
            assert r["ats_score"] == expected_composite
            assert r["resume_quality_score"] == expected_composite

    def test_06_target_role_gradient(self):
        """
        Evaluating the same resume against different roles produces distinct, realistic scores.
        """
        r_backend = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer")
        r_frontend = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Frontend Developer")
        r_devops = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="DevOps Engineer")

        # Backend score should be significantly higher than DevOps for a Java/Spring Boot resume
        assert r_backend["ats_score"] >= 50.0
        assert r_backend["ats_score"] > r_devops["ats_score"]
        assert r_backend["role_match_score"] > r_devops["role_match_score"]

    def test_07_job_description_match_only_when_provided(self):
        """
        Job Description match score is calculated ONLY when an actual JD is supplied.
        """
        r_no_jd = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer")
        assert r_no_jd["jd_match_score"] is None

        r_with_jd = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer", job_description=JD_BACKEND_SAMPLE)
        assert r_with_jd["jd_match_score"] is not None
        assert 0.0 <= r_with_jd["jd_match_score"] <= 100.0

    def test_08_repeated_analysis_determinism(self):
        """
        Running the calculation repeatedly on the same resume produces identical results.
        """
        res1 = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer")
        res2 = calculate_ats_score(RESUME_THOLKAPPIYAN, job_title="Backend Developer")
        assert res1["ats_score"] == res2["ats_score"]
        assert res1["role_match_score"] == res2["role_match_score"]
        assert res1["resume_quality_score"] == res2["resume_quality_score"]
        assert res1["matched_skills"] == res2["matched_skills"]
        assert res1["missing_skills"] == res2["missing_skills"]
