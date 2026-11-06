import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend .env is loaded when uvicorn or python starts app_fastapi
_backend_dir = Path(__file__).resolve().parent
_backend_env = _backend_dir / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
load_dotenv()

import json
import shutil
import tempfile
import datetime
import hashlib
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

import uuid
from database import engine, Base, get_db, run_auto_migrations
from models_db import (
    User, OtpRecord, ResumeRecord, ResumeSkill,
    JobDescription, AtsResult,
    InterviewSession, InterviewQuestion, InterviewAnswer,
    PracticeSession, PracticeQuestion, PracticeAnswer,
    SupportTicket, Recommendation, BuiltResume,
    DsaTopic, DsaProblem, DsaProblemTopic, DsaUserProgress, DsaSubmission
)
from services.judge0_service import (
    submit_code_judge0,
    evaluate_problem_submission,
    check_judge0_health,
    JUDGE0_URL
)
from models.resume_parser import extract_resume_text, extract_candidate_info
from models.skill_extractor import extract_skills
from models.ats_score import calculate_ats_score
from models.role_predictor import predict_role
from models.role_inference import infer_target_role
from models.resume_pdf_generator import (
    generate_resume_pdf_bytes,
    SUPPORTED_TEMPLATES,
    SUPPORTED_FONTS
)
from models.interview_engine import (
    generate_interview_questions,
    evaluate_answer,
    generate_final_report,
    get_model_status,
)
from models.practice_engine import (
    generate_practice_questions,
    calculate_practice_report,
    generate_question_key,
)
from services.practice_evaluator import (
    evaluate_practice_answer,
    PracticeEvaluationUnavailableError
)
from models.mock_interview_engine import (
    generate_mock_interview_30_questions,
    calculate_mock_interview_report,
    evaluate_mock_question,
)
from models.ai_one_to_one_engine import (
    generate_initial_hr_question,
    generate_next_hr_response,
    evaluate_one_to_one_interview,
    HrInterviewUnavailableError,
)
from services.llm_service import (
    get_llm_config,
    generate_dynamic_question,
    generate_followup_question,
    generate_answer_feedback,
    generate_resume_improvements,
    generate_skill_gap_explanation,
    generate_learning_roadmap,
)
from rag.rag_service import answer_with_rag
from services.llm_provider import get_llm_provider
from auth_utils import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, generate_otp, send_otp_email, send_support_ticket_email,
    send_malpractice_rejection_email, send_resume_pdf_email,
    get_smtp_status, ACCESS_TOKEN_EXPIRE_MINUTES, OTP_EXPIRE_MINUTES,
    MAX_OTP_ATTEMPTS, OTP_COOLDOWN_SECONDS
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_interview_assistant")

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
run_auto_migrations()

app = FastAPI(
    title="AI Interview Assistant API",
    description="Production-grade AI-assisted resume screening, ATS optimization, mock interviews, and career recommendations.",
    version="1.0.0"
)

@app.on_event("startup")
def log_startup_configuration():
    smtp_info = get_smtp_status()
    logger.info(
        f"FastAPI Startup - SMTP Configured: {smtp_info['smtp_configured']} "
        f"(Server: {smtp_info['smtp_server']}:{smtp_info['smtp_port']}, "
        f"Username Configured: {smtp_info['smtp_username_configured']}, "
        f"Password Configured: {smtp_info['smtp_password_configured']})"
    )

# 
# CORS Configuration
# 
cors_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000,http://localhost:8001,http://127.0.0.1:8000,http://127.0.0.1:8001"
)
allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 
# Global Exception Handler (Production Safe)
# 
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
    logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise exc
    email: str = payload.get("sub")
    if not email:
        raise exc
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise exc
    return user

optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_optional_current_user(token: Optional[str] = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if not payload:
            return None
        email: str = payload.get("sub")
        if not email:
            return None
        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None


# 
# Auth Schemas & Endpoints
# 

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if user and user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already registered and verified.")

    if not user:
        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            password_hash=get_password_hash(req.password),
            email_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update name/password if re-registering unverified account
        user.name = req.name.strip()
        user.password_hash = get_password_hash(req.password)
        db.commit()

    # Rate limiting: Check for OTP resend cooldown (60s)
    last_otp = db.query(OtpRecord).filter(
        OtpRecord.user_id == user.id
    ).order_by(OtpRecord.created_at.desc()).first()

    if last_otp and (datetime.datetime.utcnow() - last_otp.created_at).total_seconds() < OTP_COOLDOWN_SECONDS:
        raise HTTPException(
            status_code=429,
            detail="Please wait 60 seconds before requesting a new verification code."
        )

    otp_code = generate_otp()
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRE_MINUTES)
    db.add(OtpRecord(user_id=user.id, otp=otp_code, expires_at=expiry, is_used=False, attempts=0))
    db.commit()

    sent, send_msg = send_otp_email(user.email, otp_code)
    if not sent:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to deliver verification OTP email: {send_msg}"
        )
    return {"message": f"Verification code sent to your email. Valid for {OTP_EXPIRE_MINUTES} minutes."}

@app.post("/api/auth/verify-otp")
def verify_otp(req: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    if user.email_verified:
        return {"message": "Email is already verified. You can log in."}

    otp_record = db.query(OtpRecord).filter(
        OtpRecord.user_id == user.id,
        OtpRecord.is_used == False
    ).order_by(OtpRecord.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="No active verification code found. Please request a new code.")

    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Maximum verification attempts exceeded. Please register/request a new code.")

    if otp_record.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new code.")

    if otp_record.otp != req.otp.strip():
        otp_record.attempts += 1
        db.commit()
        remaining = MAX_OTP_ATTEMPTS - otp_record.attempts
        raise HTTPException(status_code=400, detail=f"Invalid code. {remaining} attempt(s) remaining.")

    otp_record.is_used = True
    user.email_verified = True
    db.commit()
    return {"message": "Email verified successfully. You may now log in."}

def sync_user_active_resume(db: Session, user: User) -> Optional[int]:
    """
    Validate that user.active_resume_id points to an existing ResumeRecord belonging to this user.

    - If active_resume_id is set AND the resume exists: return it.
    - If active_resume_id is set but the resume no longer exists (deleted): clear it, return None.
    - If active_resume_id is None: return None.

    IMPORTANT: This function does NOT auto-fallback to the user's latest uploaded resume.
    The active resume is ONLY set by an explicit upload or POST /api/user/active-resume.
    Historical resumes must not be automatically activated on login or page refresh.
    """
    if user.active_resume_id:
        exists = db.query(ResumeRecord.id).filter(
            ResumeRecord.id == user.active_resume_id,
            ResumeRecord.user_id == user.id
        ).first()
        if exists:
            return user.active_resume_id
        # Stale pointer — the referenced resume was deleted; clear it
        user.active_resume_id = None
        db.commit()
        db.refresh(user)
    return None

@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email is not verified. Please complete OTP verification.")

    # Clear active_resume_id on each new login.
    # Historical resumes remain in the DB for record-keeping but must NOT be auto-activated.
    # The user must explicitly upload (or re-select) a resume in the new session.
    if user.active_resume_id is not None:
        user.active_resume_id = None
        db.commit()
        db.refresh(user)

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"name": user.name, "email": user.email, "active_resume_id": None}
    }

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active_id = sync_user_active_resume(db, current_user)
    return {
        "name": current_user.name,
        "email": current_user.email,
        "active_resume_id": active_id
    }

class SetActiveResumeRequest(BaseModel):
    resume_id: int

@app.post("/api/user/active-resume")
def set_active_resume(
    req: SetActiveResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == req.resume_id,
        ResumeRecord.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found or does not belong to your account.")

    current_user.active_resume_id = resume.id
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Active resume updated successfully.",
        "active_resume_id": resume.id,
        "filename": resume.filename
    }

@app.get("/api/user/active-resume")
def get_active_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    active_id = sync_user_active_resume(db, current_user)
    if not active_id:
        return {"active_resume_id": None, "filename": None}

    resume = db.query(ResumeRecord).filter(ResumeRecord.id == active_id).first()
    return {
        "active_resume_id": resume.id,
        "filename": resume.filename,
        "predicted_role": resume.predicted_role,
        "created_at": resume.created_at.isoformat() if resume.created_at else None
    }

def get_user_active_resume(
    db: Session,
    current_user: User,
    requested_resume_id: Optional[int] = None
) -> ResumeRecord:
    """
    Retrieve the authenticated user's active resume.
    1. If an explicit requested_resume_id is provided, verify it belongs to current_user.
       If it does not belong to current_user, raise 404 (prevents cross-user access).
    2. Otherwise, look up current_user.active_resume_id via sync_user_active_resume.
    3. If the user has no resumes at all, raise 400: 'No resume uploaded yet. Please upload your resume to get started.'
    """
    if requested_resume_id is not None:
        resume = db.query(ResumeRecord).filter(
            ResumeRecord.id == requested_resume_id,
            ResumeRecord.user_id == current_user.id
        ).first()
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found or does not belong to your account."
            )
        return resume

    active_id = sync_user_active_resume(db, current_user)
    if not active_id:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded yet. Please upload your resume to get started."
        )

    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == active_id,
        ResumeRecord.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded yet. Please upload your resume to get started."
        )

    return resume



# 
# User Profile Endpoints
# 

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[str] = None
    degree: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[str] = None
    cgpa: Optional[str] = None
    target_role: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class UpdateProfilePhotoRequest(BaseModel):
    photo: Optional[str] = None
    profile_photo: Optional[str] = None

@app.get("/api/user/profile")
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    active_id = sync_user_active_resume(db, current_user)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "profile_photo": current_user.profile_photo,
        "phone": current_user.phone,
        "location": current_user.location,
        "date_of_birth": current_user.date_of_birth,
        "degree": current_user.degree,
        "college": current_user.college,
        "branch": current_user.branch,
        "graduation_year": current_user.graduation_year,
        "cgpa": current_user.cgpa,
        "target_role": current_user.target_role,
        "linkedin_url": current_user.linkedin_url,
        "github_url": current_user.github_url,
        "portfolio_url": current_user.portfolio_url,
        "active_resume_id": active_id
    }

@app.put("/api/user/profile")
def update_user_profile(
    req: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if req.name is not None:
        current_user.name = req.name.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip()
    if req.location is not None:
        current_user.location = req.location.strip()
    if req.date_of_birth is not None:
        current_user.date_of_birth = req.date_of_birth.strip()
    if req.degree is not None:
        current_user.degree = req.degree.strip()
    if req.college is not None:
        current_user.college = req.college.strip()
    if req.branch is not None:
        current_user.branch = req.branch.strip()
    if req.graduation_year is not None:
        current_user.graduation_year = req.graduation_year.strip()
    if req.cgpa is not None:
        current_user.cgpa = req.cgpa.strip()
    if req.target_role is not None:
        current_user.target_role = req.target_role.strip()
    if req.linkedin_url is not None:
        current_user.linkedin_url = req.linkedin_url.strip()
    if req.github_url is not None:
        current_user.github_url = req.github_url.strip()
    if req.portfolio_url is not None:
        current_user.portfolio_url = req.portfolio_url.strip()

    db.commit()
    db.refresh(current_user)
    return {
        "message": "Profile updated successfully.",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "profile_photo": current_user.profile_photo,
            "phone": current_user.phone,
            "location": current_user.location,
            "date_of_birth": current_user.date_of_birth,
            "degree": current_user.degree,
            "college": current_user.college,
            "branch": current_user.branch,
            "graduation_year": current_user.graduation_year,
            "cgpa": current_user.cgpa,
            "target_role": current_user.target_role,
            "linkedin_url": current_user.linkedin_url,
            "github_url": current_user.github_url,
            "portfolio_url": current_user.portfolio_url,
            "active_resume_id": current_user.active_resume_id
        }
    }

@app.post("/api/user/profile/photo")
def update_profile_photo(
    req: UpdateProfilePhotoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.profile_photo = req.photo or req.profile_photo
    db.commit()
    return {"message": "Profile photo updated successfully.", "profile_photo": current_user.profile_photo}

@app.delete("/api/user/profile/photo")
def delete_profile_photo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.profile_photo = None
    db.commit()
    return {"message": "Profile photo removed successfully."}


# 
# Health & Status
# 

@app.get("/api/health")
def health_check():
    model_info = get_model_status()
    llm_info = get_llm_config()
    smtp_info = get_smtp_status()
    return {
        "status": "ok",
        "service": "AI Interview Assistant API",
        "port": int(os.getenv("APP_PORT", "8000")),
        "database": "connected",
        "sentence_transformer": model_info,
        "llm": llm_info,
        "smtp": smtp_info,
    }

@app.get("/api/auth/smtp-status")
def get_smtp_diagnostic():
    """Safe diagnostic endpoint reporting SMTP configuration state without exposing secrets."""
    return get_smtp_status()

@app.get("/api/llm/status")
def llm_status():
    return get_llm_config()


# 
# Resume & ATS Endpoints
# 

MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5")) * 1024 * 1024

class AtsRequest(BaseModel):
    resume_id: Optional[int] = None
    job_title: Optional[str] = Field(None, max_length=150)
    job_description: Optional[str] = Field(None, max_length=15000)

@app.get("/api/resumes")
@app.get("/api/user/resumes")
def get_user_resumes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resumes = db.query(ResumeRecord).filter(
        ResumeRecord.user_id == current_user.id
    ).order_by(ResumeRecord.created_at.desc()).all()
    
    # Deduplicate logical resumes by file_hash if present
    seen_hashes = set()
    unique_resumes = []
    for r in resumes:
        h = r.file_hash or f"id_{r.id}"
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_resumes.append(r)

    return [
        {
            "id": r.id,
            "filename": r.filename,
            "email": r.email,
            "phone": r.phone,
            "years_of_experience": r.years_of_experience,
            "predicted_role": r.predicted_role,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in unique_resumes
    ]

@app.post("/api/resume/upload")
async def upload_resume(
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_ext = os.path.splitext(resume.filename)[1].lower()
    if file_ext not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or DOCX file.")

    # Read content with size constraint
    content = await resume.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. SHA-256 Hash Deduplication Check per Authenticated User
    content_hash = hashlib.sha256(content).hexdigest()
    existing_record = db.query(ResumeRecord).filter(
        ResumeRecord.user_id == current_user.id,
        ResumeRecord.file_hash == content_hash
    ).first()

    if existing_record:
        # Match existing logical resume for this user
        candidate_info = extract_candidate_info(existing_record.extracted_text)
        if not candidate_info.get("name") or candidate_info["name"] == "Candidate":
            candidate_info["name"] = current_user.name
        if not candidate_info.get("email"):
            candidate_info["email"] = existing_record.email or current_user.email

        categorized_skills = {}
        if existing_record.skills:
            for s in existing_record.skills:
                categorized_skills.setdefault(s.category, []).append(s.skill_name)
        else:
            categorized_skills = extract_skills(existing_record.extracted_text, exclude_projects=False)
            for cat, skl_list in categorized_skills.items():
                for skill in skl_list:
                    db.add(ResumeSkill(resume_id=existing_record.id, skill_name=skill, category=cat))
            db.commit()

        all_skills = [s for skills in categorized_skills.values() for s in skills]

        # Always update active resume to this (re-uploaded) resume
        current_user.active_resume_id = existing_record.id
        db.commit()
        db.refresh(current_user)

        return {
            "message": "Resume already uploaded (identical content detected). Using existing record.",
            "resume_id": existing_record.id,
            "active_resume_id": existing_record.id,
            "filename": existing_record.filename,
            "candidate_info": candidate_info,
            "predicted_role": existing_record.predicted_role or "Software Engineer",
            "confidence_level": "High",
            "top_predictions": [{"role": existing_record.predicted_role or "Software Engineer", "confidence": 0.95}],
            "categorized_skills": categorized_skills,
            "skills_list": all_skills,
            "extracted_text_preview": existing_record.extracted_text[:300] + "..." if len(existing_record.extracted_text) > 300 else existing_record.extracted_text
        }

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp_path = tmp.name
        tmp.write(content)

    try:
        extracted_text = extract_resume_text(tmp_path)
        words = extracted_text.strip().split() if extracted_text else []
        if not extracted_text or len(extracted_text.strip()) < 30 or len(words) < 10:
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from document. Ensure it contains text and is not an empty file or scanned image."
            )

        candidate_info = extract_candidate_info(extracted_text)
        categorized_skills = extract_skills(extracted_text, exclude_projects=False)
        all_skills = [s for skills in categorized_skills.values() for s in skills]

        role_data = predict_role(extracted_text)
        predicted_role = role_data.get("predicted_role", "Software Engineer")
        confidence_level = role_data.get("confidence_level", "None")
        top_predictions = role_data.get("top_predictions", [])

        # Sanitize filename
        safe_filename = os.path.basename(resume.filename).replace("\\", "_").replace("/", "_")

        resume_record = ResumeRecord(
            user_id=current_user.id,
            filename=safe_filename,
            file_hash=content_hash,
            extracted_text=extracted_text,
            email=candidate_info["email"],
            phone=candidate_info["phone"],
            years_of_experience=candidate_info["years_of_experience"],
            predicted_role=predicted_role
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        for cat, skills in categorized_skills.items():
            for skill in skills:
                db.add(ResumeSkill(resume_id=resume_record.id, skill_name=skill, category=cat))
        
        # Always update active resume to the latest newly uploaded resume
        current_user.active_resume_id = resume_record.id

        db.commit()
        db.refresh(current_user)

        return {
            "message": "Resume analyzed and indexed successfully.",
            "resume_id": resume_record.id,
            "active_resume_id": resume_record.id,
            "filename": resume_record.filename,
            "candidate_info": candidate_info,
            "predicted_role": predicted_role,
            "confidence_level": confidence_level,
            "top_predictions": top_predictions,
            "categorized_skills": categorized_skills,
            "skills_list": all_skills,
            "extracted_text_preview": extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
        }
    finally:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass

@app.get("/api/resume/active")
def get_active_resume_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user)
    candidate_info = extract_candidate_info(resume.extracted_text)
    categorized_skills = extract_skills(resume.extracted_text, exclude_projects=False)
    all_skills = [s for skills in categorized_skills.values() for s in skills]
    role_data = predict_role(resume.extracted_text)

    return {
        "id": resume.id,
        "filename": resume.filename,
        "candidate_info": candidate_info,
        "predicted_role": resume.predicted_role or role_data.get("predicted_role", "Software Engineer"),
        "confidence_level": role_data.get("confidence_level", "None"),
        "top_predictions": role_data.get("top_predictions", []),
        "categorized_skills": categorized_skills,
        "skills_list": all_skills,
        "created_at": resume.created_at.isoformat() if resume.created_at else None
    }

@app.get("/api/resume/{resume_id}")
def get_resume_details(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == resume_id,
        ResumeRecord.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    candidate_info = extract_candidate_info(resume.extracted_text)
    categorized_skills = extract_skills(resume.extracted_text, exclude_projects=False)
    all_skills = [s for skills in categorized_skills.values() for s in skills]
    role_data = predict_role(resume.extracted_text)

    return {
        "id": resume.id,
        "filename": resume.filename,
        "candidate_info": candidate_info,
        "predicted_role": resume.predicted_role or role_data.get("predicted_role", "Software Engineer"),
        "confidence_level": role_data.get("confidence_level", "None"),
        "top_predictions": role_data.get("top_predictions", []),
        "categorized_skills": categorized_skills,
        "skills_list": all_skills,
        "created_at": resume.created_at.isoformat() if resume.created_at else None
    }

ATS_ASSESSMENT_MODE_LABELS = {
    "resume baseline assessment",
    "general resume quality",
    "resume-only analysis",
    "baseline assessment",
    "target position",
    "ats evaluation",
    "resume quality assessment"
}

@app.get("/api/ats/history")
def get_ats_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = db.query(AtsResult).filter(
        AtsResult.user_id == current_user.id
    ).order_by(AtsResult.created_at.desc()).all()
    
    out = []
    for r in results:
        resume_name = r.resume.filename if r.resume else "Unknown Resume"
        raw_title = r.job_description.title if r.job_description else None
        is_mode_label = (raw_title or "").strip().lower() in ATS_ASSESSMENT_MODE_LABELS
        target_role_display = None if is_mode_label else raw_title
        assessment_mode_display = raw_title if is_mode_label else ("Resume + Target Role" if raw_title else "General Resume Quality")
        out.append({
            "id": r.id,
            "resume_id": r.resume_id,
            "resume_filename": resume_name,
            "job_title": target_role_display or "General Resume Quality",
            "target_role": target_role_display,
            "assessment_mode": assessment_mode_display,
            "ats_score": r.ats_score,
            "semantic_score": r.semantic_score,
            "skill_match_score": r.skill_match_score,
            "matched_skills": json.loads(r.matched_skills or "[]"),
            "missing_skills": json.loads(r.missing_skills or "[]"),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return out

@app.get("/api/ats/{result_id}")
def get_ats_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    r = db.query(AtsResult).filter(
        AtsResult.id == result_id,
        AtsResult.user_id == current_user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="ATS result not found.")

    raw_title = r.job_description.title if r.job_description else None
    is_mode_label = (raw_title or "").strip().lower() in ATS_ASSESSMENT_MODE_LABELS
    target_role_display = None if is_mode_label else raw_title
    assessment_mode_display = raw_title if is_mode_label else ("Resume + Target Role" if raw_title else "General Resume Quality")

    return {
        "id": r.id,
        "resume_id": r.resume_id,
        "resume_filename": r.resume.filename if r.resume else "Unknown Resume",
        "job_title": target_role_display or "General Resume Quality",
        "target_role": target_role_display,
        "assessment_mode": assessment_mode_display,
        "ats_score": r.ats_score,
        "semantic_score": r.semantic_score,
        "skill_match_score": r.skill_match_score,
        "matched_skills": json.loads(r.matched_skills or "[]"),
        "missing_skills": json.loads(r.missing_skills or "[]"),
        "created_at": r.created_at.isoformat() if r.created_at else None
    }

@app.post("/api/ats/analyze")
def analyze_ats(req: AtsRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = get_user_active_resume(db, current_user, req.resume_id)
    if not resume.extracted_text or not resume.extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Cannot analyze resume: extracted text is empty or unreadable. Please upload a clear text PDF or DOCX resume."
        )

    clean_title = (req.job_title or "").strip()
    clean_jd = (req.job_description or "").strip()

    # Separate assessment_mode from target_role
    if clean_title and clean_jd:
        assessment_mode = "Resume + Target Role + Job Description"
    elif clean_jd:
        assessment_mode = "Resume + Job Description"
    elif clean_title:
        assessment_mode = "Resume + Target Role"
    else:
        assessment_mode = "General Resume Quality"

    title_to_save = clean_title if clean_title else ("Target Position" if clean_jd else "General Resume Quality")
    desc_to_save = clean_jd if clean_jd else "Baseline resume-quality and ATS readiness evaluation."

    jd_record = JobDescription(
        user_id=current_user.id,
        title=title_to_save,
        description=desc_to_save
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    cand_info = extract_candidate_info(resume.extracted_text)

    # Filter out assessment labels from parsed candidate_info
    if cand_info.get("target_role") and cand_info["target_role"].strip().lower() in ATS_ASSESSMENT_MODE_LABELS:
        cand_info["target_role"] = None

    # ── Role inference pipeline ─────────────────────────────────────────────
    role_inference = infer_target_role(
        resume_text=resume.extracted_text,
        explicit_role=clean_title if clean_title else None,
    )
    inferred_role        = role_inference["target_role"]
    inferred_role_source = role_inference["target_role_source"]
    inferred_confidence  = role_inference["target_role_confidence"]
    role_unclear         = role_inference["target_role_unclear"]

    # Final target_role for display.
    # Priority:
    # 1. Explicit user-selected role (highest)
    # 2. Explicit role from resume headline/objective (resume_explicit via parser)
    # 3. Role inferred from signals (resume_inferred) — only when no explicit found
    # 4. None (→ "Not provided")
    # Note: resume_explicit from parser takes precedence over resume_inferred because
    # a stated headline ("Name - Senior Backend Engineer") is more reliable than signals.
    resume_parser_role = cand_info.get("target_role")
    target_role_val = None
    if clean_title and clean_title.lower() not in ATS_ASSESSMENT_MODE_LABELS:
        target_role_val = clean_title
        inferred_role_source = "user_selected"
        inferred_confidence = 1.0
        role_unclear = False
    elif resume_parser_role:
        # Headline / objective text extracted by the parser is treated as resume_explicit
        target_role_val = resume_parser_role.strip()
        inferred_role_source = "resume_explicit"
        inferred_confidence = 0.92
        role_unclear = False
    elif inferred_role and inferred_role_source not in ("not_found",):
        target_role_val = inferred_role
    # else: target_role_val stays None

    # Pass inferred role to scorer when no explicit title was given and inference was confident
    score_title = clean_title
    if not score_title and target_role_val and not role_unclear:
        score_title = target_role_val

    try:
        ats_data = calculate_ats_score(
            resume.extracted_text,
            job_description=clean_jd if clean_jd else None,
            job_title=score_title if score_title else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during calculate_ats_score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ATS calculation encountered an error: {str(e)}")

    ats_score_val         = float(ats_data.get("ats_score", 0.0) or 0.0)
    semantic_score_val    = float(ats_data.get("semantic_score", 0.0) or 0.0)
    skill_match_score_val = float(ats_data.get("skill_match_score", 0.0) or 0.0)
    matched_skills_list   = ats_data.get("matched_skills", []) or []
    missing_skills_list   = ats_data.get("missing_skills", []) or []
    analysis_mode         = ats_data.get("analysis_mode", assessment_mode)

    logger.info(
        f"[ATS Analysis] resume_id={resume.id}, words={ats_data.get('word_count')}, "
        f"mode={analysis_mode}, score={ats_score_val}, "
        f"structure={ats_data.get('structure_score')} (w={ats_data.get('structure_weight', 30)}), "
        f"skill={ats_data.get('skill_density_score')} (w={ats_data.get('skill_density_weight', 30)}), "
        f"impact={ats_data.get('content_impact_score')} (w={ats_data.get('content_impact_weight', 25)}), "
        f"length={ats_data.get('length_score')} (w={ats_data.get('length_weight', 15)})"
    )

    ats_result = AtsResult(
        user_id=current_user.id,
        resume_id=resume.id,
        job_description_id=jd_record.id,
        ats_score=ats_score_val,
        semantic_score=semantic_score_val,
        skill_match_score=skill_match_score_val,
        matched_skills=json.dumps(matched_skills_list),
        missing_skills=json.dumps(missing_skills_list)
    )
    db.add(ats_result)
    db.commit()
    db.refresh(ats_result)

    return {
        "ats_result_id": ats_result.id,
        "resume_id": resume.id,
        "resume_filename": resume.filename,
        "job_title": clean_title if clean_title else ("Target Position" if clean_jd else None),
        "target_role": target_role_val,
        "target_role_source": inferred_role_source,
        "target_role_confidence": inferred_confidence,
        "target_role_unclear": role_unclear,
        "assessment_mode": assessment_mode,
        "analysis_mode": analysis_mode,
        "candidate_info": cand_info,
        "ats_score": ats_score_val,
        # Three-tier scores
        "resume_quality_score": ats_data.get("resume_quality_score"),
        "role_match_score": ats_data.get("role_match_score"),
        "jd_match_score": ats_data.get("jd_match_score"),
        "semantic_score": semantic_score_val,
        "skill_match_score": skill_match_score_val,
        "matched_skills": matched_skills_list,
        "missing_skills": missing_skills_list,
        "matched_skills_count": len(matched_skills_list),
        "missing_skills_count": len(missing_skills_list),
        "total_job_skills": len(matched_skills_list) + len(missing_skills_list),
        "structure_score": ats_data.get("structure_score"),
        "skill_density_score": ats_data.get("skill_density_score"),
        "content_impact_score": ats_data.get("content_impact_score"),
        "length_score": ats_data.get("length_score"),
        "structure_weight": ats_data.get("structure_weight", 30),
        "skill_density_weight": ats_data.get("skill_density_weight", 30),
        "content_impact_weight": ats_data.get("content_impact_weight", 25),
        "length_weight": ats_data.get("length_weight", 15),
        "word_count": ats_data.get("word_count"),
        "role_skill_coverage": ats_data.get("role_skill_coverage"),
        "benchmark_is_exact": ats_data.get("benchmark_is_exact"),
        "scoring_note": ats_data.get("scoring_note", ""),
        "strengths": ats_data.get("strengths", []),
        "areas_to_improve": ats_data.get("areas_to_improve", []),
        "recommended_next_steps": ats_data.get("recommended_next_steps", []),
        "debug_info": {
            "resume_id": resume.id,
            "word_count": ats_data.get("word_count"),
            "sections_detected": [k for k, v in cand_info.items() if v and k in ["name", "email", "phone", "education", "experience", "projects", "certifications"]],
            "verified_skills_count": len(matched_skills_list),
            "component_scores": {
                "structure": ats_data.get("structure_score"),
                "skill_evidence": ats_data.get("skill_density_score"),
                "content_impact": ats_data.get("content_impact_score"),
                "document_length": ats_data.get("length_score")
            },
            "component_weights": {
                "structure": ats_data.get("structure_weight", 30),
                "skill_evidence": ats_data.get("skill_density_weight", 30),
                "content_impact": ats_data.get("content_impact_weight", 25),
                "document_length": ats_data.get("length_weight", 15)
            },
            "final_score": ats_score_val,
            "analysis_mode": analysis_mode
        },
        "created_at": ats_result.created_at.isoformat() if ats_result.created_at else None
    }



# 
# Interview Endpoints (Phase 6 & 8)
# 

class StartInterviewRequest(BaseModel):
    resume_id: Optional[int] = None
    job_description: Optional[str] = Field(None, max_length=15000)
    interview_type: str = Field("Technical", max_length=30)
    difficulty: str = Field("Medium", max_length=20)
    num_questions: int = Field(5, ge=1, le=15)

class SubmitAnswerRequest(BaseModel):
    question_id: int
    user_answer: str = Field(..., min_length=1, max_length=10000)

class DynamicQuestionRequest(BaseModel):
    resume_id: Optional[int] = None
    interview_type: str = "Technical"
    difficulty: str = "Medium"
    job_description: Optional[str] = None
    previous_qa: Optional[List[Dict[str, str]]] = None

class FollowupQuestionRequest(BaseModel):
    resume_id: Optional[int] = None
    previous_question: str = Field(..., max_length=1000)
    previous_answer: str = Field(..., max_length=10000)

class LlmFeedbackRequest(BaseModel):
    resume_id: Optional[int] = None
    question: str = Field(..., max_length=1000)
    answer: str = Field(..., max_length=10000)

@app.post("/api/interview/start")
def start_interview(
    req: StartInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, req.resume_id)

    model_status = get_model_status()
    if not model_status["available"]:
        raise HTTPException(
            status_code=503,
            detail=f"Sentence-transformer model unavailable: {model_status['error']}. Cannot start interview."
        )

    skill_records = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
    resume_skills = [s.skill_name for s in skill_records]
    predicted_role = resume.predicted_role or "Software Engineer"

    raw_questions = generate_interview_questions(
        predicted_role=predicted_role,
        resume_skills=resume_skills,
        interview_type=req.interview_type,
        difficulty=req.difficulty,
        num_questions=req.num_questions,
        job_description=req.job_description,
    )

    if not raw_questions:
        raise HTTPException(status_code=500, detail="Could not generate questions.")

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id,
        job_description=req.job_description,
        interview_type=req.interview_type,
        difficulty=req.difficulty,
        num_questions=len(raw_questions),
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    questions_out = []
    for idx, q in enumerate(raw_questions):
        q_record = InterviewQuestion(
            session_id=session.id,
            question_text=q["question"],
            question_type=req.interview_type,
            category=q.get("category", "general"),
            difficulty=req.difficulty,
            ideal_answer=q["ideal_answer"],
            keywords=json.dumps(q.get("keywords", [])),
            order_index=idx,
        )
        db.add(q_record)
        db.commit()
        db.refresh(q_record)
        questions_out.append({
            "id": q_record.id,
            "order_index": idx,
            "question": q["question"],
            "question_type": req.interview_type,
            "category": q.get("category", "general"),
            "difficulty": req.difficulty,
        })

    return {
        "session_id": session.id,
        "resume_id": resume.id,
        "predicted_role": predicted_role,
        "interview_type": req.interview_type,
        "difficulty": req.difficulty,
        "num_questions": len(raw_questions),
        "status": "in_progress",
        "questions": questions_out,
    }

@app.get("/api/interview/sessions")
def get_interview_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).all()
    return [
        {
            "session_id": s.id,
            "resume_id": s.resume_id,
            "interview_type": s.interview_type,
            "difficulty": s.difficulty,
            "status": s.status,
            "num_questions": s.num_questions,
            "overall_score": s.overall_score,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]

@app.get("/api/interview/{session_id}")
def get_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index).all()

    answered_ids = {a.question_id for a in db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()}

    return {
        "session_id": session.id,
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "status": session.status,
        "num_questions": session.num_questions,
        "overall_score": session.overall_score,
        "questions": [
            {
                "id": q.id,
                "order_index": q.order_index,
                "question": q.question_text,
                "question_type": q.question_type,
                "category": q.category,
                "difficulty": q.difficulty,
                "answered": q.id in answered_ids,
            }
            for q in questions
        ],
    }

@app.post("/api/interview/{session_id}/answer")
def submit_answer(
    session_id: int,
    req: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="This interview session is already completed.")
    if session.status == "cancelled":
        raise HTTPException(status_code=400, detail="This interview session was cancelled.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == req.question_id,
        InterviewQuestion.session_id == session_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this session.")

    existing = db.query(InterviewAnswer).filter(
        InterviewAnswer.question_id == req.question_id,
        InterviewAnswer.session_id == session_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This question has already been answered.")

    if not req.user_answer or not req.user_answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")

    try:
        keywords = json.loads(question.keywords)
        result = evaluate_answer(req.user_answer, question.ideal_answer, keywords)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    answer_record = InterviewAnswer(
        session_id=session_id,
        question_id=question.id,
        user_answer=req.user_answer,
        semantic_score=result["semantic_score"],
        keyword_score=result["keyword_score"],
        combined_score=result["combined_score"],
        feedback=result["feedback"],
    )
    db.add(answer_record)
    db.commit()
    db.refresh(answer_record)

    answered_count = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).count()
    next_index = question.order_index + 1
    is_last = next_index >= session.num_questions

    return {
        "question_id": question.id,
        "order_index": question.order_index,
        "semantic_score": result["semantic_score"],
        "keyword_score": result["keyword_score"],
        "combined_score": result["combined_score"],
        "feedback": result["feedback"],
        "matched_keywords": result["matched_keywords"],
        "missing_keywords": result["missing_keywords"],
        "answered_count": answered_count,
        "total_questions": session.num_questions,
        "is_last_question": is_last,
        "next_question_index": next_index if not is_last else None,
    }

@app.post("/api/interview/{session_id}/complete")
def complete_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed.")

    answers = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()
    questions = {q.id: q for q in db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).all()}

    answer_records = [
        {
            "question_text": questions[a.question_id].question_text if a.question_id in questions else "",
            "category": questions[a.question_id].category if a.question_id in questions else "general",
            "combined_score": a.combined_score,
            "semantic_score": a.semantic_score,
            "keyword_score": a.keyword_score,
            "feedback": a.feedback,
        }
        for a in answers
    ]

    report = generate_final_report(answer_records)

    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    session.overall_score = report["overall_score"]
    session.avg_semantic_score = report["avg_semantic_score"]
    session.avg_keyword_score = report["avg_keyword_score"]
    session.strengths = json.dumps(report["strengths"])
    session.improvement_areas = json.dumps(report["improvement_areas"])
    db.commit()

    # Automatically persist interview recommendation if score < 70 or weaknesses found
    if report["overall_score"] < 70 or report["improvement_areas"]:
        rec = Recommendation(
            user_id=current_user.id,
            resume_id=session.resume_id,
            type="interview",
            title="Mock Interview Performance Insights",
            description=f"Based on your recent interview (Score: {report['overall_score']:.0f}), focus on strengthening: {', '.join(report['improvement_areas'][:2]) or 'technical concepts'}.",
            priority="High" if report["overall_score"] < 50 else "Medium",
            source="llm" if get_llm_config()["has_api_key"] else "fallback",
            metadata_json=json.dumps({"session_id": session.id, "score": report["overall_score"]})
        )
        db.add(rec)
        db.commit()

    return {
        "session_id": session_id,
        "status": "completed",
        **report,
    }

@app.get("/api/interview/{session_id}/report")
def get_interview_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session not yet completed.")

    questions = {q.id: q for q in db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index).all()}

    answers = {a.question_id: a for a in db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()}

    qa_pairs = []
    for q_id, q in questions.items():
        a = answers.get(q_id)
        qa_pairs.append({
            "order_index": q.order_index,
            "question": q.question_text,
            "question_type": q.question_type,
            "category": q.category,
            "difficulty": q.difficulty,
            "user_answer": a.user_answer if a else None,
            "combined_score": a.combined_score if a else None,
            "semantic_score": a.semantic_score if a else None,
            "keyword_score": a.keyword_score if a else None,
            "feedback": a.feedback if a else "Not answered",
        })

    return {
        "session_id": session_id,
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "overall_score": session.overall_score,
        "avg_semantic_score": session.avg_semantic_score,
        "avg_keyword_score": session.avg_keyword_score,
        "strengths": json.loads(session.strengths or "[]"),
        "improvement_areas": json.loads(session.improvement_areas or "[]"),
        "questions_and_answers": qa_pairs,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }


# 
# Dynamic LLM Endpoints (Phase 8)
# 

@app.post("/api/llm/interview/question")
def llm_interview_question(
    req: DynamicQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == req.resume_id,
        ResumeRecord.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    skills = [s.skill_name for s in resume.skills]
    resume_context = {
        "predicted_role": resume.predicted_role,
        "skills": skills,
        "job_description": req.job_description
    }

    result = generate_dynamic_question(
        resume_context=resume_context,
        interview_type=req.interview_type,
        difficulty=req.difficulty,
        previous_qa=req.previous_qa
    )
    return result

@app.post("/api/llm/interview/followup")
def llm_interview_followup(
    req: FollowupQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == req.resume_id,
        ResumeRecord.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume_context = {
        "predicted_role": resume.predicted_role,
        "skills": [s.skill_name for s in resume.skills]
    }
    result = generate_followup_question(
        previous_question=req.previous_question,
        previous_answer=req.previous_answer,
        resume_context=resume_context
    )
    return result

@app.post("/api/llm/interview/feedback")
def llm_interview_feedback(
    req: LlmFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(ResumeRecord).filter(
        ResumeRecord.id == req.resume_id,
        ResumeRecord.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume_context = {
        "predicted_role": resume.predicted_role,
        "skills": [s.skill_name for s in resume.skills]
    }
    result = generate_answer_feedback(
        question=req.question,
        answer=req.answer,
        resume_context=resume_context
    )
    return result


# 
# Recommendations & Roadmap Endpoints (Phase 8)
# 

class AnalyzeRecommendationsRequest(BaseModel):
    resume_id: Optional[int] = None
    job_description_id: Optional[int] = None
    job_description_text: Optional[str] = Field(None, max_length=15000)

@app.post("/api/recommendations/analyze")
def analyze_recommendations(
    req: AnalyzeRecommendationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, req.resume_id)

    current_skills = [s.skill_name for s in resume.skills]
    target_role = resume.predicted_role or "Software Engineer"
    jd_text = req.job_description_text or ""

    if req.job_description_id:
        jd_rec = db.query(JobDescription).filter(
            JobDescription.id == req.job_description_id,
            JobDescription.user_id == current_user.id
        ).first()
        if jd_rec:
            jd_text = jd_rec.description

    missing_skills = []
    if jd_text:
        jd_skills_dict = extract_skills(jd_text, exclude_projects=False)
        jd_skills = [s for sk_list in jd_skills_dict.values() for s in sk_list]
        curr_lower = [s.lower() for s in current_skills]
        missing_skills = [s for s in jd_skills if s.lower() not in curr_lower]

    if not missing_skills:
        if "Data Science" in target_role:
            standard = ["Docker", "AWS", "PyTorch", "MLOps", "Airflow", "Kubernetes"]
        elif "Java" in target_role:
            standard = ["Docker", "Kubernetes", "Kafka", "AWS", "Microservices", "Redis"]
        else:
            standard = ["Docker", "CI/CD", "AWS", "System Design", "Unit Testing", "Redis"]
        curr_lower = [s.lower() for s in current_skills]
        missing_skills = [s for s in standard if s.lower() not in curr_lower]

    explanation = generate_skill_gap_explanation(
        current_skills=current_skills,
        target_role=target_role,
        missing_skills=missing_skills,
        jd_text=jd_text
    )

    recent_session = db.query(InterviewSession).filter(
        InterviewSession.resume_id == resume.id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == "completed"
    ).order_by(InterviewSession.completed_at.desc()).first()

    interview_weaknesses = []
    if recent_session and recent_session.improvement_areas:
        interview_weaknesses = json.loads(recent_session.improvement_areas)

    roadmap = generate_learning_roadmap(
        current_skills=current_skills,
        target_role=target_role,
        gaps=explanation.get("gaps", []),
        interview_weaknesses=interview_weaknesses
    )

    # Persist skill gap recommendation
    if explanation.get("gaps"):
        top_gap = explanation["gaps"][0]
        db.add(Recommendation(
            user_id=current_user.id,
            resume_id=resume.id,
            job_description_id=req.job_description_id,
            type="skill_gap",
            title=f"Priority Skill Gap: {top_gap['skill']}",
            description=top_gap.get("why_it_matters", f"Essential skill for {target_role}"),
            priority=top_gap.get("priority", "High"),
            source=explanation.get("source", "llm"),
            metadata_json=json.dumps(top_gap)
        ))

    # Persist roadmap recommendation
    db.add(Recommendation(
        user_id=current_user.id,
        resume_id=resume.id,
        job_description_id=req.job_description_id,
        type="learning",
        title=f"Personalized Roadmap for {target_role}",
        description=f"{len(roadmap.get('roadmap', []))}-step structured learning plan targeting your profile gaps.",
        priority="High",
        source=roadmap.get("source", "llm"),
        metadata_json=json.dumps(roadmap)
    ))
    db.commit()

    return {
        "resume_id": resume.id,
        "target_role": target_role,
        "current_skills": current_skills,
        "missing_skills": missing_skills,
        "skill_gaps": explanation.get("gaps", []),
        "gap_summary": explanation.get("summary", ""),
        "learning_roadmap": roadmap.get("roadmap", []),
        "interview_weaknesses": interview_weaknesses,
        "source": explanation.get("source", "llm")
    }

@app.get("/api/recommendations")
def get_recommendations(
    resume_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    eff_resume_id = resume_id or current_user.active_resume_id
    query = db.query(Recommendation).filter(Recommendation.user_id == current_user.id)
    if eff_resume_id:
        query = query.filter(Recommendation.resume_id == eff_resume_id)
    recs = query.order_by(Recommendation.created_at.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "resume_id": r.resume_id,
            "type": r.type,
            "title": r.title,
            "description": r.description,
            "priority": r.priority,
            "source": r.source,
            "metadata": json.loads(r.metadata_json or "{}"),
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in recs
    ]

@app.get("/api/recommendations/roadmap")
def get_roadmap(
    resume_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, resume_id)

    current_skills = [s.skill_name for s in resume.skills]
    target_role = resume.predicted_role or "Software Engineer"

    gaps = [
        {"skill": "Docker & Containers", "priority": "High", "why_it_matters": "Containerization is required for scalable microservices."},
        {"skill": "Cloud Deployment (AWS)", "priority": "High", "why_it_matters": "Cloud architecture is essential for enterprise roles."},
        {"skill": "System Design & Caching", "priority": "Medium", "why_it_matters": "High-throughput systems require Redis and message queues."}
    ]

    roadmap = generate_learning_roadmap(
        current_skills=current_skills,
        target_role=target_role,
        gaps=gaps
    )
    return roadmap


# 
# Resume Improvement Analysis (Phase 8)
# 

class ResumeAnalyzeRequest(BaseModel):
    resume_id: Optional[int] = None
    target_role: Optional[str] = Field(None, max_length=100)

@app.post("/api/resume/analyze")
def analyze_resume(
    req: ResumeAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, req.resume_id)

    role = req.target_role or resume.predicted_role or "Software Engineer"
    analysis = generate_resume_improvements(resume.extracted_text, role)

    db.add(Recommendation(
        user_id=current_user.id,
        resume_id=resume.id,
        type="resume",
        title=f"Resume Action Items for {role}",
        description=analysis.get("summary", "Resume improvement recommendations"),
        priority="Medium",
        source=analysis.get("source", "llm"),
        metadata_json=json.dumps(analysis)
    ))
    db.commit()

    return {
        "resume_id": resume.id,
        "target_role": role,
        **analysis
    }


# 
# RAG Knowledge Base Query Endpoint (Phase 8)
# 

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    resume_id: Optional[int] = None
    history: Optional[List[Dict[str, Any]]] = None

@app.post("/api/rag/query")
def rag_query(
    req: RagQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    candidate_context = None
    try:
        resume = get_user_active_resume(db, current_user, req.resume_id)
        candidate_context = {
            "target_role": resume.predicted_role,
            "skills": [s.skill_name for s in resume.skills]
        }
    except Exception:
        candidate_context = None

    result = answer_with_rag(req.query.strip(), candidate_context, history=req.history)
    return result


# 
# Dedicated Resume Practice Endpoints
# 

class StartPracticeRequest(BaseModel):
    resume_id: Optional[int] = None
    question_source: str = "resume_based" # aptitude, fundamental_concepts, problem_solving, resume_based
    question_count: int = Field(10, description="10, 20, or 30 questions")
    difficulty: str = "Medium"
    practice_type: str = "Technical"
    job_description: Optional[str] = None

@app.post("/api/practice/start")
def start_practice(
    req: StartPracticeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    source = req.question_source.lower()
    resume = None

    if source == "resume_based":
        resume = get_user_active_resume(db, current_user, req.resume_id)
    else:
        try:
            resume = get_user_active_resume(db, current_user, req.resume_id)
        except Exception:
            resume = None

    q_count = req.question_count
    if q_count not in [10, 20, 30]:
        q_count = 10

    skills = [s.skill_name for s in resume.skills] if resume else []
    predicted_role = (resume.predicted_role if resume else "Software Engineer") or "Software Engineer"
    resume_text = resume.extracted_text if resume else ""

    # Fetch recently served question texts for this user and source to minimize immediate repetition
    recent_q_records = db.query(PracticeQuestion.question_text).join(PracticeSession).filter(
        PracticeSession.user_id == current_user.id,
        PracticeSession.question_source == source
    ).order_by(PracticeSession.started_at.desc()).limit(100).all()

    recently_served_keys = {generate_question_key(r[0]) for r in recent_q_records}

    # Generate personalized questions based on category & difficulty with repetition avoidance
    raw_questions = generate_practice_questions(
        resume_text=resume_text,
        skills=skills,
        predicted_role=predicted_role,
        question_count=q_count,
        difficulty=req.difficulty,
        practice_type=req.practice_type,
        job_description=req.job_description,
        question_source=source,
        recently_served_keys=recently_served_keys
    )

    session = PracticeSession(
        user_id=current_user.id,
        resume_id=resume.id if resume else None,
        job_description=req.job_description,
        question_source=source,
        question_count=len(raw_questions),
        total_marks=len(raw_questions) * 2,
        earned_marks=0,
        difficulty=req.difficulty.capitalize(),
        practice_type=req.practice_type,
        status="in_progress"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Save practice questions
    sanitized_questions = []
    for q_item in raw_questions:
        options_val = json.dumps(q_item.get("options")) if q_item.get("options") else None
        q_rec = PracticeQuestion(
            session_id=session.id,
            question_text=q_item["question"],
            question_type=q_item.get("question_type", req.practice_type),
            category=q_item.get("category", "General"),
            difficulty=q_item.get("difficulty", req.difficulty),
            order_index=q_item["order_index"],
            ideal_answer=q_item["ideal_answer"],
            keywords=json.dumps(q_item["keywords"]),
            options=options_val,
            correct_option=q_item.get("correct_option"),
            problem_type=q_item.get("problem_type"),
            max_marks=2
        )
        db.add(q_rec)
        db.flush()
        sanitized_questions.append({
            "id": q_rec.id,
            "order_index": q_rec.order_index,
            "question_text": q_rec.question_text,
            "question_type": q_rec.question_type,
            "category": q_rec.category,
            "difficulty": q_rec.difficulty,
            "options": q_item.get("options"),
            "problem_type": q_item.get("problem_type"),
            "max_marks": 2,
            "answered": False
        })
    db.commit()

    return {
        "session_id": session.id,
        "resume_id": resume.id if resume else None,
        "resume_filename": resume.filename if resume else "General",
        "predicted_role": predicted_role,
        "question_source": session.question_source,
        "question_count": session.question_count,
        "total_marks": session.total_marks or (len(raw_questions) * 2),
        "earned_marks": 0,
        "difficulty": session.difficulty,
        "practice_type": session.practice_type,
        "status": session.status,
        "questions": sanitized_questions,
        "created_at": session.started_at.isoformat()
    }

@app.get("/api/practice/sessions")
def get_practice_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(PracticeSession).filter(
        PracticeSession.user_id == current_user.id
    ).order_by(PracticeSession.started_at.desc()).all()

    out = []
    for s in sessions:
        out.append({
            "session_id": s.id,
            "resume_id": s.resume_id,
            "resume_filename": s.resume.filename if s.resume else "General",
            "question_source": s.question_source,
            "question_count": s.question_count,
            "difficulty": s.difficulty,
            "practice_type": s.practice_type,
            "status": s.status,
            "overall_score": s.overall_score,
            "total_answered": len(s.answers),
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        })
    return out

@app.post("/api/practice/{session_id}/exit")
def exit_practice_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found.")

    session.status = "EXITED_BY_CANDIDATE"
    session.completed_at = datetime.datetime.utcnow()

    answers_list = []
    for a in session.answers:
        answers_list.append({
            "semantic_score": a.semantic_score,
            "keyword_score": a.keyword_score,
            "combined_score": a.combined_score,
            "feedback": a.feedback,
            "is_correct": a.is_correct,
            "marks_awarded": a.marks_awarded,
            "max_marks": a.max_marks
        })

    if answers_list:
        report_metrics = calculate_practice_report(answers_list)
        session.overall_score = report_metrics["overall_score"]
        session.avg_semantic_score = report_metrics["avg_semantic_score"]
        session.avg_keyword_score = report_metrics["avg_keyword_score"]
        session.strengths = json.dumps(report_metrics["strengths"])
        session.improvement_areas = json.dumps(report_metrics["improvement_areas"])
        session.total_marks = report_metrics.get("total_marks", (session.question_count or 10) * 2)
        session.earned_marks = report_metrics.get("earned_marks", sum(a.marks_awarded or 0 for a in session.answers))

    db.commit()

    return {
        "session_id": session.id,
        "status": session.status,
        "total_answered": len(session.answers),
        "question_count": session.question_count,
        "overall_score": session.overall_score,
        "completed_at": session.completed_at.isoformat()
    }

@app.get("/api/practice/{session_id}")
def get_practice_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found.")

    questions_out = []
    for q in session.questions:
        has_ans = q.answer is not None
        ans_data = None
        if has_ans:
            is_corr = q.answer.is_correct if q.answer.is_correct is not None else (q.answer.combined_score >= 50.0)
            m_awarded = q.answer.marks_awarded if q.answer.marks_awarded is not None else (2 if is_corr else 0)
            m_max = q.answer.max_marks or getattr(q, "max_marks", 2) or 2
            ans_data = {
                "user_answer": q.answer.user_answer,
                "semantic_score": q.answer.semantic_score,
                "keyword_score": q.answer.keyword_score,
                "combined_score": q.answer.combined_score,
                "feedback": q.answer.feedback,
                "is_correct": is_corr,
                "marks_awarded": m_awarded,
                "max_marks": m_max,
                "result_status": "Correct" if is_corr else "Incorrect",
                "answered_at": q.answer.answered_at.isoformat(),
                "correct_option": q.correct_option,
                "ideal_answer": q.ideal_answer
            }
        
        parsed_options = None
        if q.options:
            try:
                parsed_options = json.loads(q.options)
            except Exception:
                parsed_options = None

        questions_out.append({
            "id": q.id,
            "order_index": q.order_index,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "category": q.category,
            "difficulty": q.difficulty,
            "options": parsed_options,
            "problem_type": q.problem_type,
            "max_marks": getattr(q, "max_marks", 2) or 2,
            "answered": has_ans,
            "answer_details": ans_data
        })

    total_q_count = session.question_count or len(session.questions)
    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "question_source": session.question_source,
        "question_count": total_q_count,
        "total_marks": session.total_marks or (total_q_count * 2),
        "earned_marks": session.earned_marks or sum((a.marks_awarded if a.marks_awarded is not None else (2 if a.combined_score >= 50.0 else 0)) for a in session.answers),
        "difficulty": session.difficulty,
        "practice_type": session.practice_type,
        "status": session.status,
        "overall_score": session.overall_score,
        "questions": questions_out,
        "total_answered": len(session.answers),
        "started_at": session.started_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

class SubmitPracticeAnswerRequest(BaseModel):
    question_id: int
    user_answer: str = Field(..., min_length=1)

def _recalculate_session_marks(session: PracticeSession, db: Session):
    total_q = session.question_count or len(session.questions)
    session.total_marks = total_q * 2
    earned = 0
    for q in session.questions:
        if q.answer and q.answer.marks_awarded is not None:
            earned += q.answer.marks_awarded
    session.earned_marks = earned
    db.commit()

@app.post("/api/practice/{session_id}/answer")
def submit_practice_answer(
    session_id: int,
    req: SubmitPracticeAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found.")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Practice session is already completed.")

    question = db.query(PracticeQuestion).filter(
        PracticeQuestion.id == req.question_id,
        PracticeQuestion.session_id == session.id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this practice session.")

    max_marks = getattr(question, "max_marks", 2) or 2

    # Evaluate Answer (MCQ vs Standard Descriptive/Coding)
    if question.options and question.correct_option:
        user_choice = req.user_answer.strip().upper()
        correct_letter = question.correct_option.strip().upper()
        is_correct = False
        
        if user_choice.startswith(correct_letter) or (len(user_choice) == 1 and user_choice == correct_letter):
            is_correct = True
        else:
            try:
                opts = json.loads(question.options)
                for opt in opts:
                    if opt.upper().startswith(correct_letter) and (user_choice in opt.upper() or opt.upper() in user_choice):
                        is_correct = True
                        break
            except Exception:
                pass

        marks_awarded = max_marks if is_correct else 0
        if is_correct:
            eval_result = {
                "semantic_score": 100.0,
                "keyword_score": 100.0,
                "combined_score": 100.0,
                "feedback": f"Correct! (Option {correct_letter})\n\nExplanation: {question.ideal_answer}",
                "correct_option": correct_letter,
                "ideal_answer": question.ideal_answer,
                "is_correct": True,
                "result_status": "Correct",
                "marks_awarded": marks_awarded,
                "max_marks": max_marks
            }
        else:
            eval_result = {
                "semantic_score": 0.0,
                "keyword_score": 0.0,
                "combined_score": 0.0,
                "feedback": f"Incorrect. You selected '{req.user_answer.strip()}', but the correct answer is Option {correct_letter}.\n\nExplanation: {question.ideal_answer}",
                "correct_option": correct_letter,
                "ideal_answer": question.ideal_answer,
                "is_correct": False,
                "result_status": "Incorrect",
                "marks_awarded": 0,
                "max_marks": max_marks
            }
    else:
        if session.question_source in ["fundamental_concepts", "resume_based"]:
            context_str = ""
            if session.question_source == "resume_based" and session.resume:
                role_info = session.resume.predicted_role or "Software Engineer"
                skills_info = ", ".join([s.skill_name for s in session.resume.skills]) if session.resume.skills else "Technical skills"
                context_str = f"Candidate Target Role: {role_info}\nRelevant Skills: {skills_info}"

            try:
                eval_dict = evaluate_practice_answer(
                    question_text=question.question_text,
                    ideal_answer=question.ideal_answer,
                    user_answer=req.user_answer,
                    max_marks=max_marks,
                    context=context_str
                )
            except PracticeEvaluationUnavailableError as peu:
                logger.error(f"[SubmitPracticeAnswer] Groq evaluation unavailable: {peu}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Answer evaluation service is temporarily unavailable. Please try submitting again."
                )

            is_correct = eval_dict["is_correct"]
            marks_awarded = eval_dict["marks_awarded"]
            reason = eval_dict["reason"]

            eval_result = {
                "semantic_score": 100.0 if is_correct else 0.0,
                "keyword_score": 100.0 if is_correct else 0.0,
                "combined_score": 100.0 if is_correct else 0.0,
                "feedback": reason,
                "ideal_answer": question.ideal_answer,
                "is_correct": is_correct,
                "result_status": "Correct" if is_correct else "Incorrect",
                "marks_awarded": marks_awarded,
                "max_marks": max_marks
            }
        else:
            cleaned_user_answer = req.user_answer.strip()
            keywords_list = json.loads(question.keywords or "[]")
            eval_result = evaluate_answer(
                user_answer=cleaned_user_answer,
                ideal_answer=question.ideal_answer,
                keywords=keywords_list
            )

            comb_score = float(eval_result.get("combined_score", 0.0))
            sem_score = float(eval_result.get("semantic_score", 0.0))
            kw_score = float(eval_result.get("keyword_score", 0.0))
            user_words = cleaned_user_answer.split()

            is_substantive = len(user_words) >= 3
            is_correct = False
            if is_substantive:
                if comb_score >= 50.0:
                    is_correct = True
                elif sem_score >= 48.0 and kw_score >= 25.0:
                    is_correct = True
                elif kw_score >= 60.0 and sem_score >= 40.0:
                    is_correct = True

            marks_awarded = max_marks if is_correct else 0
            eval_result["is_correct"] = is_correct
            eval_result["result_status"] = "Correct" if is_correct else "Incorrect"
            eval_result["marks_awarded"] = marks_awarded
            eval_result["max_marks"] = max_marks

    existing_ans = db.query(PracticeAnswer).filter(PracticeAnswer.question_id == question.id).first()
    if existing_ans:
        existing_ans.user_answer = req.user_answer.strip()
        existing_ans.semantic_score = eval_result["semantic_score"]
        existing_ans.keyword_score = eval_result["keyword_score"]
        existing_ans.combined_score = eval_result["combined_score"]
        existing_ans.feedback = eval_result["feedback"]
        existing_ans.is_correct = eval_result["is_correct"]
        existing_ans.marks_awarded = eval_result["marks_awarded"]
        existing_ans.max_marks = eval_result["max_marks"]
        existing_ans.answered_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing_ans)
        _recalculate_session_marks(session, db)
        return {
            "answer_id": existing_ans.id,
            "question_id": question.id,
            "order_index": question.order_index,
            **eval_result
        }

    ans_rec = PracticeAnswer(
        session_id=session.id,
        question_id=question.id,
        user_answer=req.user_answer.strip(),
        semantic_score=eval_result["semantic_score"],
        keyword_score=eval_result["keyword_score"],
        combined_score=eval_result["combined_score"],
        feedback=eval_result["feedback"],
        is_correct=eval_result["is_correct"],
        marks_awarded=eval_result["marks_awarded"],
        max_marks=eval_result["max_marks"]
    )
    db.add(ans_rec)
    db.commit()
    db.refresh(ans_rec)
    _recalculate_session_marks(session, db)

    return {
        "answer_id": ans_rec.id,
        "question_id": question.id,
        "order_index": question.order_index,
        **eval_result
    }

@app.post("/api/practice/{session_id}/complete")
def complete_practice_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found.")

    answers_list = []
    for a in session.answers:
        answers_list.append({
            "semantic_score": a.semantic_score,
            "keyword_score": a.keyword_score,
            "combined_score": a.combined_score,
            "feedback": a.feedback,
            "is_correct": a.is_correct,
            "marks_awarded": a.marks_awarded,
            "max_marks": a.max_marks
        })

    report_metrics = calculate_practice_report(answers_list)
    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    session.overall_score = report_metrics["overall_score"]
    session.avg_semantic_score = report_metrics["avg_semantic_score"]
    session.avg_keyword_score = report_metrics["avg_keyword_score"]
    session.strengths = json.dumps(report_metrics["strengths"])
    session.improvement_areas = json.dumps(report_metrics["improvement_areas"])
    _recalculate_session_marks(session, db)
    db.commit()

    return get_practice_report_internal(session=session)

def get_practice_report_internal(session: PracticeSession) -> Dict[str, Any]:
    qa_breakdown = []
    correct_count = 0
    wrong_count = 0
    total_earned = 0
    total_max = (session.question_count or len(session.questions)) * 2

    for q in session.questions:
        ans = q.answer
        is_ans = bool(ans and ans.user_answer and ans.user_answer.strip())
        is_corr = bool(ans.is_correct) if (ans and ans.is_correct is not None) else (ans.combined_score >= 50.0 if ans else False)
        m_awarded = ans.marks_awarded if (ans and ans.marks_awarded is not None) else (2 if is_corr else 0)
        m_max = (ans.max_marks if (ans and ans.max_marks) else getattr(q, "max_marks", 2)) or 2

        if is_ans:
            if is_corr:
                correct_count += 1
            else:
                wrong_count += 1
            total_earned += m_awarded

        qa_breakdown.append({
            "order_index": q.order_index,
            "question_text": q.question_text,
            "category": q.category,
            "difficulty": q.difficulty,
            "user_answer": ans.user_answer if ans else None,
            "semantic_score": ans.semantic_score if ans else 0.0,
            "keyword_score": ans.keyword_score if ans else 0.0,
            "combined_score": ans.combined_score if ans else 0.0,
            "feedback": ans.feedback if ans else "Unanswered question.",
            "is_correct": is_corr if is_ans else False,
            "result_status": ("Correct" if is_corr else "Incorrect") if is_ans else "Unanswered",
            "marks_awarded": m_awarded if is_ans else 0,
            "max_marks": m_max
        })

    strengths = json.loads(session.strengths or "[]")
    improvements = json.loads(session.improvement_areas or "[]")
    total_q = session.question_count or len(session.questions)
    pass_thresh = 50.0
    user_pct = (correct_count / total_q * 100) if total_q > 0 else 0.0

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "question_source": session.question_source,
        "question_count": total_q,
        "total_answered": len(session.answers),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "earned_marks": total_earned,
        "total_marks": total_max,
        "is_passed": user_pct >= pass_thresh,
        "difficulty": session.difficulty,
        "practice_type": session.practice_type,
        "status": session.status,
        "overall_score": session.overall_score or round(user_pct, 1),
        "avg_semantic_score": session.avg_semantic_score or 0.0,
        "avg_keyword_score": session.avg_keyword_score or 0.0,
        "strengths": strengths,
        "improvement_areas": improvements,
        "questions_and_answers": qa_breakdown,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@app.get("/api/practice/{session_id}/report")
def get_practice_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found.")

    return get_practice_report_internal(session=session)


# 
# Phase 8 — Dedicated Mock Interview Endpoints (30 Resume-Only Questions)
# 

class StartMockInterviewRequest(BaseModel):
    resume_id: Optional[int] = None
    difficulty: str = "Medium" # Easy, Medium, Hard
    job_description: Optional[str] = None

class SubmitMockAnswerRequest(BaseModel):
    question_id: int
    user_answer: str = Field(..., min_length=1)

class RejectMockInterviewRequest(BaseModel):
    reason: str = Field(..., min_length=3)

@app.post("/api/mock-interview/start")
def start_mock_interview(
    req: StartMockInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, req.resume_id)

    skills = [s.skill_name for s in resume.skills]
    predicted_role = resume.predicted_role or "Software Engineer"

    # Generate exactly 30 questions derived ONLY from resume
    raw_questions = generate_mock_interview_30_questions(
        resume_text=resume.extracted_text,
        skills=skills,
        predicted_role=predicted_role,
        difficulty=req.difficulty
    )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id,
        job_description=req.job_description,
        interview_mode="MOCK_INTERVIEW",
        interview_type="Technical",
        difficulty=req.difficulty.capitalize(),
        num_questions=len(raw_questions),
        status="pending",
        integrity_status="PASSED",
        verification_completed=False,
        photo_verified=False,
        questions_completed=0
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Save 30 interview questions
    sanitized_questions = []
    for q_item in raw_questions:
        q_rec = InterviewQuestion(
            session_id=session.id,
            question_text=q_item["question"],
            question_type=q_item.get("question_type", "Technical"),
            category=q_item.get("category", "skill"),
            difficulty=q_item.get("difficulty", req.difficulty),
            order_index=q_item["order_index"],
            ideal_answer=q_item["ideal_answer"],
            keywords=json.dumps(q_item["keywords"])
        )
        db.add(q_rec)
        db.flush()
        sanitized_questions.append({
            "id": q_rec.id,
            "order_index": q_rec.order_index,
            "question_text": q_rec.question_text,
            "question_type": q_rec.question_type,
            "category": q_rec.category,
            "difficulty": q_rec.difficulty,
            "answered": False
        })
    db.commit()

    return {
        "session_id": session.id,
        "resume_id": resume.id,
        "resume_filename": resume.filename,
        "predicted_role": predicted_role,
        "num_questions": session.num_questions,
        "difficulty": session.difficulty,
        "status": session.status,
        "verification_completed": session.verification_completed,
        "questions": sanitized_questions,
        "started_at": session.started_at.isoformat()
    }

@app.post("/api/mock-interview/{session_id}/verify-photo")
def verify_mock_interview_photo(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    session.verification_completed = True
    session.photo_verified = True
    session.verification_timestamp = datetime.datetime.utcnow()
    session.status = "in_progress"
    db.commit()

    return {
        "session_id": session.id,
        "verification_completed": True,
        "photo_verified": True,
        "status": session.status,
        "verification_timestamp": session.verification_timestamp.isoformat()
    }

@app.get("/api/mock-interview/sessions")
def get_mock_interview_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).order_by(InterviewSession.started_at.desc()).all()

    out = []
    for s in sessions:
        out.append({
            "session_id": s.id,
            "resume_id": s.resume_id,
            "resume_filename": s.resume.filename if s.resume else "Resume",
            "num_questions": s.num_questions,
            "difficulty": s.difficulty,
            "status": s.status,
            "integrity_status": s.integrity_status,
            "rejection_reason": s.rejection_reason,
            "overall_score": s.overall_score,
            "questions_completed": s.questions_completed,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        })
    return out

@app.get("/api/mock-interview/{session_id}")
def get_mock_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    questions_out = []
    for q in session.questions:
        has_ans = q.answer is not None
        ans_data = None
        if has_ans:
            ans_data = {
                "user_answer": q.answer.user_answer,
                "semantic_score": q.answer.semantic_score,
                "keyword_score": q.answer.keyword_score,
                "combined_score": q.answer.combined_score,
                "feedback": q.answer.feedback,
                "answered_at": q.answer.answered_at.isoformat()
            }
        questions_out.append({
            "id": q.id,
            "order_index": q.order_index,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "category": q.category,
            "difficulty": q.difficulty,
            "answered": has_ans,
            "answer_details": ans_data
        })

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "num_questions": session.num_questions,
        "difficulty": session.difficulty,
        "status": session.status,
        "integrity_status": session.integrity_status,
        "rejection_reason": session.rejection_reason,
        "verification_completed": session.verification_completed,
        "photo_verified": session.photo_verified,
        "overall_score": session.overall_score,
        "questions_completed": session.questions_completed,
        "questions": questions_out,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@app.post("/api/mock-interview/{session_id}/answer")
def submit_mock_interview_answer(
    session_id: int,
    req: SubmitMockAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    if session.status in ["completed", "REJECTED_INTEGRITY_VIOLATION"]:
        raise HTTPException(status_code=400, detail=f"Interview session is {session.status}.")

    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == req.question_id,
        InterviewQuestion.session_id == session.id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this mock interview.")

    eval_result = evaluate_mock_question(
        question_text=question.question_text,
        category=question.category or "skill",
        question_type=question.question_type or "Technical",
        ideal_answer=question.ideal_answer,
        keywords=json.loads(question.keywords or "[]"),
        user_answer=req.user_answer.strip(),
        resume_text=session.resume.extracted_text if session.resume else ""
    )

    existing_ans = db.query(InterviewAnswer).filter(InterviewAnswer.question_id == question.id).first()
    if existing_ans:
        existing_ans.user_answer = req.user_answer.strip()
        existing_ans.semantic_score = eval_result["semantic_score"]
        existing_ans.keyword_score = eval_result["keyword_score"]
        existing_ans.combined_score = eval_result["combined_score"]
        existing_ans.feedback = eval_result["feedback"]
        existing_ans.answered_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing_ans)
        return {
            "answer_id": existing_ans.id,
            "question_id": question.id,
            "order_index": question.order_index,
            **eval_result
        }

    ans_rec = InterviewAnswer(
        session_id=session.id,
        question_id=question.id,
        user_answer=req.user_answer.strip(),
        semantic_score=eval_result["semantic_score"],
        keyword_score=eval_result["keyword_score"],
        combined_score=eval_result["combined_score"],
        feedback=eval_result["feedback"]
    )
    db.add(ans_rec)
    session.questions_completed = len(session.answers) + 1
    db.commit()
    db.refresh(ans_rec)

    return {
        "answer_id": ans_rec.id,
        "question_id": question.id,
        "order_index": question.order_index,
        **eval_result
    }

@app.post("/api/mock-interview/{session_id}/exit")
def exit_mock_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    session.status = "EXITED_BY_CANDIDATE"
    session.questions_completed = len(session.answers)
    session.completed_at = datetime.datetime.utcnow()

    answers_list = []
    for a in session.answers:
        answers_list.append({
            "semantic_score": a.semantic_score,
            "keyword_score": a.keyword_score,
            "combined_score": a.combined_score,
            "feedback": a.feedback,
            "is_correct": a.combined_score >= 48.0
        })

    if answers_list:
        report_metrics = calculate_mock_interview_report(answers_list)
        session.overall_score = report_metrics["overall_score"]
        session.avg_semantic_score = report_metrics["avg_semantic_score"]
        session.avg_keyword_score = report_metrics["avg_keyword_score"]
        session.strengths = json.dumps(report_metrics["strengths"])
        session.improvement_areas = json.dumps(report_metrics["improvement_areas"])

    db.commit()

    return {
        "session_id": session.id,
        "status": session.status,
        "questions_completed": session.questions_completed,
        "num_questions": session.num_questions,
        "overall_score": session.overall_score,
        "completed_at": session.completed_at.isoformat()
    }

@app.post("/api/mock-interview/{session_id}/reject")
def reject_mock_interview(
    session_id: int,
    req: RejectMockInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    session.status = "REJECTED_INTEGRITY_VIOLATION"
    session.integrity_status = "REJECTED"
    session.rejection_reason = req.reason.strip()
    session.completed_at = datetime.datetime.utcnow()
    db.commit()

    # Dispatch malpractice rejection email
    email_data = {
        "name": current_user.name or "Candidate",
        "email": current_user.email,
        "session_id": session.id,
        "reason": session.rejection_reason,
        "questions_completed": session.questions_completed,
        "total_questions": session.num_questions,
        "timestamp": session.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    email_dispatched, email_msg = send_malpractice_rejection_email(email_data)

    return {
        "session_id": session.id,
        "status": session.status,
        "integrity_status": session.integrity_status,
        "rejection_reason": session.rejection_reason,
        "questions_completed": session.questions_completed,
        "completed_at": session.completed_at.isoformat(),
        "email_dispatched": email_dispatched,
        "email_status": email_msg
    }

@app.post("/api/mock-interview/{session_id}/complete")
def complete_mock_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    if session.status == "REJECTED_INTEGRITY_VIOLATION":
        raise HTTPException(status_code=400, detail="This session was rejected for integrity violation.")

    answers_list = []
    for a in session.answers:
        answers_list.append({
            "semantic_score": a.semantic_score,
            "keyword_score": a.keyword_score,
            "combined_score": a.combined_score,
            "feedback": a.feedback,
            "is_correct": a.combined_score >= 48.0
        })

    report_metrics = calculate_mock_interview_report(answers_list)
    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    session.overall_score = report_metrics["overall_score"]
    session.avg_semantic_score = report_metrics["avg_semantic_score"]
    session.avg_keyword_score = report_metrics["avg_keyword_score"]
    session.strengths = json.dumps(report_metrics["strengths"])
    session.improvement_areas = json.dumps(report_metrics["improvement_areas"])
    db.commit()

    return get_mock_interview_report_internal(session=session)

def get_mock_interview_report_internal(session: InterviewSession) -> Dict[str, Any]:
    qa_breakdown = []
    correct_count = 0
    total_q = len(session.questions) or 30

    for q in session.questions:
        ans = q.answer
        user_ans = ans.user_answer if ans else None
        
        # Evaluate correctness for this question
        is_correct = False
        res_status = "Incorrect"
        if user_ans and user_ans.strip():
            eval_res = evaluate_mock_question(
                question_text=q.question_text,
                category=q.category or "skill",
                question_type=q.question_type or "Technical",
                ideal_answer=q.ideal_answer,
                keywords=json.loads(q.keywords or "[]"),
                user_answer=user_ans,
                resume_text=session.resume.extracted_text if session.resume else ""
            )
            is_correct = eval_res["is_correct"]
            res_status = eval_res["result_status"]
            if is_correct:
                correct_count += 1
        
        qa_breakdown.append({
            "order_index": q.order_index,
            "question_text": q.question_text,
            "category": q.category,
            "difficulty": q.difficulty,
            "user_answer": user_ans,
            "expected_answer": q.ideal_answer,
            "ideal_answer": q.ideal_answer,
            "is_correct": is_correct,
            "result_status": res_status,
            "semantic_score": ans.semantic_score if ans else 0.0,
            "keyword_score": ans.keyword_score if ans else 0.0,
            "combined_score": ans.combined_score if ans else 0.0,
            "feedback": ans.feedback if ans else "Unanswered question."
        })

    strengths = json.loads(session.strengths or "[]")
    improvements = json.loads(session.improvement_areas or "[]")
    percentage = round((correct_count / (total_q if total_q > 0 else 30)) * 100, 1)

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "num_questions": session.num_questions or 30,
        "total_questions": session.num_questions or 30,
        "correct_count": correct_count,
        "percentage": percentage,
        "questions_completed": len(session.answers),
        "difficulty": session.difficulty,
        "status": session.status,
        "integrity_status": session.integrity_status,
        "rejection_reason": session.rejection_reason,
        "overall_score": percentage,
        "avg_semantic_score": session.avg_semantic_score or 0.0,
        "avg_keyword_score": session.avg_keyword_score or 0.0,
        "strengths": strengths,
        "improvement_areas": improvements,
        "questions_and_answers": qa_breakdown,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@app.get("/api/mock-interview/{session_id}/report")
def get_mock_interview_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "MOCK_INTERVIEW"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mock interview session not found.")

    return get_mock_interview_report_internal(session=session)


# 
# Phase 8 — Dedicated AI One-to-One HR Interview Endpoints
# 

class StartAiInterviewRequest(BaseModel):
    resume_id: Optional[int] = None

class SendAiInterviewMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)

@app.post("/api/ai-interview/start")
def start_ai_one_to_one_interview(
    req: StartAiInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = get_user_active_resume(db, current_user, req.resume_id)

    skills = [s.skill_name for s in resume.skills]
    predicted_role = resume.predicted_role or "Software Engineer"

    # Generate initial personalized HR question
    try:
        opening = generate_initial_hr_question(
            resume_text=resume.extracted_text,
            skills=skills,
            predicted_role=predicted_role
        )
    except HrInterviewUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate opening HR question: {e}")
        raise HTTPException(status_code=503, detail="Groq AI Interviewer is currently unavailable. Please try again.")


    initial_transcript = [
        {
            "step_index": 0,
            "speaker": "ai_interviewer",
            "text": opening["question"],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    ]

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id,
        interview_mode="AI_ONE_TO_ONE",
        interview_type="HR",
        difficulty="Medium",
        num_questions=6,
        status="in_progress",
        integrity_status="PASSED",
        conversation_transcript=json.dumps(initial_transcript),
        questions_completed=0
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "resume_id": resume.id,
        "resume_filename": resume.filename,
        "predicted_role": predicted_role,
        "status": session.status,
        "step_index": 0,
        "first_message": opening["question"],
        "conversation_transcript": initial_transcript,
        "started_at": session.started_at.isoformat()
    }

@app.get("/api/ai-interview/sessions")
def get_ai_interview_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "AI_ONE_TO_ONE"
    ).order_by(InterviewSession.started_at.desc()).all()

    out = []
    for s in sessions:
        out.append({
            "session_id": s.id,
            "resume_id": s.resume_id,
            "resume_filename": s.resume.filename if s.resume else "Resume",
            "status": s.status,
            "overall_score": s.overall_score,
            "communication_score": s.communication_score,
            "response_clarity_score": s.response_clarity_score,
            "questions_completed": s.questions_completed,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        })
    return out

@app.get("/api/ai-interview/{session_id}")
def get_ai_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "AI_ONE_TO_ONE"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found.")

    transcript = json.loads(session.conversation_transcript or "[]")

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "status": session.status,
        "overall_score": session.overall_score,
        "communication_score": session.communication_score,
        "response_clarity_score": session.response_clarity_score,
        "conversation_transcript": transcript,
        "questions_completed": session.questions_completed,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@app.post("/api/ai-interview/{session_id}/message")
def send_ai_interview_message(
    session_id: int,
    req: SendAiInterviewMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "AI_ONE_TO_ONE"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found.")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="AI interview session is already completed.")

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")

    transcript = json.loads(session.conversation_transcript or "[]")

    # Get last AI question
    ai_questions = [t["text"] for t in transcript if t.get("speaker") == "ai_interviewer"]
    last_question = ai_questions[-1] if ai_questions else "Tell me about your background."

    resume = session.resume
    skills = [s.skill_name for s in resume.skills] if resume else []
    predicted_role = resume.predicted_role if resume else "Software Engineer"
    resume_text = resume.extracted_text if resume else ""

    candidate_turns = len([t for t in transcript if t.get("speaker") == "candidate"])

    # Prepare candidate message entry without mutating DB session transcript yet
    user_msg_entry = {
        "step_index": len(transcript),
        "speaker": "candidate",
        "text": user_text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    context_transcript = list(transcript) + [user_msg_entry]

    # Generate adaptive HR response using Groq
    try:
        ai_response = generate_next_hr_response(
            previous_question=last_question,
            user_answer=user_text,
            step_index=candidate_turns,
            resume_text=resume_text,
            skills=skills,
            predicted_role=predicted_role,
            history=context_transcript
        )
    except HrInterviewUnavailableError as e:
        # Groq failed. Session transcript was not modified.
        # No duplicate candidate entries in DB; client can retry cleanly.
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error during AI interview response generation: {e}")
        raise HTTPException(status_code=503, detail="Groq AI Interviewer is currently unavailable. Please try again.")

    # Both candidate answer and AI response succeeded; commit atomically to transcript
    transcript.append(user_msg_entry)
    ai_msg_entry = {
        "step_index": len(transcript),
        "speaker": "ai_interviewer",
        "text": ai_response["message"],
        "is_complete": ai_response.get("is_complete", False),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    transcript.append(ai_msg_entry)

    session.conversation_transcript = json.dumps(transcript)
    session.questions_completed = candidate_turns + 1
    db.commit()

    return {
        "session_id": session.id,
        "is_complete": ai_response.get("is_complete", False),
        "ai_message": ai_response["message"],
        "conversation_transcript": transcript,
        "questions_completed": session.questions_completed
    }

@app.post("/api/ai-interview/{session_id}/complete")
def complete_ai_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "AI_ONE_TO_ONE"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found.")

    transcript = json.loads(session.conversation_transcript or "[]")
    resume = session.resume
    skills = [s.skill_name for s in resume.skills] if resume else []
    predicted_role = resume.predicted_role if resume else "Software Engineer"
    resume_text = resume.extracted_text if resume else ""

    eval_result = evaluate_one_to_one_interview(
        dialogue=transcript,
        resume_text=resume_text,
        skills=skills,
        predicted_role=predicted_role
    )

    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    session.overall_score = eval_result["overall_score"]
    session.communication_score = eval_result["communication_score"]
    session.response_clarity_score = eval_result["response_clarity_score"]
    session.strengths = json.dumps(eval_result["strengths"])
    session.improvement_areas = json.dumps(eval_result["improvement_areas"])
    db.commit()

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "predicted_role": predicted_role,
        "status": session.status,
        "overall_score": session.overall_score,
        "communication_score": session.communication_score,
        "response_clarity_score": session.response_clarity_score,
        "relevance_score": eval_result.get("relevance_score", 0.0),
        "strengths": eval_result["strengths"],
        "improvement_areas": eval_result["improvement_areas"],
        "summary": eval_result["summary"],
        "conversation_transcript": transcript,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@app.get("/api/ai-interview/{session_id}/report")
def get_ai_interview_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.interview_mode == "AI_ONE_TO_ONE"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found.")

    transcript = json.loads(session.conversation_transcript or "[]")
    strengths = json.loads(session.strengths or "[]")
    improvements = json.loads(session.improvement_areas or "[]")

    return {
        "session_id": session.id,
        "resume_id": session.resume_id,
        "resume_filename": session.resume.filename if session.resume else "Resume",
        "status": session.status,
        "overall_score": session.overall_score or 0.0,
        "communication_score": session.communication_score or 0.0,
        "response_clarity_score": session.response_clarity_score or 0.0,
        "strengths": strengths,
        "improvement_areas": improvements,
        "conversation_transcript": transcript,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }



# 
# Support Tickets & Help Desk Endpoints
# 

class SupportTicketRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    category: str = Field(..., min_length=2, max_length=100)
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)

@app.post("/api/support/ticket")
def create_support_ticket(
    req: SupportTicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket_code = f"TICK-{uuid.uuid4().hex[:8].upper()}"
    
    user_name = req.name.strip() if req.name and req.name.strip() else current_user.name
    user_email = req.email.strip() if req.email and req.email.strip() else current_user.email

    ticket = SupportTicket(
        ticket_id=ticket_code,
        user_id=current_user.id,
        name=user_name,
        email=user_email,
        category=req.category.strip(),
        subject=req.subject.strip(),
        description=req.description.strip(),
        status="Open"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    email_data = {
        "ticket_id": ticket.ticket_id,
        "name": ticket.name,
        "email": ticket.email,
        "category": ticket.category,
        "subject": ticket.subject,
        "description": ticket.description,
        "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    email_sent, email_msg = send_support_ticket_email(email_data)

    response_msg = "Complaint submitted successfully!"
    if email_sent:
        email_status_msg = "An email notification has been dispatched to our support team (ainterviewassistant@gmail.com)."
    else:
        email_status_msg = "Your complaint has been recorded. Email notification is temporarily pending."

    return {
        "message": response_msg,
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "category": ticket.category,
        "subject": ticket.subject,
        "created_at": ticket.created_at.isoformat(),
        "email_dispatched": email_sent,
        "email_status": email_status_msg
    }

@app.get("/api/support/tickets")
def get_user_support_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tickets = db.query(SupportTicket).filter(
        SupportTicket.user_id == current_user.id
    ).order_by(SupportTicket.created_at.desc()).all()

    return [
        {
            "id": t.id,
            "ticket_id": t.ticket_id,
            "category": t.category,
            "subject": t.subject,
            "description": t.description,
            "status": t.status,
            "admin_reply": t.admin_reply,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else None
        }
        for t in tickets
    ]

class SupportChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)

SUPPORT_FAQ_KNOWLEDGE = [
    {
        "keywords": ["otp", "code", "email", "verify", "gmail", "login", "register", "password", "auth"],
        "answer": "For OTP and Login issues:\n1. Check your email inbox and Spam/Junk folder for the 6-digit verification code.\n2. OTP codes are valid for 5 minutes. If expired, request a new OTP.\n3. Make sure you entered your correct registered email address.\n4. If you hit maximum attempts, wait for the cooldown timer before retrying."
    },
    {
        "keywords": ["active resume", "profile", "change resume", "select resume", "default resume"],
        "answer": "Active Resume Management:\n1. Uploaded resumes power all interview, practice, ATS, and recommendation modules.\n2. To switch or view your active resume, go to 'Resume Upload' or the feature setup screens.\n3. Your personal and educational details are managed separately in 'User Profile'."
    },
    {
        "keywords": ["ats", "score", "black screen", "blank screen", "job description", "match", "percentage"],
        "answer": "ATS Scoring & Analysis:\n1. Overall ATS score combines semantic relevance (50%) and canonical technical skill matching (50%).\n2. Enter both the Job Title and Job Description to run the analysis.\n3. If an analysis encounters an issue, click 'Try Again' or 'Edit Job Description' to refine your input without losing your active resume."
    },
    {
        "keywords": ["practice", "aptitude", "mcq", "fundamental", "category", "questions count"],
        "answer": "Practice Mode Categories & Options:\n1. Choose 10, 20, or 30 questions per practice session.\n2. Aptitude: 4-option multiple-choice questions (MCQs) covering quantitative, logical, and verbal reasoning with instant verification.\n3. Fundamental Concepts: Core CS concepts across OS, DBMS, OOP, and Networks.\n4. Resume Based: Tailored questions extracted from your active resume. Both typing and voice input are supported."
    },
    {
        "keywords": ["mock interview", "exit", "fullscreen", "phone", "rejection", "malpractice", "camera", "proctoring"],
        "answer": "Mock Interview Proctoring & Exit Rules:\n1. Fullscreen mode and camera presence are required during Mock Interviews.\n2. Clean Exit: You can safely exit at any time by clicking 'Exit Interview'. Your completed answers will be preserved without malpractice penalties.\n3. Integrity Rules: Sustained absence from camera (>15s), multiple faces (>8s), or phone detection (>10s) will trigger an automated integrity termination."
    },
    {
        "keywords": ["voice", "voice input", "input", "mic", "microphone", "speech", "speech-to-text", "repeating", "words", "audio", "dictation"],
        "answer": "Voice Dictation & Microphone:\n1. Click 'Start Speaking' to dictate your answer using the Web Speech API.\n2. Real-time speech-to-text processes interim transcripts cleanly without repeating words.\n3. Click 'Stop Speaking' when done, and feel free to edit or refine your text before submitting."
    },
    {
        "keywords": ["resume builder", "pdf", "template", "download", "email resume", "build resume"],
        "answer": "Resume Builder Features:\n1. Create professional, single/multi-page A4 resumes using 5 distinct templates (Modern, Simple ATS, Minimal, Fresher, Technical).\n2. Use 'Auto-fill from Active Resume' to quickly populate your contact details and skills.\n3. Click 'Generate & Download PDF Resume' to immediately download your compiled PDF and receive an email copy."
    },
    {
        "keywords": ["ticket", "complaint", "support", "contact", "bug", "issue", "problem", "report"],
        "answer": "Submitting a Support Ticket:\n1. Click the 'Report a Problem' tab in Help & Support.\n2. Fill in your name, registered email, issue category, subject, and description.\n3. A unique Ticket ID will be generated and dispatched to our engineering team."
    }
]

SUPPORT_BOT_MANDATED_REFUSAL = (
    "I'm the AI Interview Assistant Support Bot. I can only help with problems related to this application. "
    "Please describe the issue you're facing in the AI Interview Assistant."
)

SUPPORT_BOT_SYSTEM_PROMPT = (
    "You are the AI Interview Assistant Support Bot. You work EXCLUSIVELY as a Help & Support assistant "
    "for this web application (AI Interview Assistant).\n\n"
    "YOUR SCOPE IS STRICTLY LIMITED TO APPLICATION HELP & TROUBLESHOOTING:\n"
    "- Reporting application problems, errors, or bugs\n"
    "- Login and user registration issues\n"
    "- OTP email verification, expiration, and password recovery\n"
    "- Resume upload, parsing issues, and active resume selection\n"
    "- ATS Analysis calculation, scoring explanations, and job description input\n"
    "- Mock Interview technical sessions, full-screen mode, face detection, phone detection, and exit confirmation\n"
    "- AI One-to-One HR Interview conversational mode and evaluations\n"
    "- Practice Sessions (Aptitude MCQs, CS Concepts, Resume-based questions, voice dictation)\n"
    "- AI Career Recommendations and Step-by-Step Learning Roadmaps\n"
    "- Resume Builder templates, PDF generation, and auto-filling from active resume\n"
    "- Help & Support center navigation, complaint ticket submission, and status guidance\n\n"
    "CRITICAL MANDATORY RULE FOR UNRELATED QUESTIONS:\n"
    "You are NOT a general-purpose AI assistant. For ANY unrelated question—including general programming doubts, "
    "coding requests ('write code for...', 'write a python function...', 'implement binary search'), mathematics, "
    "science, jokes, recipes, weather, trivia, or general technical topics unrelated to operating this application—"
    "you MUST respond EXACTLY with:\n"
    "\"I'm the AI Interview Assistant Support Bot. I can only help with problems related to this application. "
    "Please describe the issue you're facing in the AI Interview Assistant.\"\n\n"
    "TROUBLESHOOTING INSTRUCTIONS FOR APPLICATION ISSUES:\n"
    "- Provide clear, concise, step-by-step troubleshooting instructions.\n"
    "- If the user's issue is ambiguous or lacks details, ask a targeted follow-up question.\n"
    "- If an issue requires engineering inspection, advise the user to submit a ticket via the 'Report a Problem' tab.\n"
    "- Do not invent nonexistent features or claim to perform actions you cannot perform.\n"
    "- Never reveal API keys, database credentials, server configurations, or passwords."
)

@app.post("/api/support/chat")
def support_chat(
    req: SupportChatRequest,
    current_user: User = Depends(get_current_user)
):
    q_text = req.query.strip()
    q_lower = q_text.lower()

    # Pre-filter obvious unrelated queries (coding questions, algorithms, math, general trivia)
    unrelated_patterns = [
        r'\bwrite\s+(?:a\s+)?(?:python|java|c\+\+|javascript|typescript|code|script|function|program|class|algorithm)\b',
        r'\b(?:quicksort|mergesort|binary\s+search|bubble\s+sort|two\s+sum|reverse\s+(?:a\s+)?linked\s+list|leetcode|fibonacci)\b',
        r'\b(?:what\s+is\s+the\s+capital\s+of|who\s+is\s+the\s+president\s+of|tell\s+me\s+a\s+joke|how\s+to\s+cook|recipe\s+for)\b',
        r'^\s*(?:calculate|solve)\s+[\d\+\-\*\/\^\(\)\s\=]+$',
    ]
    if any(re.search(pat, q_lower) for pat in unrelated_patterns):
        return {
            "query": req.query,
            "answer": SUPPORT_BOT_MANDATED_REFUSAL,
            "suggested_action": "Describe an issue you are facing in AI Interview Assistant."
        }

    provider = get_llm_provider()
    try:
        llm_reply = provider.generate_text(
            system_prompt=SUPPORT_BOT_SYSTEM_PROMPT,
            user_prompt=q_text,
            temperature=0.1,
            json_mode=False
        )
        if llm_reply and llm_reply.strip():
            clean_reply = llm_reply.strip()
            if "I'm the AI Interview Assistant Support Bot" in clean_reply or "only help with problems related to this application" in clean_reply:
                clean_reply = SUPPORT_BOT_MANDATED_REFUSAL
            return {
                "query": req.query,
                "answer": clean_reply,
                "suggested_action": "Need engineering support? Click 'Report a Problem' to submit a complaint ticket."
            }
    except Exception as e:
        logger.warning(f"[SupportChat] LLM provider invocation failed, checking FAQ knowledge: {e}")

    # Fallback to FAQ knowledge base
    best_match = None
    max_overlap = 0
    for entry in SUPPORT_FAQ_KNOWLEDGE:
        overlap = sum(1 for kw in entry["keywords"] if kw in q_lower)
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = entry

    if best_match and max_overlap >= 1:
        return {
            "query": req.query,
            "answer": best_match["answer"],
            "suggested_action": "Need further help? Click 'Report a Problem' to submit a support ticket."
        }

    return {
        "query": req.query,
        "answer": "I am the AI Support Assistant. I can assist you with Login/OTP, Resume Upload, ATS Analysis, Practice Sessions, Voice Input, Camera Verification, and AI Tech Bot features.\n\nIf you are experiencing a technical bug or account problem, please click 'Report a Problem' to submit a direct complaint ticket to our support team.",
        "suggested_action": "Click 'Report a Problem' tab to submit an official support ticket."
    }


# 
# Resume Builder Endpoints
# 

class ResumeBuilderGenerateRequest(BaseModel):
    template_id: str = Field("Modern", max_length=50)
    font_family: str = Field("Helvetica", max_length=50)
    primary_color: Optional[str] = "#1e293b"
    title: Optional[str] = "Professional Resume"
    personal_info: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = ""
    skills: Any = Field(default_factory=dict)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Any] = Field(default_factory=list)
    achievements: List[Any] = Field(default_factory=list)
    custom_sections: List[Dict[str, Any]] = Field(default_factory=list)

@app.post("/api/resume-builder/generate")
def generate_built_resume(
    req: ResumeBuilderGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        resume_data_dict = req.dict()
        pdf_bytes = generate_resume_pdf_bytes(
            template_id=req.template_id,
            resume_data=resume_data_dict,
            font_family=req.font_family,
            primary_color=req.primary_color
        )
    except Exception as e:
        logger.error(f"Failed to generate resume PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compile resume PDF: {str(e)}")

    build_dir = os.path.join(os.path.dirname(__file__), "uploads", "built_resumes")
    os.makedirs(build_dir, exist_ok=True)

    cand_name = req.personal_info.get("name") or current_user.name
    filename_prefix = "".join(c for c in cand_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    if not filename_prefix:
        filename_prefix = f"User_{current_user.id}"
    pdf_filename = f"{filename_prefix}_{req.template_id}_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join(build_dir, pdf_filename)

    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Dispatched PDF via email attachment
    email_sent, email_status = send_resume_pdf_email(
        to_email=current_user.email,
        candidate_name=cand_name,
        template_name=req.template_id,
        pdf_bytes=pdf_bytes,
        filename=pdf_filename
    )

    built_resume = BuiltResume(
        user_id=current_user.id,
        title=req.title or f"{req.template_id} Resume",
        template_id=req.template_id,
        font_family=req.font_family,
        resume_data=json.dumps(resume_data_dict),
        pdf_path=pdf_path,
        email_sent=email_sent,
        email_status=email_status
    )
    db.add(built_resume)
    db.commit()
    db.refresh(built_resume)

    return {
        "success": True,
        "message": "Resume PDF generated successfully.",
        "resume_id": built_resume.id,
        "title": built_resume.title,
        "template_id": built_resume.template_id,
        "font_family": built_resume.font_family,
        "download_url": f"/api/resume-builder/download/{built_resume.id}",
        "email_sent": email_sent,
        "email_status": email_status,
        "user_email": current_user.email,
        "created_at": built_resume.created_at.isoformat() if built_resume.created_at else None
    }

@app.get("/api/resume-builder/download/{resume_id}")
def download_built_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    built_resume = db.query(BuiltResume).filter(
        BuiltResume.id == resume_id,
        BuiltResume.user_id == current_user.id
    ).first()
    if not built_resume or not built_resume.pdf_path or not os.path.exists(built_resume.pdf_path):
        raise HTTPException(status_code=404, detail="Resume PDF file not found.")

    filename = os.path.basename(built_resume.pdf_path)
    return FileResponse(
        path=built_resume.pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

@app.get("/api/resume-builder/history")
def get_built_resumes_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resumes = db.query(BuiltResume).filter(
        BuiltResume.user_id == current_user.id
    ).order_by(BuiltResume.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "template_id": r.template_id,
            "font_family": r.font_family,
            "resume_data": json.loads(r.resume_data) if r.resume_data else {},
            "email_sent": r.email_sent,
            "email_status": r.email_status,
            "download_url": f"/api/resume-builder/download/{r.id}",
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in resumes
    ]

@app.post("/api/resume-builder/{resume_id}/resend-email")
def resend_built_resume_email(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    built_resume = db.query(BuiltResume).filter(
        BuiltResume.id == resume_id,
        BuiltResume.user_id == current_user.id
    ).first()
    if not built_resume or not built_resume.pdf_path or not os.path.exists(built_resume.pdf_path):
        raise HTTPException(status_code=404, detail="Resume PDF file not found.")

    with open(built_resume.pdf_path, "rb") as f:
        pdf_bytes = f.read()

    data = json.loads(built_resume.resume_data) if built_resume.resume_data else {}
    cand_name = data.get("personal_info", {}).get("name") or current_user.name
    filename = os.path.basename(built_resume.pdf_path)

    email_sent, email_status = send_resume_pdf_email(
        to_email=current_user.email,
        candidate_name=cand_name,
        template_name=built_resume.template_id,
        pdf_bytes=pdf_bytes,
        filename=filename
    )

    built_resume.email_sent = email_sent
    built_resume.email_status = email_status
    db.commit()


# 
# Topic-Based DSA Problem Solving Endpoints
# 

class UpdateProblemStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(unsolved|attempted|solved)$")
    notes: Optional[str] = None

class ExecuteDsaCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    stdin: Optional[str] = ""

class SubmitDsaCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)

@app.get("/api/dsa/judge0-status")
def get_dsa_judge0_status():
    return check_judge0_health()

@app.get("/api/dsa/topics")
def get_dsa_topics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    topics = db.query(DsaTopic).order_by(DsaTopic.order_index).all()
    user_id = current_user.id if current_user else None

    # Pre-fetch user solved problem IDs if user authenticated
    solved_problem_ids = set()
    if user_id:
        solved_records = db.query(DsaUserProgress.problem_id).filter(
            DsaUserProgress.user_id == user_id,
            DsaUserProgress.status == "solved"
        ).all()
        solved_problem_ids = {r[0] for r in solved_records}

    result = []
    for topic in topics:
        topic_problems = [pt.problem for pt in topic.problems if pt.problem]
        total = len(topic_problems)
        easy = sum(1 for p in topic_problems if p.difficulty.lower() == "easy")
        medium = sum(1 for p in topic_problems if p.difficulty.lower() == "medium")
        hard = sum(1 for p in topic_problems if p.difficulty.lower() == "hard")
        solved = sum(1 for p in topic_problems if p.id in solved_problem_ids)

        result.append({
            "id": topic.id,
            "name": topic.name,
            "slug": topic.slug,
            "description": topic.description,
            "order_index": topic.order_index,
            "total_problems": total,
            "easy_count": easy,
            "medium_count": medium,
            "hard_count": hard,
            "solved_count": solved,
            "completion_percentage": round((solved / total * 100), 1) if total > 0 else 0
        })

    return result

@app.get("/api/dsa/problems")
def get_dsa_problems(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = db.query(DsaProblem)

    # Topic filtering (supports single slug/name or comma-separated list)
    if topic and topic.strip() and topic.strip().lower() != "all":
        topic_tokens = [t.strip().lower() for t in topic.split(",") if t.strip()]
        matched_topics = db.query(DsaTopic).filter(
            (DsaTopic.slug.in_(topic_tokens)) | (DsaTopic.name.in_([t.strip() for t in topic.split(",") if t.strip()]))
        ).all()
        if matched_topics:
            topic_ids = [t.id for t in matched_topics]
            query = query.join(DsaProblemTopic).filter(DsaProblemTopic.topic_id.in_(topic_ids)).distinct()
        else:
            for tok in topic_tokens:
                query = query.filter(DsaProblem.topic_tags_json.ilike(f"%{tok}%"))

    # Difficulty filtering
    if difficulty and difficulty.strip() and difficulty.strip().lower() != "all":
        query = query.filter(DsaProblem.difficulty.ilike(difficulty.strip()))

    # Search query
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (DsaProblem.title.ilike(search_pattern)) | (DsaProblem.description.ilike(search_pattern))
        )

    # Progress mapping for current user
    user_id = current_user.id if current_user else None
    progress_map = {}
    if user_id:
        user_progresses = db.query(DsaUserProgress).filter(DsaUserProgress.user_id == user_id).all()
        progress_map = {up.problem_id: up for up in user_progresses}

    problems = query.order_by(DsaProblem.id.asc()).all()

    filtered_problems = []
    for p in problems:
        prog = progress_map.get(p.id)
        user_status = prog.status if prog else "unsolved"

        if status and status.strip() and status.strip().lower() != "all":
            stat_filter = status.strip().lower()
            if stat_filter == "solved" and user_status != "solved":
                continue
            elif stat_filter == "attempted" and user_status != "attempted":
                continue
            elif stat_filter == "unsolved" and user_status != "unsolved":
                continue

        filtered_problems.append((p, prog, user_status))

    total = len(filtered_problems)
    paginated = filtered_problems[offset : offset + limit]

    problem_list = []
    for p, prog, u_status in paginated:
        try:
            tags = json.loads(p.topic_tags_json) if p.topic_tags_json else []
        except Exception:
            tags = []
        problem_list.append({
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "difficulty": p.difficulty,
            "topic_tags": tags,
            "external_url": p.external_url,
            "supports_execution": p.supports_execution,
            "status": u_status,
            "attempts_count": prog.attempts_count if prog else 0,
            "solved_at": prog.solved_at.isoformat() if prog and prog.solved_at else None,
        })

    return {
        "total": total,
        "problems": problem_list
    }

@app.get("/api/dsa/problems/{problem_ref}")
def get_dsa_problem_detail(
    problem_ref: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if problem_ref.isdigit():
        problem = db.query(DsaProblem).filter(DsaProblem.id == int(problem_ref)).first()
    else:
        problem = db.query(DsaProblem).filter(DsaProblem.slug == problem_ref).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    examples = json.loads(problem.examples_json) if problem.examples_json else []
    constraints = json.loads(problem.constraints_json) if problem.constraints_json else []
    topic_tags = json.loads(problem.topic_tags_json) if problem.topic_tags_json else []
    starter_code = json.loads(problem.starter_code_json) if problem.starter_code_json else {}
    all_test_cases = json.loads(problem.test_cases_json) if problem.test_cases_json else []
    
    sample_cases = [tc for tc in all_test_cases if tc.get("is_sample")]
    if not sample_cases and all_test_cases:
        sample_cases = all_test_cases[:2]

    user_prog_data = None
    latest_sub_data = None
    if current_user:
        up = db.query(DsaUserProgress).filter(
            DsaUserProgress.user_id == current_user.id,
            DsaUserProgress.problem_id == problem.id
        ).first()
        if up:
            user_prog_data = {
                "status": up.status,
                "attempts_count": up.attempts_count,
                "solved_at": up.solved_at.isoformat() if up.solved_at else None,
                "notes": up.notes
            }

        latest_sub = db.query(DsaSubmission).filter(
            DsaSubmission.user_id == current_user.id,
            DsaSubmission.problem_id == problem.id
        ).order_by(DsaSubmission.submitted_at.desc()).first()
        if latest_sub:
            latest_sub_data = {
                "id": latest_sub.id,
                "language": latest_sub.language,
                "code": latest_sub.code,
                "status": latest_sub.status,
                "test_cases_passed": latest_sub.test_cases_passed,
                "total_test_cases": latest_sub.total_test_cases,
                "submitted_at": latest_sub.submitted_at.isoformat()
            }

    return {
        "id": problem.id,
        "slug": problem.slug,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "description": problem.description,
        "examples": examples,
        "constraints": constraints,
        "topic_tags": topic_tags,
        "external_url": problem.external_url,
        "supports_execution": problem.supports_execution,
        "starter_code": starter_code,
        "sample_test_cases": sample_cases,
        "user_progress": user_prog_data or {"status": "unsolved", "attempts_count": 0, "solved_at": None, "notes": None},
        "latest_submission": latest_sub_data
    }

@app.post("/api/dsa/problems/{problem_ref}/status")
def update_dsa_problem_status(
    problem_ref: str,
    req: UpdateProblemStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if problem_ref.isdigit():
        problem = db.query(DsaProblem).filter(DsaProblem.id == int(problem_ref)).first()
    else:
        problem = db.query(DsaProblem).filter(DsaProblem.slug == problem_ref).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    progress = db.query(DsaUserProgress).filter(
        DsaUserProgress.user_id == current_user.id,
        DsaUserProgress.problem_id == problem.id
    ).first()

    if not progress:
        progress = DsaUserProgress(
            user_id=current_user.id,
            problem_id=problem.id,
            status=req.status,
            attempts_count=1 if req.status in ["attempted", "solved"] else 0,
            solved_at=datetime.datetime.utcnow() if req.status == "solved" else None,
            notes=req.notes
        )
        db.add(progress)
    else:
        progress.status = req.status
        if req.status == "solved" and not progress.solved_at:
            progress.solved_at = datetime.datetime.utcnow()
        elif req.status == "unsolved":
            progress.solved_at = None
        if req.notes is not None:
            progress.notes = req.notes
        progress.last_attempted_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(progress)

    return {
        "problem_id": problem.id,
        "status": progress.status,
        "solved_at": progress.solved_at.isoformat() if progress.solved_at else None,
        "attempts_count": progress.attempts_count,
        "notes": progress.notes
    }

@app.get("/api/dsa/progress")
def get_dsa_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_problems = db.query(DsaProblem).count()
    
    user_records = db.query(DsaUserProgress).filter(DsaUserProgress.user_id == current_user.id).all()
    solved_records = [r for r in user_records if r.status == "solved"]
    attempted_records = [r for r in user_records if r.status == "attempted"]

    solved_problem_ids = {r.problem_id for r in solved_records}
    total_solved = len(solved_records)
    total_attempted = len(attempted_records)

    difficulties = ["Easy", "Medium", "Hard"]
    by_difficulty = {}
    for diff in difficulties:
        tot = db.query(DsaProblem).filter(DsaProblem.difficulty.ilike(diff)).count()
        sol = db.query(DsaProblem).join(DsaUserProgress).filter(
            DsaUserProgress.user_id == current_user.id,
            DsaUserProgress.status == "solved",
            DsaProblem.difficulty.ilike(diff)
        ).count()
        by_difficulty[diff] = {
            "total": tot,
            "solved": sol,
            "percentage": round((sol / tot * 100), 1) if tot > 0 else 0
        }

    topics = db.query(DsaTopic).order_by(DsaTopic.order_index).all()
    by_topic = []
    for topic in topics:
        topic_problems = [pt.problem for pt in topic.problems if pt.problem]
        t_total = len(topic_problems)
        t_solved = sum(1 for p in topic_problems if p.id in solved_problem_ids)
        by_topic.append({
            "topic_id": topic.id,
            "name": topic.name,
            "slug": topic.slug,
            "total": t_total,
            "solved": t_solved,
            "percentage": round((t_solved / t_total * 100), 1) if t_total > 0 else 0
        })

    recent_subs = db.query(DsaSubmission).filter(
        DsaSubmission.user_id == current_user.id
    ).order_by(DsaSubmission.submitted_at.desc()).limit(10).all()

    submissions_list = []
    for s in recent_subs:
        submissions_list.append({
            "id": s.id,
            "problem_id": s.problem_id,
            "problem_title": s.problem.title if s.problem else "Unknown",
            "language": s.language,
            "status": s.status,
            "test_cases_passed": s.test_cases_passed,
            "total_test_cases": s.total_test_cases,
            "execution_time_ms": s.execution_time_ms,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None
        })

    return {
        "total_problems": total_problems,
        "total_solved": total_solved,
        "total_attempted": total_attempted,
        "overall_percentage": round((total_solved / total_problems * 100), 1) if total_problems > 0 else 0,
        "by_difficulty": by_difficulty,
        "by_topic": by_topic,
        "recent_submissions": submissions_list
    }

@app.post("/api/dsa/problems/{problem_ref}/execute")
def execute_dsa_code(
    problem_ref: str,
    req: ExecuteDsaCodeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if problem_ref.isdigit():
        problem = db.query(DsaProblem).filter(DsaProblem.id == int(problem_ref)).first()
    else:
        problem = db.query(DsaProblem).filter(DsaProblem.slug == problem_ref).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    res = submit_code_judge0(
        source_code=req.code,
        language=req.language,
        stdin=req.stdin or ""
    )
    return res

@app.post("/api/dsa/problems/{problem_ref}/submit")
def submit_dsa_code(
    problem_ref: str,
    req: SubmitDsaCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if problem_ref.isdigit():
        problem = db.query(DsaProblem).filter(DsaProblem.id == int(problem_ref)).first()
    else:
        problem = db.query(DsaProblem).filter(DsaProblem.slug == problem_ref).first()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    test_cases = json.loads(problem.test_cases_json) if problem.test_cases_json else []
    eval_res = evaluate_problem_submission(
        source_code=req.code,
        language=req.language,
        test_cases=test_cases
    )

    verdict = eval_res.get("verdict", "Execution Error")
    passed = eval_res.get("passed", False)
    passed_count = eval_res.get("passed_count", 0)
    total_count = eval_res.get("total_count", len(test_cases))

    sub_status = verdict
    first_res = eval_res.get("results", [{}])[0] if eval_res.get("results") else {}
    
    submission = DsaSubmission(
        user_id=current_user.id,
        problem_id=problem.id,
        language=req.language.lower(),
        code=req.code,
        status=sub_status,
        test_cases_passed=passed_count,
        total_test_cases=total_count,
        execution_time_ms=first_res.get("execution_time_ms"),
        memory_kb=first_res.get("memory_kb"),
        stdout=first_res.get("stdout"),
        stderr=first_res.get("stderr") or eval_res.get("error_message")
    )
    db.add(submission)

    progress = db.query(DsaUserProgress).filter(
        DsaUserProgress.user_id == current_user.id,
        DsaUserProgress.problem_id == problem.id
    ).first()

    if not progress:
        progress = DsaUserProgress(
            user_id=current_user.id,
            problem_id=problem.id,
            status="solved" if passed else "attempted",
            attempts_count=1,
            solved_at=datetime.datetime.utcnow() if passed else None,
            last_attempted_at=datetime.datetime.utcnow()
        )
        db.add(progress)
    else:
        progress.attempts_count = (progress.attempts_count or 0) + 1
        progress.last_attempted_at = datetime.datetime.utcnow()
        if passed:
            progress.status = "solved"
            if not progress.solved_at:
                progress.solved_at = datetime.datetime.utcnow()
        elif progress.status != "solved":
            progress.status = "attempted"

    db.commit()
    db.refresh(progress)

    return {
        "verdict": verdict,
        "passed": passed,
        "passed_count": passed_count,
        "total_count": total_count,
        "user_status": progress.status,
        "results": eval_res.get("results", []),
        "error_message": eval_res.get("error_message"),
        "submission_id": submission.id
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=port, reload=False)

