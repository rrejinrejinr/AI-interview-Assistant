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

import base64
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

# ---------------------------------------------------------------------------
# Resend API Configuration (primary delivery path)
# ---------------------------------------------------------------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()

# ---------------------------------------------------------------------------
# Legacy Email / SMTP Configuration (fallback when Resend is not configured)
# ---------------------------------------------------------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
# Handle potential spaces or quotes in Google App Passwords
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "").strip("\"'")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "").strip() or SMTP_USERNAME or "noreply@ai-assistant.local"

SUPPORT_RECEIVER_EMAIL = os.getenv("SUPPORT_RECEIVER_EMAIL", "ainterviewassistant@gmail.com").strip() or "ainterviewassistant@gmail.com"


# ---------------------------------------------------------------------------
# Resend helper — lazy import so the app still loads if resend is absent
# ---------------------------------------------------------------------------

def _resend_configured() -> bool:
    """Return True when RESEND_API_KEY and RESEND_FROM_EMAIL are both set."""
    return bool(RESEND_API_KEY and RESEND_FROM_EMAIL)


def _send_via_resend(
    to_email: str,
    subject: str,
    text_body: str,
    reply_to: Optional[str] = None,
    attachments: Optional[list] = None,
) -> Tuple[bool, str]:
    """
    Deliver a plain-text email through the Resend API.

    Args:
        to_email:    Recipient address.
        subject:     Email subject line.
        text_body:   Plain-text body content.
        reply_to:    Optional Reply-To address.
        attachments: Optional list of Resend Attachment dicts
                     (keys: 'content' (List[int]|str), 'filename', 'content_type').

    Returns:
        (success, status_message)
    """
    try:
        import resend as _resend_sdk
    except ImportError:
        logger.error(
            "resend package is not installed. Run: pip install resend  "
            "or add resend>=2.52.0 to backend/requirements.txt"
        )
        return False, "resend package is not installed on the server."

    _resend_sdk.api_key = RESEND_API_KEY

    params: dict = {
        "from": RESEND_FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "text": text_body,
    }
    if reply_to:
        params["reply_to"] = reply_to
    if attachments:
        params["attachments"] = attachments

    try:
        response = _resend_sdk.Emails.send(params)
        email_id = getattr(response, "id", None) or (response.get("id") if isinstance(response, dict) else None)
        logger.info(
            "Resend delivery succeeded: to=%s subject=%r id=%s",
            to_email, subject, email_id,
        )
        return True, "Email sent successfully via Resend."
    except Exception as exc:
        # Log the exception type/message but never the API key or OTP value
        logger.error(
            "Resend delivery failed: to=%s subject=%r error_type=%s error=%s",
            to_email, subject, type(exc).__name__, exc,
        )
        return False, f"Resend delivery error: {type(exc).__name__}"


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def get_email_delivery_status() -> dict:
    """
    Safe diagnostic status that never exposes secrets.
    Reports which delivery backend is active.
    """
    return {
        "resend_configured": _resend_configured(),
        "resend_from_email": RESEND_FROM_EMAIL if RESEND_FROM_EMAIL else None,
        "smtp_configured": bool(SMTP_USERNAME and SMTP_PASSWORD),
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "smtp_username_configured": bool(SMTP_USERNAME),
        "smtp_password_configured": bool(SMTP_PASSWORD),
        "sender_email": SENDER_EMAIL,
        "active_backend": "resend" if _resend_configured() else ("smtp" if SMTP_USERNAME and SMTP_PASSWORD else "none"),
    }


# Keep the old name as an alias so existing imports and the /api/auth/smtp-status
# endpoint in app_fastapi.py continue to work without modification.
def get_smtp_status() -> dict:
    """Backward-compatible alias for get_email_delivery_status()."""
    return get_email_delivery_status()


# ---------------------------------------------------------------------------
# JWT / password helpers (unchanged)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SMTP fallback helper (used when Resend is not configured)
# ---------------------------------------------------------------------------

def _send_via_smtp(msg: EmailMessage) -> Tuple[bool, str]:
    """
    Attempt SMTP delivery using the configured SMTP_* env vars.
    Returns (success, status_message).
    """
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
        logger.info("SMTP delivery succeeded: to=%s subject=%r", msg["To"], msg["Subject"])
        return True, "Email sent successfully via SMTP."
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "SMTP authentication failed (username=%s): %s. "
            "Ensure 2-Step Verification is enabled and a 16-character Google App Password is used.",
            SMTP_USERNAME, exc,
        )
        return False, "SMTP authentication failed. Please verify the Google App Password on the server."
    except smtplib.SMTPServerDisconnected as exc:
        logger.error("SMTP server disconnected (server=%s): %s", SMTP_SERVER, exc)
        return False, "SMTP server disconnected unexpectedly."
    except Exception as exc:
        logger.error("SMTP delivery failed: %s: %s", type(exc).__name__, exc)
        return False, f"SMTP delivery error: {type(exc).__name__}"
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Public email functions
# ---------------------------------------------------------------------------

def send_otp_email(to_email: str, otp: str) -> Tuple[bool, str]:
    """
    Send verification OTP email.

    Delivery priority:
      1. Resend API (when RESEND_API_KEY + RESEND_FROM_EMAIL are set)
      2. SMTP (when SMTP_USERNAME + SMTP_PASSWORD are set)
      3. Dev-mode console mock (non-production only)

    Returns (success: bool, status_message: str).
    OTP value is never logged.
    """
    subject = "AI Interview Assistant - Your Verification OTP"
    body = (
        f"Hello,\n\n"
        f"Your verification OTP code for AI Interview Assistant is: {otp}\n\n"
        f"This code will expire in {OTP_EXPIRE_MINUTES} minutes. "
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nAI Interview Assistant Team"
    )

    # --- Primary: Resend API ---
    if _resend_configured():
        return _send_via_resend(to_email=to_email, subject=subject, text_body=body)

    # --- Fallback: SMTP ---
    if SMTP_USERNAME and SMTP_PASSWORD:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        success, status = _send_via_smtp(msg)
        if success:
            return True, "Verification email sent successfully."
        if APP_ENV == "development":
            print(
                f"\n{'='*50}\n[DEV MOCK EMAIL SENT FALLBACK]\n"
                f"To: {to_email}\nSubject: {subject}\n"
                f"[OTP hidden — check DB or console]\n{'='*50}\n"
            )
            return True, f"SMTP delivery failed; fell back to development mock output."
        return False, status

    # --- Dev-mode mock (no credentials configured) ---
    if APP_ENV == "production":
        logger.error(
            "No email delivery backend configured in production. "
            "Set RESEND_API_KEY + RESEND_FROM_EMAIL (or SMTP_USERNAME + SMTP_PASSWORD)."
        )
        return False, "Email delivery is not configured on the server."

    # Development / test: print mock (OTP shown only in non-prod console)
    print(
        f"\n{'='*50}\n[DEV MOCK EMAIL SENT]\n"
        f"To: {to_email}\nSubject: {subject}\nOTP: {otp}\n{'='*50}\n"
    )
    return True, "Dev mock email sent (no delivery backend configured)."


def send_support_ticket_email(ticket_data: dict) -> Tuple[bool, str]:
    """
    Send support complaint notification email to the support inbox.
    Sets the user's email as Reply-To so the support team can reply directly.

    Delivery priority: Resend → SMTP → error.
    Returns (success: bool, status_message: str).
    """
    support_target_email = SUPPORT_RECEIVER_EMAIL or "ainterviewassistant@gmail.com"
    ticket_id   = ticket_data.get("ticket_id", "UNKNOWN")
    user_name   = ticket_data.get("name", "Unknown User")
    user_email  = ticket_data.get("email", "Unknown Email")
    category    = ticket_data.get("category", "General")
    subject_txt = ticket_data.get("subject", "No Subject")
    description = ticket_data.get("description", "")
    created_at  = ticket_data.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    email_subject = f"New Support Complaint \u2013 {ticket_id}"
    body = (
        f"AI Interview Assistant \u2014 Support Complaint Report\n"
        f"{'='*60}\n"
        f"Ticket ID:              {ticket_id}\n"
        f"Submission Date/Time:   {created_at}\n"
        f"User Full Name:         {user_name}\n"
        f"User Account Email:     {user_email}\n"
        f"Issue Category:         {category}\n"
        f"Subject:                {subject_txt}\n"
        f"{'='*60}\n\n"
        f"Detailed Description of Problem:\n"
        f"{description}\n\n"
        f"{'='*60}\n"
        f"Reply-To: {user_email}\n"
        f"(Direct replies to this email will be delivered to {user_email})\n"
    )
    reply_to = user_email if user_email and "@" in user_email else None

    # --- Primary: Resend API ---
    if _resend_configured():
        success, msg = _send_via_resend(
            to_email=support_target_email,
            subject=email_subject,
            text_body=body,
            reply_to=reply_to,
        )
        if success:
            logger.info(
                "Support complaint email [%s] delivered to %s via Resend (Reply-To=%s).",
                ticket_id, support_target_email, reply_to,
            )
            return True, f"Support notification email delivered to {support_target_email}."
        return False, "Your complaint has been recorded. Email notification is temporarily pending."

    # --- Fallback: SMTP ---
    if SMTP_USERNAME and SMTP_PASSWORD:
        msg_obj = EmailMessage()
        msg_obj.set_content(body)
        msg_obj["Subject"] = email_subject
        msg_obj["From"] = SENDER_EMAIL or SMTP_USERNAME or "ainterviewassistant@gmail.com"
        msg_obj["To"] = support_target_email
        if reply_to:
            msg_obj["Reply-To"] = reply_to
        success, smtp_msg = _send_via_smtp(msg_obj)
        if success:
            logger.info(
                "Support complaint email [%s] delivered to %s via SMTP (Reply-To=%s).",
                ticket_id, support_target_email, reply_to,
            )
            return True, f"Support notification email delivered to {support_target_email}."
        return False, "Your complaint has been recorded. Email notification is temporarily pending."

    # --- No backend configured ---
    logger.warning(
        "No email delivery backend configured. Support ticket %s logged to DB, "
        "but email to %s was skipped.",
        ticket_id, support_target_email,
    )
    return False, (
        "No email delivery backend is configured on the server. "
        "Ticket saved in database, but email notification was not sent."
    )


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

    Delivery priority: Resend → SMTP → dev-mode mock.
    Returns (success: bool, status_message: str).
    """
    if not to_email:
        return False, "Recipient email address is required."

    email_subject = f"Your Generated Resume \u2014 {filename}"
    body = (
        f"Hello {candidate_name or 'Candidate'},\n\n"
        f"Your professional resume ({template_name} template) generated with "
        f"AI Interview Assistant Resume Builder is attached to this email.\n\n"
        f"Filename: {filename}\n"
        f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Best regards,\nAI Interview Assistant Team"
    )

    # --- Primary: Resend API (with PDF attachment) ---
    if _resend_configured():
        # Resend expects attachment content as a list of integers (byte values)
        pdf_int_list = list(pdf_bytes)
        attachment = {
            "content": pdf_int_list,
            "filename": filename,
            "content_type": "application/pdf",
        }
        success, status = _send_via_resend(
            to_email=to_email,
            subject=email_subject,
            text_body=body,
            attachments=[attachment],
        )
        if success:
            logger.info("Resume PDF email delivered to %s via Resend (file=%s).", to_email, filename)
            return True, "Resume email sent successfully."
        if APP_ENV == "development":
            print(
                f"\n{'='*55}\n[DEV RESUME PDF EMAIL FALLBACK — Resend error]\n"
                f"To: {to_email}\nAttachment: {filename} ({len(pdf_bytes)} bytes)\n{'='*55}\n"
            )
            return True, f"Resend error; dev mock recorded: {status}"
        return False, status

    # --- Fallback: SMTP (with PDF attachment) ---
    if SMTP_USERNAME and SMTP_PASSWORD:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = email_subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)
        success, smtp_status = _send_via_smtp(msg)
        if success:
            logger.info("Resume PDF email delivered to %s via SMTP (file=%s).", to_email, filename)
            return True, "Resume email sent successfully."
        if APP_ENV == "development":
            print(
                f"\n{'='*55}\n[DEV RESUME PDF EMAIL FALLBACK — SMTP error]\n"
                f"To: {to_email}\nAttachment: {filename}\n{'='*55}\n"
            )
            return True, f"SMTP error; dev mock recorded: {smtp_status}"
        return False, f"Failed to send email: {smtp_status}"

    # --- Dev-mode mock (no credentials configured) ---
    if APP_ENV == "production":
        return False, "Email delivery is not configured on the server."
    print(
        f"\n{'='*55}\n[DEV RESUME PDF EMAIL MOCK]\n"
        f"To: {to_email}\nSubject: {email_subject}\n"
        f"Attachment: {filename} ({len(pdf_bytes)} bytes)\n{'='*55}\n"
    )
    return True, "Dev mock email logged (no delivery backend configured)."


def send_malpractice_rejection_email(session_data: dict) -> Tuple[bool, str]:
    """
    Send an automated notification to the candidate when a Mock Interview session
    is terminated due to an integrity/malpractice violation.
    Neutral, factual, professional tone without unsupported accusations.

    Delivery priority: Resend → SMTP → dev-mode mock.
    Returns (success: bool, status_message: str).
    """
    candidate_name   = session_data.get("name", "Candidate")
    candidate_email  = session_data.get("email", "").strip()
    session_id       = session_data.get("session_id", "N/A")
    reason           = session_data.get("reason", "Interview integrity requirements were not satisfied.")
    questions_completed = session_data.get("questions_completed", 0)
    total_questions  = session_data.get("total_questions", 30)
    timestamp        = session_data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    if not candidate_email:
        return False, "Candidate email is missing."

    email_subject = "Mock Interview Rejected \u2014 Interview Integrity Violation"
    body = (
        f"Dear {candidate_name},\n\n"
        f"Your mock interview session (ID: {session_id}) has been terminated "
        f"because the interview integrity requirements were not satisfied.\n\n"
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
        f"In accordance with our interview integrity policy, mock interview sessions "
        f"require continuous, unhindered single-candidate face presence in the camera frame.\n\n"
        f"You may start a new mock interview session when you are ready from your dashboard.\n\n"
        f"Sincerely,\n"
        f"AI Interview Assistant Evaluation System"
    )

    # --- Primary: Resend API ---
    if _resend_configured():
        success, status = _send_via_resend(
            to_email=candidate_email,
            subject=email_subject,
            text_body=body,
        )
        if success:
            logger.info(
                "Integrity rejection email for session [%s] delivered to %s via Resend.",
                session_id, candidate_email,
            )
            return True, "Rejection email delivered successfully."
        if APP_ENV == "development":
            print(
                f"\n{'='*55}\n[DEV INTEGRITY REJECTION EMAIL FALLBACK — Resend error]\n"
                f"To: {candidate_email}\nSession: {session_id}\n{'='*55}\n"
            )
            return True, f"Resend error; dev fallback logged: {status}"
        return False, f"Failed to deliver rejection email: {status}"

    # --- Fallback: SMTP ---
    if SMTP_USERNAME and SMTP_PASSWORD:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = email_subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = candidate_email
        success, smtp_status = _send_via_smtp(msg)
        if success:
            logger.info(
                "Integrity rejection email for session [%s] delivered to %s via SMTP.",
                session_id, candidate_email,
            )
            return True, "Rejection email delivered successfully."
        if APP_ENV == "development":
            print(
                f"\n{'='*55}\n[DEV INTEGRITY EMAIL FALLBACK — SMTP error]\n"
                f"To: {candidate_email}\nSession: {session_id}\n{'='*55}\n"
            )
            return True, "SMTP failed; dev fallback logged."
        return False, f"Failed to deliver rejection email: {smtp_status}"

    # --- Dev-mode mock (no credentials configured) ---
    if APP_ENV == "production":
        logger.error("No email delivery backend configured in production. Cannot send rejection email.")
        return False, "Email delivery is not configured on the server."
    print(
        f"\n{'='*55}\n[DEV INTEGRITY REJECTION EMAIL MOCK]\n"
        f"To: {candidate_email}\nSubject: {email_subject}\n"
        f"Session: {session_id}\nReason: {reason}\n{'='*55}\n"
    )
    return True, "Dev mock rejection email logged."
