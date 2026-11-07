# 🤖 AI Interview Assistant

An end-to-end, privacy-preserving AI assistant for resume screening, ATS optimization, face-monitored technical mock interviews, and personalized career roadmaps.

---

## 🌟 Key Features

1. **📄 Intelligent Resume Parsing & Skill Extraction**:
   - Parses PDF and DOCX files.
   - Extracts candidate contact information, years of experience, and categorized skills across 7 technical categories.

2. **🎯 Calibrated Role Prediction**:
   - Predicts job category across 25 roles using a calibrated machine learning pipeline (`TF-IDF + LogisticRegression + Sigmoid Calibration`).
   - Delivers reliable confidence levels (`High`, `Medium`, `Low`) and top-3 probability distributions.

3. **📊 Explainable ATS Scoring**:
   - Dual-engine ATS formula combining 50% semantic cosine similarity and 50% canonical skill overlap.
   - Highlights matched vs missing keywords and skills without obscure black-box scoring.

4. **🔒 Secure Authentication & Data Isolation**:
   - Candidate registration with 6-digit numeric email OTP verification.
   - Password security with `bcrypt` (12 rounds) and `HS256` signed JWT bearer tokens.
   - Strict per-user data isolation across resumes, interviews, and recommendations.

5. **🎤 Personalized AI Mock Interview**:
   - Generates interview questions tailored to the candidate's actual extracted resume skills and target role.
   - Evaluates candidate answers in real time using dense vector embeddings (`SentenceTransformer all-MiniLM-L6-v2`) and keyword coverage metrics.
   - Dynamic conversational follow-up questions powered by configurable LLM integration.

6. **📷 Client-Side Camera & Face Presence Verification**:
   - Validates candidate physical presence before and during mock interviews using MediaPipe Face Detection in WebAssembly.
   - **Privacy Guarantee**: Zero video frames or photos are stored or sent to the backend. No biometric facial recognition or identity database matching.

7. **🚀 AI Career Hub, Skill Gaps & RAG Knowledge Assistant**:
   - Analyzes skill gaps and constructs structured milestone learning roadmaps.
   - Actionable resume improvement suggestions for measurable impact metrics.
   - Local RAG technical assistant querying curated technical documentation across Python, ML, Backend, Cloud/DevOps, SQL, and System Design.

---

## 🛠️ Technology Stack

- **Frontend**: React, Modern Component Architecture, MediaPipe Face Detection (WASM), Axios.
- **Backend**: FastAPI (Python 3.11), Uvicorn, Pydantic, SQLAlchemy ORM.
- **Database**: PostgreSQL (Production) / SQLite (Development).
- **Machine Learning**: `scikit-learn`, `sentence-transformers`, `spaCy`, `numpy`, `pandas`.
- **Authentication**: JWT (`python-jose`), `bcrypt`, SMTP Email Verification.
- **AI & RAG**: Configurable LLM Service (`OpenAI`, `Gemini`, `OpenRouter`, `Mock`), Local Dense Vector Store (Cosine Similarity).

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL (or local SQLite)

### 2. Environment Setup
Copy the environment template:
```bash
cp .env.example .env
```
Edit `.env` with your database and security settings.

### 3. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app_fastapi:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Running Tests
Run the comprehensive end-to-end regression and security test suite:
```bash
python run_phase9_final_tests.py
```

---

## 📖 Documentation
- [System Architecture (ARCHITECTURE.md)](ARCHITECTURE.md)
- [API Reference (API_DOCUMENTATION.md)](API_DOCUMENTATION.md)
- [Deployment Guide (DEPLOYMENT.md)](DEPLOYMENT.md)
- [Security & Privacy (SECURITY.md)](SECURITY.md)
- [Final Audit Report (FINAL_AUDIT_REPORT.md)](FINAL_AUDIT_REPORT.md)
