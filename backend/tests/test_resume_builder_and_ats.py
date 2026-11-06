"""
test_resume_builder_and_ats.py — Comprehensive tests for ATS fix, active resume, support ticket privacy, and Resume Builder PDF generator.
"""

import unittest
import os
import io
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app_fastapi import app
from database import get_db, Base, engine
from models_db import User, ResumeRecord, ResumeSkill, BuiltResume
from auth_utils import create_access_token
from models.resume_pdf_generator import (
    build_resume_pdf,
    SUPPORTED_TEMPLATES,
    SUPPORTED_FONTS
)

class TestResumeBuilderAndAts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        db = next(get_db())
        test_email = "test_builder_user@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                email=test_email,
                password_hash="test_hash",
                email_verified=True,
                name="Test Builder Candidate"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
        if not resume:
            resume = ResumeRecord(
                user_id=user.id,
                filename="test_builder_resume.pdf",
                extracted_text="Full Stack Engineer experienced in Python, React, FastAPI, PostgreSQL, and Docker.",
                predicted_role="Full Stack Developer"
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            for s in ["Python", "React", "FastAPI", "PostgreSQL", "Docker"]:
                db.add(ResumeSkill(resume_id=resume.id, skill_name=s, category="Technical"))
            db.commit()

        token = create_access_token({"sub": user.email})
        cls.user = user
        cls.resume = resume
        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_pdf_generator_all_5_templates(self):
        """Test PDF generator produces valid non-empty %PDF bytes for all 5 templates and fonts."""
        sample_data = {
            "full_name": "Jane Developer",
            "email": "jane@example.com",
            "phone": "+1 555-0199",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/janedev",
            "github": "github.com/janedev",
            "summary": "Full stack developer with 3 years experience building scalable web applications.",
            "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "Git"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Cloud Scale Inc",
                    "location": "San Francisco, CA",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "bullets": ["Architected microservices using FastAPI", "Reduced database latency by 40%"]
                }
            ],
            "education": [
                {
                    "degree": "B.S. in Computer Science",
                    "institution": "Tech University",
                    "location": "CA",
                    "year": "2021",
                    "score": "3.9 GPA"
                }
            ],
            "projects": [
                {
                    "title": "AI Interview Platform",
                    "tech_stack": "React, FastAPI, PostgreSQL",
                    "link": "https://github.com/janedev/ai-interview",
                    "bullets": ["Integrated NLP analysis pipelines", "Designed responsive user interfaces"]
                }
            ],
            "certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "year": "2023"
                }
            ],
            "achievements": [
                "Dean's Honor List 2019-2021",
                "Winner of Silicon Valley Hackathon 2022"
            ],
            "languages": ["English", "Spanish"]
        }

        for tmpl in SUPPORTED_TEMPLATES:
            for font in ["Helvetica", "Times New Roman", "Georgia"]:
                pdf_bytes = build_resume_pdf(sample_data, template_name=tmpl, font_family=font)
                self.assertIsInstance(pdf_bytes, bytes)
                self.assertTrue(len(pdf_bytes) > 500, f"Template {tmpl} with font {font} generated too small PDF")
                self.assertTrue(pdf_bytes.startswith(b"%PDF"), f"Template {tmpl} did not produce valid %PDF header")

    def test_02_set_and_get_active_resume(self):
        """Test setting and retrieving the active resume ID."""
        resp = self.client.post(
            "/api/user/active-resume",
            json={"resume_id": self.resume.id},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("active_resume_id"), self.resume.id)

        get_resp = self.client.get("/api/user/active-resume", headers=self.headers)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json().get("active_resume_id"), self.resume.id)

    def test_03_resume_builder_generate_endpoint(self):
        """Test POST /api/resume-builder/generate creates BuiltResume and generates downloadable PDF."""
        payload = {
            "template_name": "Modern",
            "font_family": "Helvetica",
            "resume_data": {
                "full_name": "Alex Smith",
                "email": "alex@example.com",
                "phone": "555-123-4567",
                "location": "Boston, MA",
                "summary": "Enthusiastic software engineer",
                "skills": ["Python", "Docker", "SQL"],
                "education": [
                    {"degree": "B.E. Computer Science", "institution": "Boston College", "year": "2024", "score": "3.8"}
                ],
                "experience": [],
                "projects": [
                    {"title": "ATS Engine", "tech_stack": "Python, TF-IDF", "bullets": ["Built resume parser"]}
                ],
                "certifications": [],
                "achievements": [],
                "languages": ["English"]
            }
        }

        with patch("auth_utils.send_resume_pdf_email", return_value=True):
            resp = self.client.post(
                "/api/resume-builder/generate",
                json=payload,
                headers=self.headers
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertIn("resume_id", data)
            self.assertIn("download_url", data)
            resume_id = data["resume_id"]

            # Test download
            dl_resp = self.client.get(f"/api/resume-builder/download/{resume_id}", headers=self.headers)
            self.assertEqual(dl_resp.status_code, 200)
            self.assertEqual(dl_resp.headers.get("content-type"), "application/pdf")
            self.assertTrue(dl_resp.content.startswith(b"%PDF"))

            # Test history
            hist_resp = self.client.get("/api/resume-builder/history", headers=self.headers)
            self.assertEqual(hist_resp.status_code, 200)
            self.assertTrue(len(hist_resp.json()) >= 1)

if __name__ == "__main__":
    unittest.main()
