"""
test_role_inference.py
======================
Unit tests for the rule-based role inference engine (role_inference.py).

Covers:
  - Explicit user-selected role (highest priority)
  - Explicit role stated in resume objective / headline
  - Multi-signal inference: ML, Data Science, Backend, Frontend, Full Stack,
    DevOps, Android
  - Ambiguous / mixed signals → unclear
  - Weak / empty resume → not_found
  - Assessment-mode labels never appear as target_role
  - Re-analysis with role override
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.role_inference import infer_target_role

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def assert_role_result(result, expected_role=None, expected_source=None, unclear=None, min_confidence=None, max_confidence=None):
    assert "target_role" in result
    assert "target_role_source" in result
    assert "target_role_confidence" in result
    assert "target_role_unclear" in result
    assert 0.0 <= result["target_role_confidence"] <= 1.0, f"confidence out of range: {result['target_role_confidence']}"
    if expected_role is not None:
        assert result["target_role"] == expected_role, f"Expected role '{expected_role}', got '{result['target_role']}'"
    if expected_source is not None:
        assert result["target_role_source"] == expected_source, f"Expected source '{expected_source}', got '{result['target_role_source']}'"
    if unclear is not None:
        assert result["target_role_unclear"] == unclear, f"Expected unclear={unclear}, got {result['target_role_unclear']}"
    if min_confidence is not None:
        assert result["target_role_confidence"] >= min_confidence, f"Confidence {result['target_role_confidence']} < {min_confidence}"
    if max_confidence is not None:
        assert result["target_role_confidence"] <= max_confidence, f"Confidence {result['target_role_confidence']} > {max_confidence}"


# ---------------------------------------------------------------------------
# Resume fixtures
# ---------------------------------------------------------------------------

RESUME_ML = """
Priya Sharma
Email: priya@example.com | GitHub: github.com/priya

Summary:
Passionate about machine learning and deep learning. Looking to build intelligent systems.

Education:
B.Tech in Computer Science, IIT Bombay, 2024

Technical Skills:
Python, PyTorch, TensorFlow, scikit-learn, NumPy, Pandas, Keras

Projects:
- Image Classifier: Built a convolutional neural network using PyTorch for image classification (95% accuracy).
- Sentiment Analyser: Trained a transformer-based model to perform sentiment analysis on product reviews.
- Fraud Detection: Implemented an XGBoost classifier with hyperparameter tuning using cross-validation.
"""

RESUME_JAVA_BACKEND = """
Rohan Mehta
Email: rohan@example.com

Education:
B.E. in Information Technology, VIT Vellore, 2023

Skills:
Java, Spring Boot, REST APIs, PostgreSQL, Docker, Git, Maven

Projects:
- Library Management API: Developed a REST API using Spring Boot and PostgreSQL to manage books and members.
- Secure Auth Service: Built backend authentication microservice with JWT, Spring Boot, and Docker.
"""

RESUME_PYTHON_DATA = """
Ananya Singh
Email: ananya@example.com

Skills:
Python, SQL, Pandas, NumPy, matplotlib, seaborn, scikit-learn, Power BI

Projects:
- Customer Segmentation: Performed clustering and exploratory data analysis using K-Means.
- Sales Dashboard: Built interactive Power BI dashboard showing KPIs and monthly trends.
- Churn Prediction: Built a logistic regression model with cross-validation and hypothesis testing.
"""

RESUME_FRONTEND = """
Arjun Patel
Email: arjun@example.com

Skills:
React, JavaScript, TypeScript, HTML, CSS, Tailwind CSS, Next.js, Redux, Git

Projects:
- E-commerce UI: Built the frontend of an e-commerce app with React and Tailwind.
- Portfolio Site: Designed a responsive user interface using Next.js and TypeScript.
"""

RESUME_DEVOPS = """
Siddharth Rao
Email: sid@example.com

Skills:
Docker, Kubernetes, AWS, CI/CD, Terraform, Linux, Bash, Ansible, Git

Projects:
- Automated Deployment Pipeline: Set up a deployment pipeline using Jenkins CI/CD and Docker containers.
- Infrastructure as Code: Provisioned AWS infrastructure using Terraform and Ansible.
"""

RESUME_ANDROID = """
Kavya Nair
Email: kavya@example.com

Skills:
Kotlin, Android, Jetpack Compose, Android Studio, Room Database, Retrofit, MVVM, Git

Projects:
- Task Manager App: Built an Android app with Kotlin and Jetpack Compose with local persistence using Room.
- Weather App: Published a weather application on Play Store using Kotlin and Retrofit.
"""

RESUME_AMBIGUOUS = """
Deepak Joshi
Email: deepak@example.com

Skills:
Python, Java, JavaScript, SQL, HTML, CSS, Docker

Projects:
- CLI Tool: Built a command-line utility in Python.
- Basic Web Page: Created a simple webpage with HTML and CSS.
"""

RESUME_WEAK = """
Resume
Name: Unknown
Email: test@test.com
"""

RESUME_OBJECTIVE_EXPLICIT = """
Meera Krishnan
Email: meera@example.com

Objective: Seeking a position as Data Scientist in a research-driven organization.

Education:
M.Sc. Statistics, University of Delhi, 2024

Skills:
Python, R, SPSS, regression, clustering, hypothesis testing, matplotlib
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRoleInference:

    def test_01_user_selected_role_overrides_all(self):
        """User-selected role always wins, regardless of resume content."""
        result = infer_target_role(RESUME_ML, explicit_role="iOS Developer")
        assert_role_result(result,
            expected_role="iOS Developer",
            expected_source="user_selected",
            unclear=False,
            min_confidence=1.0
        )

    def test_02_ml_engineer_inference(self):
        """Strong ML signals → Machine Learning Engineer inferred."""
        result = infer_target_role(RESUME_ML)
        assert_role_result(result,
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )
        assert result["target_role"] in ("Machine Learning Engineer", "NLP / AI Engineer"), \
            f"Unexpected role: {result['target_role']}"

    def test_03_backend_java_inference(self):
        """Java + Spring Boot + REST API + PostgreSQL + Docker signals → Backend Developer."""
        result = infer_target_role(RESUME_JAVA_BACKEND)
        assert_role_result(result,
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )
        assert result["target_role"] in ("Backend Developer", "Software Engineer"), \
            f"Unexpected role: {result['target_role']}"

    def test_04_data_analyst_or_scientist_inference(self):
        """Python + SQL + Pandas + Power BI + clustering → Data Analyst or Data Scientist."""
        result = infer_target_role(RESUME_PYTHON_DATA)
        assert_role_result(result,
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )
        assert result["target_role"] in ("Data Analyst", "Data Scientist", "Machine Learning Engineer"), \
            f"Unexpected role: {result['target_role']}"

    def test_05_frontend_developer_inference(self):
        """React + TypeScript + Next.js + HTML/CSS/Tailwind signals → Frontend Developer."""
        result = infer_target_role(RESUME_FRONTEND)
        assert_role_result(result,
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )
        assert result["target_role"] in ("Frontend Developer", "Full Stack Developer"), \
            f"Unexpected role: {result['target_role']}"

    def test_06_devops_inference(self):
        """Docker + Kubernetes + CI/CD + Terraform → DevOps Engineer."""
        result = infer_target_role(RESUME_DEVOPS)
        assert_role_result(result,
            expected_role="DevOps Engineer",
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )

    def test_07_android_inference(self):
        """Kotlin + Jetpack Compose + Room + Android Studio → Android Developer."""
        result = infer_target_role(RESUME_ANDROID)
        assert_role_result(result,
            expected_role="Android Developer",
            expected_source="resume_inferred",
            unclear=False,
            min_confidence=0.45
        )

    def test_08_ambiguous_mixed_signals_unclear(self):
        """Python + Java + JS + Docker without dominant role → unclear or low confidence."""
        result = infer_target_role(RESUME_AMBIGUOUS)
        # Either unclear=True or low confidence (< 0.6)
        is_ambiguous = result["target_role_unclear"] or result["target_role_confidence"] < 0.60
        assert is_ambiguous, (
            f"Expected ambiguous result, got role='{result['target_role']}', "
            f"source='{result['target_role_source']}', confidence={result['target_role_confidence']}"
        )

    def test_09_weak_resume_not_found(self):
        """Very short/weak resume → not_found."""
        result = infer_target_role(RESUME_WEAK)
        assert_role_result(result,
            expected_role=None,
            expected_source="not_found",
            unclear=True,
            max_confidence=0.44
        )

    def test_10_empty_text_not_found(self):
        """Empty resume text → not_found."""
        result = infer_target_role("")
        assert_role_result(result,
            expected_role=None,
            expected_source="not_found",
            unclear=True
        )

    def test_11_explicit_objective_in_resume(self):
        """Explicitly stated 'Seeking a position as Data Scientist' → resume_explicit source."""
        result = infer_target_role(RESUME_OBJECTIVE_EXPLICIT)
        # Should be resume_explicit (from objective pattern) OR resume_inferred (from signals)
        assert result["target_role_source"] in ("resume_explicit", "resume_inferred"), \
            f"Unexpected source: {result['target_role_source']}"
        assert result["target_role"] is not None, "Expected a role to be found"
        assert result["target_role_unclear"] is False

    def test_12_assessment_labels_never_returned_as_role(self):
        """Assessment-mode labels must never be returned as target_role."""
        bad_labels = [
            "Resume Baseline Assessment",
            "General Resume Quality",
            "resume-only analysis",
            "Baseline Assessment",
            "Target Position",
        ]
        for label in bad_labels:
            result = infer_target_role(RESUME_ML, explicit_role=label)
            # explicit_role is a bad label → should be rejected → falls back to inference
            assert result["target_role"] != label, \
                f"Assessment label '{label}' leaked into target_role"
            assert result["target_role_source"] in ("resume_inferred", "not_found", "resume_explicit"), \
                f"Unexpected source for label '{label}': {result['target_role_source']}"

    def test_13_confidence_range_valid(self):
        """Confidence is always in [0, 1] range for all resumes."""
        for text in [RESUME_ML, RESUME_JAVA_BACKEND, RESUME_PYTHON_DATA,
                     RESUME_FRONTEND, RESUME_DEVOPS, RESUME_ANDROID,
                     RESUME_AMBIGUOUS, RESUME_WEAK, ""]:
            result = infer_target_role(text)
            assert 0.0 <= result["target_role_confidence"] <= 1.0, \
                f"Out-of-range confidence {result['target_role_confidence']} for text snippet"

    def test_14_user_selected_clears_unclear_flag(self):
        """When user selects a role, target_role_unclear must be False regardless of resume."""
        result = infer_target_role(RESUME_AMBIGUOUS, explicit_role="Machine Learning Engineer")
        assert_role_result(result,
            expected_role="Machine Learning Engineer",
            expected_source="user_selected",
            unclear=False,
            min_confidence=1.0
        )

    def test_15_minimum_two_signals_required(self):
        """Role inference should not trigger on a single keyword alone."""
        # Only one faint signal (just "docker" mentioned once)
        sparse_text = "I know how to use docker for containerization. I enjoy hiking."
        result = infer_target_role(sparse_text)
        # Should NOT confidently infer DevOps Engineer from a single keyword
        if result["target_role"] == "DevOps Engineer":
            assert result["target_role_unclear"] is True or result["target_role_confidence"] < 0.60, \
                "DevOps Engineer inferred from a single 'docker' mention without 2+ signals"
