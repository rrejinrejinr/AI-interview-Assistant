"""
test_resend_email_integration.py
=================================
Tests that verify the Resend email delivery integration in auth_utils.py.

All tests run fully offline — the Resend SDK and smtplib are mocked so no
real API key or SMTP credentials are needed.

Coverage:
  - send_otp_email via Resend (primary)
  - send_otp_email dev-mock fallback when no backend is configured
  - send_otp_email SMTP fallback when Resend is not configured
  - send_resume_pdf_email via Resend with PDF attachment
  - send_malpractice_rejection_email via Resend
  - get_smtp_status() returns Resend + SMTP fields (backward-compatible)
  - /api/auth/register endpoint triggers Resend send (mocked)
  - /api/auth/smtp-status health endpoint shape
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth_utils
from auth_utils import (
    send_otp_email,
    send_resume_pdf_email,
    send_malpractice_rejection_email,
    get_smtp_status,
    OTP_EXPIRE_MINUTES,
)
from fastapi.testclient import TestClient
from app_fastapi import app
from database import SessionLocal
from models_db import User, OtpRecord

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESEND_ENV = {
    "auth_utils.RESEND_API_KEY": "re_test_mock_key",
    "auth_utils.RESEND_FROM_EMAIL": "noreply@test.example.com",
}

NO_SMTP_ENV = {
    "auth_utils.SMTP_USERNAME": "",
    "auth_utils.SMTP_PASSWORD": "",
}


# ---------------------------------------------------------------------------
# 1. send_otp_email – Resend path
# ---------------------------------------------------------------------------

class TestSendOtpEmailResend:
    """OTP email is delivered via Resend when API key + sender are configured."""

    def test_resend_called_with_correct_params(self):
        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils._send_via_resend", return_value=(True, "Email sent successfully via Resend.")) as mock_send:

            success, msg = send_otp_email("candidate@example.com", "123456")

            assert success is True
            assert "sent" in msg.lower()
            mock_send.assert_called_once()
            kwargs = mock_send.call_args[1]
            assert kwargs["to_email"] == "candidate@example.com"
            assert "AI Interview Assistant" in kwargs["subject"]
            # OTP must appear in body text
            assert "123456" in kwargs["text_body"]
            # OTP expiry must be mentioned
            assert str(OTP_EXPIRE_MINUTES) in kwargs["text_body"]

    def test_resend_error_returns_false_in_production(self):
        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils.APP_ENV", "production"), \
             patch("auth_utils._send_via_resend", return_value=(False, "Resend delivery error: ResendError")):

            success, msg = send_otp_email("candidate@example.com", "999888")
            assert success is False
            assert "resend" in msg.lower() or "error" in msg.lower()

    def test_resend_error_dev_fallback_returns_true(self):
        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils.APP_ENV", "development"), \
             patch("auth_utils._send_via_resend", return_value=(False, "Resend delivery error: ResendError")):

            success, msg = send_otp_email("candidate@example.com", "111222")
            # Resend IS configured and returned False — dev fallback should NOT apply here;
            # _send_via_resend failure in Resend path is propagated directly.
            # (dev mock only applies when NO backend is configured)
            assert success is False


# ---------------------------------------------------------------------------
# 2. send_otp_email – SMTP fallback
# ---------------------------------------------------------------------------

class TestSendOtpEmailSmtpFallback:
    """When RESEND_API_KEY is absent, SMTP is used as fallback."""

    def test_smtp_used_when_resend_not_configured(self):
        with patch("auth_utils.RESEND_API_KEY", ""), \
             patch("auth_utils.RESEND_FROM_EMAIL", ""), \
             patch("auth_utils.SMTP_USERNAME", "smtp_user@gmail.com"), \
             patch("auth_utils.SMTP_PASSWORD", "smtp_app_password"), \
             patch("smtplib.SMTP") as mock_smtp:

            mock_server = mock_smtp.return_value
            success, msg = send_otp_email("candidate@example.com", "654321")

            assert success is True
            assert mock_server.send_message.called
            sent_msg = mock_server.send_message.call_args[0][0]
            assert sent_msg["To"] == "candidate@example.com"
            assert "OTP" in sent_msg["Subject"] or "Verification" in sent_msg["Subject"]


# ---------------------------------------------------------------------------
# 3. send_otp_email – dev-mock (no backend)
# ---------------------------------------------------------------------------

class TestSendOtpEmailDevMock:
    """When neither Resend nor SMTP is configured, dev-mode returns True."""

    def test_dev_mock_returns_true(self, capsys):
        with patch("auth_utils.RESEND_API_KEY", ""), \
             patch("auth_utils.RESEND_FROM_EMAIL", ""), \
             patch("auth_utils.SMTP_USERNAME", ""), \
             patch("auth_utils.SMTP_PASSWORD", ""), \
             patch("auth_utils.APP_ENV", "development"):

            success, msg = send_otp_email("dev@example.com", "000111")
            assert success is True
            assert "mock" in msg.lower() or "dev" in msg.lower()
            # OTP should appear in console output (dev only)
            captured = capsys.readouterr()
            assert "000111" in captured.out

    def test_production_no_backend_returns_false(self):
        with patch("auth_utils.RESEND_API_KEY", ""), \
             patch("auth_utils.RESEND_FROM_EMAIL", ""), \
             patch("auth_utils.SMTP_USERNAME", ""), \
             patch("auth_utils.SMTP_PASSWORD", ""), \
             patch("auth_utils.APP_ENV", "production"):

            success, msg = send_otp_email("prod@example.com", "777888")
            assert success is False
            assert "not configured" in msg.lower() or "delivery" in msg.lower()


# ---------------------------------------------------------------------------
# 4. send_resume_pdf_email – Resend path with attachment
# ---------------------------------------------------------------------------

class TestSendResumePdfEmailResend:

    def test_pdf_attachment_sent_via_resend(self):
        fake_pdf = b"%PDF-1.4 fake pdf bytes"
        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils._send_via_resend", return_value=(True, "Email sent successfully via Resend.")) as mock_send:

            success, msg = send_resume_pdf_email(
                to_email="user@example.com",
                candidate_name="Alice Smith",
                pdf_bytes=fake_pdf,
                filename="Alice_Smith_Resume.pdf",
                template_name="Modern",
            )

            assert success is True
            mock_send.assert_called_once()
            kwargs = mock_send.call_args[1]
            assert kwargs["to_email"] == "user@example.com"
            assert "Alice_Smith_Resume.pdf" in kwargs["subject"]
            # Attachment must be a list with one entry containing the PDF
            assert len(kwargs["attachments"]) == 1
            att = kwargs["attachments"][0]
            assert att["filename"] == "Alice_Smith_Resume.pdf"
            assert att["content_type"] == "application/pdf"
            # Content is a list of integers matching the PDF bytes
            assert att["content"] == list(fake_pdf)

    def test_missing_to_email_returns_false(self):
        success, msg = send_resume_pdf_email(
            to_email="",
            candidate_name="Bob",
            pdf_bytes=b"fake",
        )
        assert success is False
        assert "required" in msg.lower() or "address" in msg.lower()


# ---------------------------------------------------------------------------
# 5. send_malpractice_rejection_email – Resend path
# ---------------------------------------------------------------------------

class TestSendMalpracticeRejectionEmailResend:

    def test_rejection_email_sent_via_resend(self):
        session_data = {
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "session_id": "SESS-9999",
            "reason": "Multiple faces detected.",
            "questions_completed": 5,
            "total_questions": 30,
            "timestamp": "2026-11-07 10:00:00 UTC",
        }
        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils._send_via_resend", return_value=(True, "Email sent successfully via Resend.")) as mock_send:

            success, msg = send_malpractice_rejection_email(session_data)

            assert success is True
            mock_send.assert_called_once()
            kwargs = mock_send.call_args[1]
            assert kwargs["to_email"] == "charlie@example.com"
            assert "Integrity" in kwargs["subject"] or "Rejected" in kwargs["subject"]
            assert "SESS-9999" in kwargs["text_body"]
            assert "Charlie Brown" in kwargs["text_body"]
            assert "Multiple faces detected" in kwargs["text_body"]

    def test_missing_email_returns_false(self):
        success, msg = send_malpractice_rejection_email({"name": "Nobody", "email": ""})
        assert success is False
        assert "email" in msg.lower()


# ---------------------------------------------------------------------------
# 6. get_smtp_status() backward compatibility + new Resend fields
# ---------------------------------------------------------------------------

class TestGetSmtpStatus:

    def test_returns_resend_fields(self):
        with patch("auth_utils.RESEND_API_KEY", "re_test"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "from@test.com"):
            info = get_smtp_status()
            assert "resend_configured" in info
            assert info["resend_configured"] is True
            assert info["resend_from_email"] == "from@test.com"
            assert "active_backend" in info
            assert info["active_backend"] == "resend"

    def test_active_backend_smtp_when_resend_absent(self):
        with patch("auth_utils.RESEND_API_KEY", ""), \
             patch("auth_utils.RESEND_FROM_EMAIL", ""), \
             patch("auth_utils.SMTP_USERNAME", "user@gmail.com"), \
             patch("auth_utils.SMTP_PASSWORD", "apppass"):
            info = get_smtp_status()
            assert info["active_backend"] == "smtp"
            assert info["resend_configured"] is False

    def test_active_backend_none_when_nothing_configured(self):
        with patch("auth_utils.RESEND_API_KEY", ""), \
             patch("auth_utils.RESEND_FROM_EMAIL", ""), \
             patch("auth_utils.SMTP_USERNAME", ""), \
             patch("auth_utils.SMTP_PASSWORD", ""):
            info = get_smtp_status()
            assert info["active_backend"] == "none"

    def test_legacy_smtp_fields_still_present(self):
        """Old smtp_configured / smtp_server keys must still be present for backward compat."""
        info = get_smtp_status()
        for key in ("smtp_configured", "smtp_server", "smtp_port",
                    "smtp_username_configured", "smtp_password_configured", "sender_email"):
            assert key in info, f"Missing legacy key: {key}"


# ---------------------------------------------------------------------------
# 7. /api/auth/smtp-status endpoint
# ---------------------------------------------------------------------------

class TestSmtpStatusEndpoint:

    def test_endpoint_returns_200_and_resend_fields(self):
        with patch("auth_utils.RESEND_API_KEY", "re_test"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "from@test.com"):
            resp = client.get("/api/auth/smtp-status")
            assert resp.status_code == 200
            data = resp.json()
            assert "resend_configured" in data
            assert "active_backend" in data
            # Legacy fields still present
            assert "smtp_configured" in data


# ---------------------------------------------------------------------------
# 8. /api/auth/register endpoint – Resend triggered
# ---------------------------------------------------------------------------

class TestRegisterEndpointWithResend:

    def test_register_triggers_resend_send(self):
        """POST /api/auth/register should call _send_via_resend when Resend is configured."""
        import uuid
        test_email = f"resend_reg_test_{uuid.uuid4().hex[:8]}@example.com"

        db = SessionLocal()
        try:
            # Clean up any leftover from previous run
            existing = db.query(User).filter(User.email == test_email).first()
            if existing:
                db.delete(existing)
                db.commit()
        finally:
            db.close()

        with patch("auth_utils.RESEND_API_KEY", "re_test_mock_key"), \
             patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
             patch("auth_utils._send_via_resend", return_value=(True, "Email sent successfully via Resend.")) as mock_send:

            resp = client.post("/api/auth/register", json={
                "name": "Resend Tester",
                "email": test_email,
                "password": "SecurePass123!",
            })

            assert resp.status_code == 200, f"Register failed: {resp.text}"
            data = resp.json()
            assert "verification code" in data.get("message", "").lower() or "sent" in data.get("message", "").lower()
            # Resend path was used
            mock_send.assert_called_once()
            kwargs = mock_send.call_args[1]
            assert kwargs["to_email"] == test_email

        # Cleanup
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == test_email).first()
            if user:
                db.delete(user)
                db.commit()
        finally:
            db.close()
