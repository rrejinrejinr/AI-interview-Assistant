# API Reference Documentation — AI Interview Assistant

Base URL: `http://localhost:8001/api` (or configured host)

All endpoints requiring authentication require a standard HTTP header:
```text
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Register a new candidate account and send an email verification OTP code.
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "securepassword123"
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "message": "Verification code sent to your email. Valid for 5 minutes."
  }
  ```

### `POST /api/auth/verify-otp`
Verify candidate's 6-digit OTP code.
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "otp": "123456"
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "message": "Email verified successfully. You may now log in."
  }
  ```

### `POST /api/auth/login`
Authenticate with email and password to receive a JWT access token.
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "securepassword123"
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "name": "Jane Doe",
      "email": "jane@example.com"
    }
  }
  ```

### `GET /api/auth/me`
Retrieve authenticated candidate profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response** `200 OK`:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
  ```

---

## 2. Resume & ATS Endpoints

### `POST /api/resume/upload`
Upload and analyze a resume file (PDF/DOCX, max 5MB).
- **Headers**: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
- **Body Form**: `resume`: File binary
- **Response** `200 OK`:
  ```json
  {
    "message": "Resume analyzed and indexed successfully.",
    "resume_id": 1,
    "filename": "Jane_Doe_Resume.pdf",
    "candidate_info": {
      "email": "jane@example.com",
      "phone": "+1-555-0199",
      "years_of_experience": "4 years"
    },
    "predicted_role": "Data Science",
    "confidence_level": "High",
    "top_predictions": [
      {"role": "Data Science", "probability": 0.72},
      {"role": "Python Developer", "probability": 0.18}
    ],
    "skills_list": ["Python", "Machine Learning", "FastAPI", "SQL"]
  }
  ```

### `POST /api/ats/analyze`
Analyze resume alignment with a target Job Description.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "resume_id": 1,
    "job_title": "Senior Data Scientist",
    "job_description": "We are seeking a Data Scientist experienced in Python, Machine Learning, Docker, and AWS."
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "ats_result_id": 1,
    "resume_id": 1,
    "job_title": "Senior Data Scientist",
    "ats_score": 75.0,
    "semantic_score": 50.0,
    "skill_match_score": 100.0,
    "matched_skills": ["Machine Learning", "Python"],
    "missing_skills": ["AWS", "Docker"],
    "semantic_weight": 0.5,
    "skill_weight": 0.5
  }
  ```

---

## 3. Mock Interview Endpoints

### `POST /api/interview/start`
Initialize a personalized mock interview session.
- **Request Body**:
  ```json
  {
    "resume_id": 1,
    "job_description": "Optional JD text...",
    "interview_type": "Technical",
    "difficulty": "Medium",
    "num_questions": 5
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "session_id": 10,
    "resume_id": 1,
    "predicted_role": "Data Science",
    "interview_type": "Technical",
    "difficulty": "Medium",
    "num_questions": 5,
    "status": "in_progress",
    "questions": [
      {
        "id": 101,
        "order_index": 0,
        "question": "Explain the bias-variance tradeoff in machine learning.",
        "question_type": "Technical",
        "category": "concept",
        "difficulty": "Medium"
      }
    ]
  }
  ```

### `POST /api/interview/{session_id}/answer`
Submit a candidate's answer for real-time scoring.
- **Request Body**:
  ```json
  {
    "question_id": 101,
    "user_answer": "High bias leads to underfitting while high variance leads to overfitting. Regularization helps control variance."
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "question_id": 101,
    "semantic_score": 88.5,
    "keyword_score": 80.0,
    "combined_score": 85.5,
    "feedback": "Strong answer covering fundamental trade-offs and regularization.",
    "matched_keywords": ["underfitting", "overfitting", "regularization"],
    "missing_keywords": ["L1/L2"],
    "answered_count": 1,
    "total_questions": 5,
    "is_last_question": false
  }
  ```

### `POST /api/interview/{session_id}/complete`
Finalize interview and generate performance summary report.
- **Response** `200 OK`:
  ```json
  {
    "session_id": 10,
    "status": "completed",
    "overall_score": 85.5,
    "avg_semantic_score": 88.5,
    "avg_keyword_score": 80.0,
    "strengths": ["Clear technical explanations", "Solid concept foundations"],
    "improvement_areas": ["Include specific quantitative project examples"],
    "completed_at": "2026-08-25T00:00:00Z"
  }
  ```

---

## 4. Career Recommendations & RAG Endpoints

### `POST /api/recommendations/analyze`
Analyze resume skill gaps against industry requirements and interview performance.
- **Request Body**:
  ```json
  {
    "resume_id": 1,
    "job_description_text": "Seeking ML Engineer with Docker, Kubernetes, AWS."
  }
  ```

### `GET /api/recommendations/roadmap?resume_id=1`
Fetch ordered milestone-based learning roadmap.

### `POST /api/resume/analyze`
Analyze resume for weak bullet points and missing measurable impact.

### `POST /api/rag/query`
Query the verified technical knowledge base.
- **Request Body**:
  ```json
  {
    "query": "What is the difference between containers and virtual machines in Docker?",
    "resume_id": 1
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "answer": "Virtual machines run full guest OS on top of a hypervisor...",
    "citations": ["cloud_docker_kubernetes.md"],
    "suggested_next_topics": ["Docker Compose", "Kubernetes Pods"],
    "retrieved_count": 3
  }
  ```
