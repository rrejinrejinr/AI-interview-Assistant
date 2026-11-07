import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models_db import User, SupportTicket
from auth_utils import get_password_hash, create_access_token, send_support_ticket_email
from app_fastapi import app

client = TestClient(app)


@pytest.fixture
def auth_header():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "support_test_user@example.com").first()
    if not user:
        user = User(
            name="Support Tester",
            email="support_test_user@example.com",
            password_hash=get_password_hash("TestPass123!"),
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_support_ticket_creation_and_reply_to_email():
    """
    Verify support ticket email composition, recipient, and Reply-To.

    The test mocks auth_utils._send_via_resend (the Resend primary path) so it
    succeeds without a live API key, then inspects the arguments passed to it.
    """
    ticket_payload = {
        "ticket_id": "TICK-TEST-999",
        "name": "John Doe",
        "email": "johndoe@example.com",
        "category": "ATS Analysis",
        "subject": "ATS score not calculating",
        "description": "The ATS score button is great, but I need assistance with keyword matching.",
        "created_at": "2026-11-04 12:00:00 UTC",
    }

    # Patch Resend as configured and intercept _send_via_resend
    with patch("auth_utils.RESEND_API_KEY", "re_test_key_mock"), \
         patch("auth_utils.RESEND_FROM_EMAIL", "noreply@test.example.com"), \
         patch("auth_utils._send_via_resend", return_value=(True, "Email sent successfully via Resend.")) as mock_resend:

        sent, msg_info = send_support_ticket_email(ticket_payload)

        assert sent is True, f"Expected sent=True, got: {msg_info}"
        assert "delivered" in msg_info.lower(), f"Unexpected status message: {msg_info}"
        assert mock_resend.called, "_send_via_resend was not called"

        call_kwargs = mock_resend.call_args[1]  # keyword args

        # Recipient
        assert call_kwargs["to_email"] == "ainterviewassistant@gmail.com"

        # Reply-To
        assert call_kwargs["reply_to"] == "johndoe@example.com"

        # Subject includes ticket ID and complaint marker
        assert "TICK-TEST-999" in call_kwargs["subject"]
        assert "New Support Complaint" in call_kwargs["subject"]

        # Body contains all key fields
        body = call_kwargs["text_body"]
        assert "John Doe" in body
        assert "johndoe@example.com" in body
        assert "ATS Analysis" in body
        assert "ATS score not calculating" in body
        assert "The ATS score button is great" in body


def test_support_ticket_smtp_fallback():
    """
    When Resend is NOT configured, verify the SMTP fallback path is used
    and the email message contains the correct recipient and Reply-To header.
    """
    ticket_payload = {
        "ticket_id": "TICK-SMTP-001",
        "name": "Jane Doe",
        "email": "janedoe@example.com",
        "category": "Login Issue",
        "subject": "Cannot log in",
        "description": "Password reset is not working.",
        "created_at": "2026-11-05 09:00:00 UTC",
    }

    with patch("auth_utils.RESEND_API_KEY", ""), \
         patch("auth_utils.RESEND_FROM_EMAIL", ""), \
         patch("auth_utils.SMTP_USERNAME", "test_smtp@gmail.com"), \
         patch("auth_utils.SMTP_PASSWORD", "mock_app_password_16ch"), \
         patch("smtplib.SMTP") as mock_smtp:

        mock_server = mock_smtp.return_value

        sent, msg_info = send_support_ticket_email(ticket_payload)

        assert sent is True, f"Expected sent=True, got: {msg_info}"
        assert mock_server.send_message.called, "smtplib.SMTP.send_message was not called"

        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "ainterviewassistant@gmail.com"
        assert sent_msg["Reply-To"] == "janedoe@example.com"
        assert "TICK-SMTP-001" in sent_msg["Subject"]

        payload = sent_msg.get_payload()
        assert "Jane Doe" in payload
        assert "Cannot log in" in payload


def test_support_ticket_api_endpoint(auth_header):
    """Verify /api/support/ticket endpoint persists ticket in DB and triggers notification."""
    with patch("app_fastapi.send_support_ticket_email", return_value=(True, "Delivered successfully")):
        payload = {
            "name": "Jane User",
            "email": "janeuser@example.com",
            "category": "Resume Upload",
            "subject": "PDF formatting query",
            "description": "Please check if two-column PDF resumes are supported.",
        }
        res = client.post("/api/support/ticket", json=payload, headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["ticket_id"].startswith("TICK-")
        assert data["status"] == "Open"
        assert data["email_dispatched"] is True

        # Check DB persistence
        db = SessionLocal()
        ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == data["ticket_id"]).first()
        assert ticket is not None
        assert ticket.name == "Jane User"
        assert ticket.email == "janeuser@example.com"
        assert ticket.category == "Resume Upload"
        assert ticket.subject == "PDF formatting query"
        db.close()
