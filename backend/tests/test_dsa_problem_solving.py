import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app_fastapi import app
from database import Base, get_db
from models_db import User, DsaTopic, DsaProblem, DsaProblemTopic, DsaUserProgress, DsaSubmission
from auth_utils import get_password_hash, create_access_token
from services.dsa_catalog import seed_dsa_catalog, DSA_TOPICS

from sqlalchemy.pool import StaticPool

# Use an in-memory SQLite database with StaticPool for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed DSA catalog in the test database
        seed_dsa_catalog(db)
        
        # Create a test user
        user = User(
            name="DSA Test Candidate",
            email="dsa_candidate@example.com",
            password_hash=get_password_hash("password123"),
            email_verified=True
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "dsa_candidate@example.com"})
    return {"Authorization": f"Bearer {token}"}

def test_all_20_dsa_topics_seeded(client):
    """Verify that all 20 requested DSA topics are seeded and returned."""
    res = client.get("/api/dsa/topics")
    assert res.status_code == 200
    topics = res.json()
    assert len(topics) == 20

    topic_names = [t["name"] for t in topics]
    required_topics = [
        "Arrays and Hashing",
        "Two Pointers",
        "Sliding Window",
        "Binary Search",
        "Strings",
        "Stack and Queue",
        "Linked List",
        "Recursion and Backtracking",
        "Trees and Binary Search Trees",
        "Heap and Priority Queue",
        "Graphs",
        "Dynamic Programming",
        "Greedy Algorithms",
        "Intervals",
        "Tries",
        "Union Find",
        "Bit Manipulation",
        "Math and Number Theory",
        "Advanced Graph Algorithms",
        "Segment Tree and Fenwick Tree"
    ]
    for req in required_topics:
        assert req in topic_names, f"Expected topic '{req}' was not found in catalog."

def test_filter_problems_by_topic_and_difficulty(client):
    """Test filtering problems by specific topic and difficulty."""
    # Filter by topic: Arrays and Hashing
    res = client.get("/api/dsa/problems?topic=arrays-and-hashing")
    assert res.status_code == 200
    data = res.json()
    assert "problems" in data
    assert len(data["problems"]) > 0
    for p in data["problems"]:
        assert "Arrays and Hashing" in p["topic_tags"] or "arrays-and-hashing" in [t.lower() for t in p["topic_tags"]]

    # Filter by difficulty: Easy
    res_easy = client.get("/api/dsa/problems?difficulty=Easy")
    assert res_easy.status_code == 200
    easy_data = res_easy.json()
    assert len(easy_data["problems"]) > 0
    for p in easy_data["problems"]:
        assert p["difficulty"] == "Easy"

def test_search_problems(client):
    """Test searching problems by keyword."""
    res = client.get("/api/dsa/problems?search=Two Sum")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    found = any("Two Sum" in p["title"] for p in data["problems"])
    assert found

def test_problem_detail_endpoint(client):
    """Test fetching problem detail by slug and numeric id."""
    res = client.get("/api/dsa/problems/two-sum")
    assert res.status_code == 200
    detail = res.json()
    assert detail["title"] == "Two Sum"
    assert detail["difficulty"] == "Easy"
    assert "leetcode.com" in detail["external_url"]
    assert "starter_code" in detail
    assert "python" in detail["starter_code"]
    assert "javascript" in detail["starter_code"]
    assert "java" in detail["starter_code"]
    assert "cpp" in detail["starter_code"]
    assert len(detail["examples"]) > 0
    assert len(detail["constraints"]) > 0

    # Also test numeric id
    num_id = detail["id"]
    res_id = client.get(f"/api/dsa/problems/{num_id}")
    assert res_id.status_code == 200
    assert res_id.json()["title"] == "Two Sum"

def test_user_progress_status_update(client, auth_headers):
    """Test updating user status (solved, attempted, unsolved) and unique tracking."""
    # Fetch two-sum problem
    res_p = client.get("/api/dsa/problems/two-sum")
    p_id = res_p.json()["id"]

    # Mark as solved
    res_solve = client.post(
        f"/api/dsa/problems/{p_id}/status",
        json={"status": "solved", "notes": "Completed optimal O(N) hash map solution"},
        headers=auth_headers
    )
    assert res_solve.status_code == 200
    solve_data = res_solve.json()
    assert solve_data["status"] == "solved"
    assert solve_data["solved_at"] is not None

    # Check progress API
    res_prog = client.get("/api/dsa/progress", headers=auth_headers)
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert prog["total_solved"] >= 1

    # Mark as unsolved
    res_unsolve = client.post(
        f"/api/dsa/problems/{p_id}/status",
        json={"status": "unsolved"},
        headers=auth_headers
    )
    assert res_unsolve.status_code == 200
    assert res_unsolve.json()["status"] == "unsolved"
    assert res_unsolve.json()["solved_at"] is None

def test_judge0_status_endpoint(client):
    """Check Judge0 health check endpoint returns valid JSON structure without crashing."""
    res = client.get("/api/dsa/judge0-status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data

def test_code_execution_handles_gracefully(client, auth_headers):
    """Test code execution endpoint handles requests safely even if Judge0 is offline."""
    res = client.post(
        "/api/dsa/problems/two-sum/execute",
        json={
            "code": "print('Hello DSA')",
            "language": "python",
            "stdin": ""
        },
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    # Either executed successfully (if local Judge0 is running) or returned clean service unavailable
    assert "success" in data
    if not data["success"]:
        assert data["error_type"] in ["SERVICE_UNAVAILABLE", "HTTP_ERROR", "EXECUTION_EXCEPTION"]
