import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_fastapi import app
from database import SessionLocal
from models_db import User, OtpRecord
from auth_utils import verify_password, get_password_hash

client = TestClient(app)

def test_existing_registered_user_login():
    """Test 1: Existing registered user can log in successfully and receive JWT token."""
    res = client.post(
        "/api/auth/login",
        json={"email": "rrejinrejin123@gmail.com", "password": "123456"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rrejinrejin123@gmail.com"
    assert data["user"]["name"] == "REJIN"
    # Verify CORS headers
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"

def test_login_incorrect_password():
    """Test 2: Incorrect password returns 401 with 'Incorrect email or password.'"""
    res = client.post(
        "/api/auth/login",
        json={"email": "rrejinrejin123@gmail.com", "password": "WrongPassword999!"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res.status_code == 401
    assert res.json().get("detail") == "Incorrect email or password."

def test_login_unknown_email():
    """Test 3: Unknown email returns 401 with 'Incorrect email or password.'"""
    res = client.post(
        "/api/auth/login",
        json={"email": "completely_unknown_user_9999@example.com", "password": "SomePassword123!"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res.status_code == 401
    assert res.json().get("detail") == "Incorrect email or password."

def test_new_registration_and_login_flow():
    """Test 4: Register new user, verify OTP, then login."""
    test_email = "pytest_candidate_flow@example.com"
    test_pwd = "CandidateSecret2026!"
    test_name = "Pytest Candidate"

    db = SessionLocal()
    try:
        # Clean up if exists from prior test
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Create user directly (simulating registration with verified OTP)
        new_user = User(
            name=test_name,
            email=test_email,
            password_hash=get_password_hash(test_pwd),
            email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Login with newly registered user
        login_res = client.post(
            "/api/auth/login",
            json={"email": test_email, "password": test_pwd},
            headers={"Origin": "http://localhost:5173"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        assert token is not None

        # Verify password verification uses bcrypt checkpw
        assert verify_password(test_pwd, new_user.password_hash) is True
        assert verify_password("WrongPassword!", new_user.password_hash) is False
    finally:
        # Clean up test user
        cleanup_u = db.query(User).filter(User.email == test_email).first()
        if cleanup_u:
            db.delete(cleanup_u)
            db.commit()
        db.close()

def test_browser_refresh_token_validation():
    """Test 5: Simulate browser refresh by calling /api/auth/me with Bearer token."""
    # First login to get a valid token
    login_res = client.post(
        "/api/auth/login",
        json={"email": "rrejinrejin123@gmail.com", "password": "123456"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Call /api/auth/me as App.jsx does on reload
    me_res = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Origin": "http://localhost:5173"
        }
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "rrejinrejin123@gmail.com"
    assert me_data["name"] == "REJIN"
    # Ensure CORS allows origin on refresh
    assert me_res.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_authenticated_protected_endpoints():
    """Test 6: Authenticated access to protected resume endpoints with token."""
    login_res = client.post(
        "/api/auth/login",
        json={"email": "rrejinrejin123@gmail.com", "password": "123456"}
    )
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Protected me endpoint
    r1 = client.get("/api/auth/me", headers=auth_headers)
    assert r1.status_code == 200

    # 2. Protected resumes list endpoint
    r2 = client.get("/api/resumes", headers=auth_headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    # 3. Request without token returns 401 Unauthorized
    r3 = client.get("/api/auth/me")
    assert r3.status_code == 401
