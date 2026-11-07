import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from backend directory and project root before reading any env vars
current_dir = Path(__file__).resolve().parent
backend_env = current_dir / ".env"
root_env = current_dir.parent / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
if root_env.exists():
    load_dotenv(root_env)
load_dotenv()

import random
import smtplib
import ssl
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from email.message import EmailMessage

logger = logging.getLogger(__name__)

# Configuration
APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super_secret_production_ready_jwt_key_2026")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 days

OTP_EXPIRE_MINUTES = 5          # 5-minute expiry
MAX_OTP_ATTEMPTS = 3            # Max 3 verification attempts
OTP_COOLDOWN_SECONDS = 60       # 60s cooldown between resends

# Email SMTP Config
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
# Handle potential spaces or quotes in Google App Passwords
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "").strip("\"'")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "").strip() or SMTP_USERNAME or "noreply@ai-assistant.local"


def get_smtp_status() -> dict:
    """Safe diagnostic status function that never exposes secrets or passwords."""
    return {
        "smtp_configured": bool(SMTP_USERNAME and SMTP_PASSWORD),
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "smtp_username_configured": bool(SMTP_USERNAME),
        "smtp_password_configured": bool(SMTP_PASSWORD),
        "sender_email": SENDER_EMAIL
    }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        password_bytes = plain_password.encode('utf-8') if isinstance(plain_password, str) else plain_password
        hash_str = hashed_password.strip() if isinstance(hashed_password, str) else hashed_password.decode('utf-8').strip()
        hash_bytes = hash_str.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt salted password hash."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed_pwd = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_pwd.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT access token signature and expiration."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_otp() -> str:
    """Generate cryptographically secure 6-digit numeric OTP."""
    return f"{random.SystemRandom().randint(100000, 999999)}"


def send_otp_email(to_email: str, otp: str) -> Tuple[bool, str]:
    """
    Send verification OTP email via Gmail/SMTP with STARTTLS on port 587.
    Returns (success: bool, status_message: str).
    """
    msg = EmailMessage()
    msg.set_content(
        f"Hello,\n\n"
        f"Your verification OTP code for AI Interview Assistant is: {otp}\n\n"
        f"This code will expire in {OTP_EXPIRE_MINUTES} minutes. If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nAI Interview Assistant Team"
    )
    msg["Subject"] = "AI Interview Assistant - Your Verification OTP"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        if APP_ENV == "production":
            logger.error("SMTP credentials not configured in production. Cannot send OTP.")
            return False, "SMTP credentials are not configured on the server."
        # Development / Test mock email fallback
        print(f"\n{'='*50}\n[DEV MOCK EMAIL SENT]\nTo: {to_email}\nSubject: {msg['Subject']}\nOTP: {otp}\n{'='*50}\n")
        return True, "Dev mock email sent (SMTP unconfigured)."

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10.0)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Verification email successfully sent to {to_email} via Gmail SMTP.")
        return True, "Verification email sent successfully."
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            f"Gmail SMTP Authentication Failed: {e}. "
            f"Please ensure 2-Step Verification is active on the sender account and a 16-character Google App Password (not standard account password) is set in SMTP_PASSWORD."
        )
        if APP_ENV == "development":
            print(f"\n{'='*50}\n[DEV MOCK EMAIL SENT FALLBACK]\nTo: {to_email}\nSubject: {msg['Subject']}\nOTP: {otp}\n{'='*50}\n")
            return True, "Gmail authentication failed; fell back to development mock output."
        return False, "Gmail SMTP authentication failed. Please verify the Google App Password on the server."
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {type(e).__name__}: {e}")
        if APP_ENV == "development":
            print(f"\n{'='*50}\n[DEV MOCK EMAIL SENT FALLBACK]\nTo: {to_email}\nSubject: {msg['Subject']}\nOTP: {otp}\n{'='*50}\n")
            return True, f"SMTP delivery failed ({type(e).__name__}); fell back to development mock output."
        return False, f"Failed to send email via SMTP: {type(e).__name__}"


SUPPORT_RECEIVER_EMAIL = os.getenv("SUPPORT_RECEIVER_EMAIL", "ainterviewassistant@gmail.com").strip() or "ainterviewassistant@gmail.com"


def send_support_ticket_email(ticket_data: dict) -> Tuple[bool, str]:
    """
    Send support complaint notification email to ainterviewassistant@gmail.com.
    Sets user's email as Reply-To so support team can directly reply.
    Returns (success: bool, status_message: str).
    """
    support_target_email = SUPPORT_RECEIVER_EMAIL or "ainterviewassistant@gmail.com"
    ticket_id = ticket_data.get("ticket_id", "UNKNOWN")
    user_name = ticket_data.get("name", "Unknown User")
    user_email = ticket_data.get("email", "Unknown Email")
    category = ticket_data.get("category", "General")
    subject = ticket_data.get("subject", "No Subject")
    description = ticket_data.get("description", "")
    created_at = ticket_data.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    msg = EmailMessage()
    msg.set_content(
        f"AI Interview Assistant — Support Complaint Report\n"
        f"{'='*60}\n"
        f"Ticket ID:              {ticket_id}\n"
        f"Submission Date/Time:   {created_at}\n"
        f"User Full Name:         {user_name}\n"
        f"User Account Email:     {user_email}\n"
        f"Issue Category:         {category}\n"
        f"Subject:                {subject}\n"
        f"{'='*60}\n\n"
        f"Detailed Description of Problem:\n"
        f"{description}\n\n"
        f"{'='*60}\n"
        f"Reply-To: {user_email}\n"
        f"(Direct replies to this email will be delivered to {user_email})\n"
    )
    msg["Subject"] = f"New Support Complaint – {ticket_id}"
    msg["From"] = SENDER_EMAIL or SMTP_USERNAME or "ainterviewassistant@gmail.com"
    msg["To"] = support_target_email
    if user_email and "@" in user_email:
        msg["Reply-To"] = user_email

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(f"SMTP credentials not configured on the server. Support ticket {ticket_id} logged to DB, but email dispatch to {support_target_email} was skipped.")
        return False, "SMTP credentials are not configured on the server. Ticket saved in database, but email notification was not sent."

    server = None
    try:
        ssl_context = ssl.create_default_context()
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=ssl_context, timeout=15.0)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15.0)
            server.ehlo()
            server.starttls(context=ssl_context)
            server.ehlo()

        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        logger.info(f"Support complaint email [{ticket_id}] successfully delivered to {support_target_email} with Reply-To={user_email}.")
        return True, f"Support notification email delivered to {support_target_email}."
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Gmail SMTP Authentication Failed for user {SMTP_USERNAME}: {e}. Ensure 2-Step Verification is enabled and a 16-character Google App Password is used.")
        return False, "Your complaint has been recorded. Email notification is temporarily pending (authentication error)."
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"Gmail SMTP Server Disconnected for user {SMTP_USERNAME}: {e}. Connection closed by Gmail server after authentication attempt.")
        return False, "Your complaint has been recorded. Email notification is temporarily pending."
    except Exception as e:
        logger.error(f"Failed to deliver support ticket email: {type(e).__name__}: {e}")
        return False, "Your complaint has been recorded. Email notification is temporarily pending."
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass


def send_resume_pdf_email(
    to_email: str,
    candidate_name: str,
    pdf_bytes: bytes,
    filename: str = "Resume.pdf",
    template_name: str = "Simple",
    **kwargs
) -> Tuple[bool, str]:
    """
    Email generated resume PDF as attachment to the authenticated user's account email.
    """
    if not to_email:
        return False, "Recipient email address is required."

    msg = EmailMessage()
    msg.set_content(
        f"Hello {candidate_name or 'Candidate'},\n\n"
        f"Your professional resume ({template_name} template) generated with AI Interview Assistant Resume Builder is attached to this email.\n\n"
        f"Filename: {filename}\n"
        f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Best regards,\nAI Interview Assistant Team"
    )
    msg["Subject"] = f"Your Generated Resume — {filename}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename
    )

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        if APP_ENV == "production":
            return False, "SMTP credentials are not configured on the server."
        print(f"\n{'='*55}\n[DEV RESUME PDF EMAIL MOCK]\nTo: {to_email}\nSubject: {msg['Subject']}\nAttachment: {filename} ({len(pdf_bytes)} bytes)\n{'='*55}\n")
        return True, "Dev mock email logged (SMTP unconfigured)."

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=12.0)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Resume PDF email successfully delivered to {to_email}.")
        return True, "Resume email sent successfully."
    except Exception as e:
        logger.error(f"Failed to email resume PDF to {to_email}: {e}")
        if APP_ENV == "development":
            print(f"\n{'='*55}\n[DEV RESUME PDF EMAIL FALLBACK]\nTo: {to_email}\nAttachment: {filename}\n{'='*55}\n")
            return True, f"Mock resume delivery recorded: {e}"
        return False, f"Failed to send email: {e}"


def send_malpractice_rejection_email(session_data: dict) -> tuple[bool, str]:
    """
    Sends an automated notification to the candidate when a Mock Interview session
    is terminated due to an integrity/malpractice violation.
    Neutral, factual, professional tone without unsupported accusations.
    """
    candidate_name = session_data.get("name", "Candidate")
    candidate_email = session_data.get("email", "").strip()
    session_id = session_data.get("session_id", "N/A")
    reason = session_data.get("reason", "Interview integrity requirements were not satisfied.")
    questions_completed = session_data.get("questions_completed", 0)
    total_questions = session_data.get("total_questions", 30)
    timestamp = session_data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    if not candidate_email:
        return False, "Candidate email is missing."

    msg = EmailMessage()
    msg.set_content(
        f"Dear {candidate_name},\n\n"
        f"Your mock interview session (ID: {session_id}) has been terminated because the interview integrity requirements were not satisfied.\n\n"
        f"{'='*55}\n"
        f"SESSION DETAILS\n"
        f"{'='*55}\n"
        f"Candidate Name:       {candidate_name}\n"
        f"Candidate Email:      {candidate_email}\n"
        f"Session ID:           {session_id}\n"
        f"Interview Status:     REJECTED_INTEGRITY_VIOLATION\n"
        f"Date & Time:          {timestamp}\n"
        f"Questions Completed:  {questions_completed} / {total_questions}\n"
        f"Reason for Rejection: {reason}\n"
        f"{'='*55}\n\n"
        f"In accordance with our interview integrity policy, mock interview sessions require continuous, unhindered single-candidate face presence in the camera frame.\n\n"
        f"You may start a new mock interview session when you are ready from your dashboard.\n\n"
        f"Sincerely,\n"
        f"AI Interview Assistant Evaluation System"
    )
    msg["Subject"] = "Mock Interview Rejected — Interview Integrity Violation"
    msg["From"] = SENDER_EMAIL
    msg["To"] = candidate_email

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        if APP_ENV == "production":
            logger.error("SMTP credentials unconfigured in production. Cannot send rejection email.")
            return False, "SMTP credentials unconfigured."
        print(f"\n{'='*55}\n[DEV INTEGRITY REJECTION EMAIL MOCK]\nTo: {candidate_email}\nSubject: {msg['Subject']}\nSession: {session_id}\nReason: {reason}\n{'='*55}\n")
        return True, "Dev mock rejection email logged."

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10.0)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Integrity rejection email for session [{session_id}] sent to {candidate_email}.")
        return True, "Rejection email delivered successfully."
    except Exception as e:
        logger.error(f"Failed to deliver integrity rejection email: {type(e).__name__}: {e}")
        if APP_ENV == "development":
            print(f"\n{'='*55}\n[DEV INTEGRITY EMAIL FALLBACK]\nTo: {candidate_email}\nSubject: {msg['Subject']}\nSession: {session_id}\nReason: {reason}\n{'='*55}\n")
            return True, "SMTP failed; dev fallback logged."
        return False, f"Failed to deliver rejection email: {type(e).__name__}"


