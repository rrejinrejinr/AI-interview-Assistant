import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
    active_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    
    # User Profile Fields (Personal, Education, Professional, Photo)
    profile_photo = Column(Text, nullable=True)          # Base64 data URL or photo path
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    college = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    graduation_year = Column(String, nullable=True)
    cgpa = Column(String, nullable=True)
    target_role = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    resumes = relationship("ResumeRecord", back_populates="user", foreign_keys="ResumeRecord.user_id")
    job_descriptions = relationship("JobDescription", back_populates="user")
    ats_results = relationship("AtsResult", back_populates="user")
    otps = relationship("OtpRecord", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    practice_sessions = relationship("PracticeSession", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")
    built_resumes = relationship("BuiltResume", back_populates="user", cascade="all, delete-orphan")
    dsa_progress = relationship("DsaUserProgress", back_populates="user", cascade="all, delete-orphan")
    dsa_submissions = relationship("DsaSubmission", back_populates="user", cascade="all, delete-orphan")

class OtpRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="otps")

class ResumeRecord(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_reference = Column(String, nullable=True)
    file_hash = Column(String, nullable=True, index=True) # SHA-256 for duplicate detection
    extracted_text = Column(Text, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    years_of_experience = Column(String, nullable=True)
    predicted_role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="resumes", foreign_keys=[user_id])
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    ats_results = relationship("AtsResult", back_populates="resume")
    interview_sessions = relationship("InterviewSession", back_populates="resume")
    practice_sessions = relationship("PracticeSession", back_populates="resume")
    recommendations = relationship("Recommendation", back_populates="resume")

class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    category = Column(String, nullable=False)

    resume = relationship("ResumeRecord", back_populates="skills")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="job_descriptions")
    ats_results = relationship("AtsResult", back_populates="job_description")
    recommendations = relationship("Recommendation", back_populates="job_description")

class AtsResult(Base):
    __tablename__ = "ats_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    ats_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    skill_match_score = Column(Float, nullable=False)
    matched_skills = Column(Text, nullable=False)
    missing_skills = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="ats_results")
    resume = relationship("ResumeRecord", back_populates="ats_results")
    job_description = relationship("JobDescription", back_populates="ats_results")


# 
# Mock Interview Tables (Phase 6)
# 

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=True)
    interview_mode = Column(String, nullable=False, default="MOCK_INTERVIEW") # MOCK_INTERVIEW, AI_ONE_TO_ONE
    interview_type = Column(String, nullable=False)   # Technical, Behavioral, HR, Mixed
    difficulty = Column(String, nullable=False)        # Easy, Medium, Hard
    num_questions = Column(Integer, nullable=False, default=30)
    status = Column(String, nullable=False, default="pending")  # pending, verified, in_progress, completed, REJECTED_INTEGRITY_VIOLATION, cancelled
    integrity_status = Column(String, nullable=False, default="PASSED") # PASSED, WARNING, REJECTED
    rejection_reason = Column(Text, nullable=True)
    verification_completed = Column(Boolean, default=False)
    verification_timestamp = Column(DateTime, nullable=True)
    photo_verified = Column(Boolean, default=False)
    questions_completed = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)
    avg_semantic_score = Column(Float, nullable=True)
    avg_keyword_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    response_clarity_score = Column(Float, nullable=True)
    strengths = Column(Text, nullable=True)           # JSON list
    improvement_areas = Column(Text, nullable=True)   # JSON list
    conversation_transcript = Column(Text, nullable=True) # JSON dialog history for AI One-to-One
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    resume = relationship("ResumeRecord", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan",
                             order_by="InterviewQuestion.order_index")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)    # Technical, Behavioral, HR
    category = Column(String, nullable=True)           # role, skill, project, experience, education, technology
    difficulty = Column(String, nullable=False)
    ideal_answer = Column(Text, nullable=False)        # NEVER sent to frontend before submission
    keywords = Column(Text, nullable=False)            # JSON list — NEVER sent to frontend
    order_index = Column(Integer, nullable=False)

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False, unique=True)
    user_answer = Column(Text, nullable=False)
    semantic_score = Column(Float, nullable=False)
    keyword_score = Column(Float, nullable=False)
    combined_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("InterviewQuestion", back_populates="answer")


# 
# Practice Tables (Dedicated Resume-Based Practice)
# 

class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=True)
    question_source = Column(String, nullable=False, default="resume_based") # fundamental_concepts, problem_solving, resume_based
    question_count = Column(Integer, nullable=False, default=10) # 10, 20, 30
    difficulty = Column(String, nullable=False, default="Medium") # Easy, Medium, Hard
    practice_type = Column(String, nullable=False, default="Technical") # Technical, Behavioral, Role-Specific, Mixed
    status = Column(String, nullable=False, default="in_progress") # in_progress, completed, cancelled
    overall_score = Column(Float, nullable=True)
    avg_semantic_score = Column(Float, nullable=True)
    avg_keyword_score = Column(Float, nullable=True)
    total_marks = Column(Integer, nullable=True, default=0)
    earned_marks = Column(Integer, nullable=True, default=0)
    strengths = Column(Text, nullable=True) # JSON list
    improvement_areas = Column(Text, nullable=True) # JSON list
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="practice_sessions")
    resume = relationship("ResumeRecord", back_populates="practice_sessions")
    questions = relationship("PracticeQuestion", back_populates="session", cascade="all, delete-orphan",
                             order_by="PracticeQuestion.order_index")
    answers = relationship("PracticeAnswer", back_populates="session", cascade="all, delete-orphan")


class PracticeQuestion(Base):
    __tablename__ = "practice_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False, default="Technical")
    category = Column(String, nullable=True)
    difficulty = Column(String, nullable=False, default="Medium")
    order_index = Column(Integer, nullable=False)
    ideal_answer = Column(Text, nullable=False)
    keywords = Column(Text, nullable=False) # JSON list
    options = Column(Text, nullable=True) # JSON array of 4 strings for MCQs
    correct_option = Column(String, nullable=True) # "A", "B", "C", "D"
    problem_type = Column(String, nullable=True) # "coding", "debugging", "algorithm", "data_structure", "complexity"
    max_marks = Column(Integer, nullable=True, default=2)

    session = relationship("PracticeSession", back_populates="questions")
    answer = relationship("PracticeAnswer", back_populates="question", uselist=False)


class PracticeAnswer(Base):
    __tablename__ = "practice_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("practice_questions.id"), nullable=False, unique=True)
    user_answer = Column(Text, nullable=False)
    semantic_score = Column(Float, nullable=False)
    keyword_score = Column(Float, nullable=False)
    combined_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True, default=False)
    marks_awarded = Column(Integer, nullable=True, default=0)
    max_marks = Column(Integer, nullable=True, default=2)
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("PracticeSession", back_populates="answers")
    question = relationship("PracticeQuestion", back_populates="answer")


# 
# Support Tickets Table
# 

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="Open") # Open, In Progress, Resolved
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="support_tickets")


# 
# Phase 8 — Recommendations Table
# 

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    type = Column(String, nullable=False)          # skill_gap, learning, interview, resume, career
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False)       # High, Medium, Low
    source = Column(String, nullable=False)         # llm, fallback
    metadata_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
    resume = relationship("ResumeRecord", back_populates="recommendations")
    job_description = relationship("JobDescription", back_populates="recommendations")


# 
# Resume Builder — Built Resumes Table
# 

class BuiltResume(Base):
    __tablename__ = "built_resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    template_id = Column(String, nullable=False, default="Simple")
    font_family = Column(String, nullable=False, default="Helvetica")
    pdf_path = Column(String, nullable=False)
    resume_data = Column(Text, nullable=False)
    email_sent = Column(Boolean, default=False)
    email_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="built_resumes")


# 
# Topic-Based DSA Problem Solving Tables
# 

class DsaTopic(Base):
    __tablename__ = "dsa_topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    problems = relationship("DsaProblemTopic", back_populates="topic", cascade="all, delete-orphan")


class DsaProblem(Base):
    __tablename__ = "dsa_problems"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    difficulty = Column(String, nullable=False, default="Medium") # Easy, Medium, Hard
    description = Column(Text, nullable=False)
    examples_json = Column(Text, nullable=True) # JSON list of examples [{input, output, explanation}]
    constraints_json = Column(Text, nullable=True) # JSON list of constraints
    topic_tags_json = Column(Text, nullable=False) # JSON list of string tags
    external_url = Column(String, nullable=False) # Official LeetCode problem URL
    supports_execution = Column(Boolean, default=True) # True if local Judge0 execution supported
    starter_code_json = Column(Text, nullable=True) # JSON object with language templates
    test_cases_json = Column(Text, nullable=True) # JSON list of [{input, expected_output, is_sample}]
    source = Column(String, default="leetcode")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    topics = relationship("DsaProblemTopic", back_populates="problem", cascade="all, delete-orphan")
    user_progress = relationship("DsaUserProgress", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("DsaSubmission", back_populates="problem", cascade="all, delete-orphan")


class DsaProblemTopic(Base):
    __tablename__ = "dsa_problem_topics"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("dsa_topics.id", ondelete="CASCADE"), nullable=False, index=True)

    problem = relationship("DsaProblem", back_populates="topics")
    topic = relationship("DsaTopic", back_populates="problems")


class DsaUserProgress(Base):
    __tablename__ = "dsa_user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_dsa_user_problem"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="unsolved") # unsolved, attempted, solved
    solved_at = Column(DateTime, nullable=True)
    last_attempted_at = Column(DateTime, default=datetime.datetime.utcnow)
    attempts_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="dsa_progress")
    problem = relationship("DsaProblem", back_populates="user_progress")


class DsaSubmission(Base):
    __tablename__ = "dsa_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("dsa_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String, nullable=False) # python, javascript, java, cpp
    code = Column(Text, nullable=False)
    status = Column(String, nullable=False) # Accepted, Wrong Answer, Time Limit Exceeded, Compilation Error, Runtime Error, Execution Error
    test_cases_passed = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    execution_time_ms = Column(Float, nullable=True)
    memory_kb = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="dsa_submissions")
    problem = relationship("DsaProblem", back_populates="submissions")

