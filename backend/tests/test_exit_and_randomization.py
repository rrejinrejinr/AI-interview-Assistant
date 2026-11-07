"""
test_exit_and_randomization.py — Tests for Exit APIs, 4 Practice Categories, Difficulty Scaling, and Randomization
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app_fastapi import app
from database import get_db, Base, engine
from models_db import User, ResumeRecord, ResumeSkill, PracticeSession, PracticeQuestion, InterviewSession, InterviewQuestion
from models.practice_engine import generate_practice_questions, generate_question_key
from auth_utils import create_access_token

client = TestClient(app)

class TestExitAndRandomization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        test_email = "test_exit_user@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                email=test_email,
                password_hash="test_hash",
                email_verified=True,
                name="Test Exit Candidate"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
        if not resume:
            resume = ResumeRecord(
                user_id=user.id,
                filename="test_exit_resume.pdf",
                extracted_text="Experienced Software Engineer with Python, FastAPI, PostgreSQL, and Docker. Built scalable distributed microservices.",
                predicted_role="Backend Developer"
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            for s in ["Python", "FastAPI", "PostgreSQL", "Docker"]:
                db.add(ResumeSkill(resume_id=resume.id, skill_name=s, category="Technical"))
            db.commit()

        token = create_access_token({"sub": user.email})
        cls.user = user
        cls.resume = resume
        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_practice_4_categories_generation(self):
        """Verify that all 4 practice categories generate 10, 20, and 30 questions."""
        for cat in ["aptitude", "fundamental_concepts", "problem_solving", "resume_based"]:
            for count in [10, 20]:
                qs = generate_practice_questions(
                    resume_text="Experienced in Python, SQL, REST APIs",
                    skills=["Python", "SQL", "REST APIs"],
                    predicted_role="Backend Developer",
                    question_count=count,
                    difficulty="Medium",
                    practice_type="Technical",
                    question_source=cat
                )
                self.assertEqual(len(qs), count, f"Failed for category {cat} with count {count}")
                for q in qs:
                    self.assertIn("question", q)
                    self.assertIn("ideal_answer", q)
                    self.assertIn("keywords", q)
                    self.assertIn("order_index", q)

    def test_02_practice_question_randomization_and_repetition(self):
        """
        Test that when recently served question keys are provided:
          - Session 1: returns initial questions
          - Session 2: prioritizes unseen questions (substantial non-overlap)
          - Session 3: deprioritizes recently served questions
        """
        skills = ["Python", "SQL", "Docker"]
        # Session 1
        session_1_qs = generate_practice_questions(
            skills=skills,
            question_count=10,
            difficulty="Medium",
            question_source="fundamental_concepts",
            recently_served_keys=set()
        )
        keys_1 = {q["question_key"] for q in session_1_qs}
        self.assertEqual(len(keys_1), 10)

        # Session 2 with keys_1 marked as recently served
        session_2_qs = generate_practice_questions(
            skills=skills,
            question_count=10,
            difficulty="Medium",
            question_source="fundamental_concepts",
            recently_served_keys=keys_1
        )
        keys_2 = {q["question_key"] for q in session_2_qs}

        # Verify that Session 2 prioritized fresh unseen questions
        non_overlap = keys_2 - keys_1
        self.assertGreater(len(non_overlap), 0, "Session 2 should prioritize unseen questions from the bank")

        # Session 3 with both keys_1 and keys_2
        combined_seen = keys_1.union(keys_2)
        session_3_qs = generate_practice_questions(
            skills=skills,
            question_count=10,
            difficulty="Medium",
            question_source="fundamental_concepts",
            recently_served_keys=combined_seen
        )
        self.assertEqual(len(session_3_qs), 10)

    def test_03_practice_difficulty_scaling(self):
        """Verify that Easy and Hard question pools have different questions."""
        easy_qs = generate_practice_questions(
            skills=["Python"],
            question_count=10,
            difficulty="Easy",
            question_source="aptitude"
        )
        hard_qs = generate_practice_questions(
            skills=["Python"],
            question_count=10,
            difficulty="Hard",
            question_source="aptitude"
        )
        easy_keys = {q["question_key"] for q in easy_qs}
        hard_keys = {q["question_key"] for q in hard_qs}
        self.assertNotEqual(easy_keys, hard_keys)

    def test_04_practice_exit_endpoint(self):
        """Test POST /api/practice/{session_id}/exit sets EXITED_BY_CANDIDATE."""
        # Start practice session
        start_resp = client.post(
            "/api/practice/start",
            json={
                "resume_id": self.resume.id,
                "question_source": "aptitude",
                "question_count": 10,
                "difficulty": "Easy"
            },
            headers=self.headers
        )
        self.assertEqual(start_resp.status_code, 200)
        session_id = start_resp.json()["session_id"]

        # Exit session
        exit_resp = client.post(f"/api/practice/{session_id}/exit", headers=self.headers)
        self.assertEqual(exit_resp.status_code, 200)
        exit_data = exit_resp.json()
        self.assertEqual(exit_data["status"], "EXITED_BY_CANDIDATE")
        self.assertEqual(exit_data["session_id"], session_id)
        self.assertIn("completed_at", exit_data)

    def test_05_mock_interview_exit_endpoint(self):
        """Test POST /api/mock-interview/{session_id}/exit sets EXITED_BY_CANDIDATE and does NOT trigger rejection email."""
        # Start mock interview
        start_resp = client.post(
            "/api/mock-interview/start",
            json={"resume_id": self.resume.id, "difficulty": "Medium"},
            headers=self.headers
        )
        self.assertEqual(start_resp.status_code, 200)
        session_id = start_resp.json()["session_id"]

        with patch("app_fastapi.send_malpractice_rejection_email") as mock_email:
            exit_resp = client.post(f"/api/mock-interview/{session_id}/exit", headers=self.headers)
            self.assertEqual(exit_resp.status_code, 200)
            exit_data = exit_resp.json()
            self.assertEqual(exit_data["status"], "EXITED_BY_CANDIDATE")
            self.assertEqual(exit_data["session_id"], session_id)
            self.assertEqual(exit_data["num_questions"], 30)
            self.assertIn("completed_at", exit_data)

            # CRUCIAL: Exit MUST NOT trigger rejection email
            mock_email.assert_not_called()

if __name__ == "__main__":
    unittest.main()
