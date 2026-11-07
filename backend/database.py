import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Absolute default SQLite database path in project root/backend to avoid CWD discrepancies
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Handle PostgreSQL vs SQLite connect args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def run_auto_migrations():
    """
    Safely adds missing columns to existing SQLite/Postgres tables if they were added in code.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # 1. Check interview_sessions table columns
    if "interview_sessions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("interview_sessions")]
        with engine.connect() as conn:
            if "interview_mode" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN interview_mode VARCHAR DEFAULT 'MOCK_INTERVIEW'"))
            if "integrity_status" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN integrity_status VARCHAR DEFAULT 'PASSED'"))
            if "rejection_reason" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN rejection_reason TEXT"))
            if "verification_completed" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN verification_completed BOOLEAN DEFAULT 0"))
            if "verification_timestamp" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN verification_timestamp DATETIME"))
            if "photo_verified" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN photo_verified BOOLEAN DEFAULT 0"))
            if "questions_completed" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN questions_completed INTEGER DEFAULT 0"))
            if "communication_score" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN communication_score FLOAT"))
            if "response_clarity_score" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN response_clarity_score FLOAT"))
            if "conversation_transcript" not in columns:
                conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN conversation_transcript TEXT"))
            conn.commit()

    # 2. Check practice_sessions table columns
    if "practice_sessions" in inspector.get_table_names():
        p_columns = [c["name"] for c in inspector.get_columns("practice_sessions")]
        with engine.connect() as conn:
            if "question_source" not in p_columns:
                conn.execute(text("ALTER TABLE practice_sessions ADD COLUMN question_source VARCHAR DEFAULT 'resume_based'"))
            if "total_marks" not in p_columns:
                conn.execute(text("ALTER TABLE practice_sessions ADD COLUMN total_marks INTEGER DEFAULT 0"))
            if "earned_marks" not in p_columns:
                conn.execute(text("ALTER TABLE practice_sessions ADD COLUMN earned_marks INTEGER DEFAULT 0"))
            conn.commit()

    # 3. Check practice_questions table columns
    if "practice_questions" in inspector.get_table_names():
        pq_columns = [c["name"] for c in inspector.get_columns("practice_questions")]
        with engine.connect() as conn:
            if "options" not in pq_columns:
                conn.execute(text("ALTER TABLE practice_questions ADD COLUMN options TEXT"))
            if "correct_option" not in pq_columns:
                conn.execute(text("ALTER TABLE practice_questions ADD COLUMN correct_option VARCHAR"))
            if "problem_type" not in pq_columns:
                conn.execute(text("ALTER TABLE practice_questions ADD COLUMN problem_type VARCHAR"))
            if "max_marks" not in pq_columns:
                conn.execute(text("ALTER TABLE practice_questions ADD COLUMN max_marks INTEGER DEFAULT 2"))
            conn.commit()

    # 3b. Check practice_answers table columns
    if "practice_answers" in inspector.get_table_names():
        pa_columns = [c["name"] for c in inspector.get_columns("practice_answers")]
        with engine.connect() as conn:
            if "is_correct" not in pa_columns:
                conn.execute(text("ALTER TABLE practice_answers ADD COLUMN is_correct BOOLEAN DEFAULT 0"))
            if "marks_awarded" not in pa_columns:
                conn.execute(text("ALTER TABLE practice_answers ADD COLUMN marks_awarded INTEGER DEFAULT 0"))
            if "max_marks" not in pa_columns:
                conn.execute(text("ALTER TABLE practice_answers ADD COLUMN max_marks INTEGER DEFAULT 2"))
            conn.commit()

    # 4. Check users table columns
    if "users" in inspector.get_table_names():
        u_columns = [c["name"] for c in inspector.get_columns("users")]
        with engine.connect() as conn:
            if "active_resume_id" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN active_resume_id INTEGER"))
            if "profile_photo" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_photo TEXT"))
            if "phone" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR"))
            if "location" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR"))
            if "date_of_birth" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN date_of_birth VARCHAR"))
            if "degree" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN degree VARCHAR"))
            if "college" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN college VARCHAR"))
            if "branch" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN branch VARCHAR"))
            if "graduation_year" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN graduation_year VARCHAR"))
            if "cgpa" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN cgpa VARCHAR"))
            if "target_role" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN target_role VARCHAR"))
            if "linkedin_url" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN linkedin_url VARCHAR"))
            if "github_url" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN github_url VARCHAR"))
            if "portfolio_url" not in u_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN portfolio_url VARCHAR"))
            conn.commit()

    # 5. Check resumes table columns
    if "resumes" in inspector.get_table_names():
        r_columns = [c["name"] for c in inspector.get_columns("resumes")]
        with engine.connect() as conn:
            if "file_hash" not in r_columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN file_hash VARCHAR"))
            conn.commit()

    # 6. Check built_resumes table schema (non-destructive)
if "built_resumes" in inspector.get_table_names():
    b_columns = [c["name"] for c in inspector.get_columns("built_resumes")]
    if "template_name" in b_columns or "data_json" in b_columns:
        import logging
        logging.getLogger(__name__).warning(
            "Legacy built_resumes schema detected. "
            "Skipping destructive migration to preserve existing records."
        )

    # 7. Create any newly registered tables
    Base.metadata.create_all(bind=engine)

    # 8. Seed DSA Topics and Problems catalog
    try:
        from services.dsa_catalog import seed_dsa_catalog
        db_session = SessionLocal()
        try:
            seed_dsa_catalog(db_session)
        finally:
            db_session.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to auto-seed DSA catalog: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

