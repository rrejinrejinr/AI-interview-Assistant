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
    """Verify support ticket email composition, recipient, and Reply-To header."""
    with patch("smtplib.SMTP") as mock_smtp, \
         patch("auth_utils.SMTP_USERNAME", "test_smtp_user@gmail.com"), \
         patch("auth_utils.SMTP_PASSWORD", "mock_app_password_16ch"):

        mock_server = mock_smtp.return_value

        # Test the email dispatcher directly with ticket_data dict
        ticket_payload = {
            "ticket_id": "TICK-TEST-999",
            "name": "John Doe",
            "email": "johndoe@example.com",
            "category": "ATS Analysis",
            "subject": "ATS score not calculating",
            "description": "The ATS score button is great, but I need assistance with keyword matching.",
            "created_at": "2026-11-04 12:00:00 UTC"
        }

        sent, msg_info = send_support_ticket_email(ticket_payload)

        assert sent is True
        assert "delivered" in msg_info.lower()
        assert mock_server.send_message.called
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "ainterviewassistant@gmail.com"
        assert sent_msg["Reply-To"] == "johndoe@example.com"
        # Email subject format: "New Support Complaint – TICK-XXXX"
        assert "TICK-TEST-999" in sent_msg["Subject"]
        assert "New Support Complaint" in sent_msg["Subject"]

        # Verify body contains complaint subject and details
        payload = sent_msg.get_payload()
        assert "John Doe" in payload
        assert "johndoe@example.com" in payload
        assert "ATS Analysis" in payload
        assert "ATS score not calculating" in payload  # complaint subject is in body
        assert "The ATS score button is great" in payload

def test_support_ticket_api_endpoint(auth_header):
    """Verify /api/support/ticket endpoint persists ticket in DB and triggers notification."""
    with patch("app_fastapi.send_support_ticket_email", return_value=(True, "Delivered successfully")):
        payload = {
            "name": "Jane User",
            "email": "janeuser@example.com",
            "category": "Resume Upload",
            "subject": "PDF formatting query",
            "description": "Please check if two-column PDF resumes are supported."
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
