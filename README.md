# AI Interview Assistant

An AI-powered platform for resume analysis, ATS matching, technical mock interviews, career recommendations, and technical knowledge Q&A.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-0a7f5a?style=for-the-badge)](https://ai-interview-assistant-puce.vercel.app/)
[![Backend](https://img.shields.io/badge/API-Render-5f43e9?style=for-the-badge)](https://ai-interview-assistant-1-04fe.onrender.com/api/health)

**Live application:** https://ai-interview-assistant-puce.vercel.app/

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Run Locally](#run-locally)
- [Environment Configuration](#environment-configuration)
- [Tests](#tests)
- [Deployment](#deployment)
- [Email Delivery Note](#email-delivery-note)
- [Security and Privacy](#security-and-privacy)
- [Documentation](#documentation)

## Overview

AI Interview Assistant helps candidates prepare for technical roles by connecting resume analysis, job-description matching, mock interviews, and learning recommendations in one application.

The frontend is built with React and Vite. A FastAPI backend provides authenticated APIs, machine-learning workflows, database access, and integrations with external AI and code-execution services. PostgreSQL is used for the deployed database, with SQLite available for local development.

## Features

### Resume analysis
- Upload and parse PDF and DOCX resumes.
- Extract candidate details and technical skills.
- Predict a likely role across the project's supported role categories.
- Review extracted skills and resume analysis results.

### ATS matching
- Compare a resume with a target job description.
- Produce an explainable score using semantic text similarity and skill overlap (configured as a 50/50 combination).
- Show matched and missing skills to help candidates identify improvement areas.

### AI mock interviews
- Generate role- and skill-aware interview questions.
- Evaluate submitted answers and provide feedback.
- Produce an interview performance report.
- Offer interview flows with camera face-presence checks. Camera detection runs in the browser; the application does not send or store camera frames for this check.

### Career recommendations
- Identify skill gaps.
- Generate structured learning recommendations and milestone-based roadmaps.
- Provide resume improvement suggestions.

### AI Tech Bot (RAG)
- Answer technical questions using the project's curated Markdown knowledge base.
- Retrieve relevant passages using a lightweight TF-IDF index and cosine similarity.
- Use the configured LLM provider (Groq in the current production deployment) to compose responses with source references.
- Keep RAG retrieval lightweight for low-memory hosting; the RAG retrieval path does not need to load PyTorch or Sentence Transformers.

### Additional application modules
- Account registration, email OTP verification, and JWT-based login.
- User-scoped resume and interview data.
- Support tickets and support-related email notifications.
- DSA practice and code-submission services, with Judge0 integration where configured.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite 7, Axios, Lucide React |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL (deployed), SQLite (local development), SQLAlchemy |
| Machine learning / NLP | scikit-learn, spaCy, NumPy, pandas, sentence-transformers (used by interview-evaluation workflows) |
| RAG retrieval | TF-IDF, cosine similarity, curated Markdown knowledge base |
| LLM integration | Groq in the current deployment; provider layer also supports configured alternatives |
| Authentication | bcrypt password hashing, JWT access tokens, email OTP verification |
| Browser-based face check | MediaPipe Face Detection / WebAssembly |
| Email | Resend API with SMTP fallback |
| Code execution | Judge0 service integration |

## Architecture

```text
                         React + Vite frontend
                                  |
                            HTTPS / Axios
                                  |
                           FastAPI backend
                                  |
           +----------------------+----------------------+
           |                      |                      |
      Authentication         Application APIs       AI services
      JWT + OTP              Resume / ATS            LLM provider
           |                 Interviews              RAG / TF-IDF
           |                 Career plans             Role prediction
           |                 Support / DSA
           |
      PostgreSQL (production) / SQLite (local)
```

The AI Tech Bot uses TF-IDF retrieval over the curated knowledge base before sending the retrieved context to the configured LLM provider. Other machine-learning workflows, such as interview answer evaluation, have their own model dependencies.

## Repository Structure

```text
AI-interview-Assistant/
├── backend/
│   ├── app_fastapi.py          # FastAPI application and API routes
│   ├── auth_utils.py            # Authentication, OTP, and email delivery
│   ├── database.py              # SQLAlchemy database configuration
│   ├── models_db.py              # Database models
│   ├── models/                  # Resume, ATS, role, and interview models
│   ├── rag/                     # Knowledge ingestion, TF-IDF store, retrieval
│   │   └── knowledge_base/      # Curated technical Markdown files
│   ├── services/                # LLM, Judge0, and supporting services
│   ├── tests/                   # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React application components
│   │   └── services/            # API client
│   └── package.json
├── trained_model/                # Trained model artifacts
├── Dockerfile
├── docker-compose.yml
├── ARCHITECTURE.md
├── API_DOCUMENTATION.md
├── DEPLOYMENT.md
├── SECURITY.md
└── README.md
```

## Run Locally

### Prerequisites

- Python 3.11
- Node.js 18 or later
- npm
- A database: SQLite for a quick local setup, or PostgreSQL
- An API key for the LLM provider you choose (Groq is used in the current deployment)

### 1. Clone the repository

```bash
git clone https://github.com/rrejinrejinr/AI-interview-Assistant.git
cd AI-interview-Assistant
```

### 2. Set up the backend

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

**macOS / Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Edit `backend/.env` and add or set the following local values:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./app.db
JWT_SECRET_KEY=replace_with_a_long_random_secret
CORS_ORIGINS=http://localhost:5173
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Keep real credentials in your local environment file only. Do not commit `backend/.env`.

Start the backend from the `backend` directory:

```bash
cd backend
python -m uvicorn app_fastapi:app --host 127.0.0.1 --port 8001 --reload
```

The API will be available at `http://127.0.0.1:8001`. FastAPI's interactive API documentation is at `http://127.0.0.1:8001/docs`.

### 3. Set up the frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm install
```

Create `frontend/.env` with the local backend URL:

```dotenv
VITE_API_URL=http://127.0.0.1:8001/api
```

Start the Vite development server:

```bash
npm run dev
```

Open the local frontend URL printed by Vite (normally `http://localhost:5173`).

## Environment Configuration

Configure only the integrations you intend to use. The backend environment template is `backend/.env.example`.

| Variable | Purpose |
|---|---|
| `APP_ENV` | Application environment, such as `development` or `production` |
| `DATABASE_URL` | Database connection string |
| `JWT_SECRET_KEY` | Secret used to sign access tokens |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `LLM_PROVIDER` | Selects the configured LLM provider |
| `GROQ_API_KEY`, `GROQ_MODEL` | Groq credentials and model when Groq is selected |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Resend email delivery |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | SMTP fallback settings |
| `SUPPORT_RECEIVER_EMAIL` | Destination for support notifications |
| `JUDGE0_URL` | Judge0 service URL, if code execution is enabled |

Never put API keys, passwords, database credentials, JWT secrets, OAuth tokens, or other secrets in source code, the README, screenshots, or Git commits.

## Tests

Run tests from the repository root after installing backend dependencies:

```bash
python -m pytest backend/tests -v
```

You can also run focused test groups:

```bash
python -m pytest backend/tests/test_rag_lightweight.py -v
python -m pytest backend/tests/test_role_predictor.py -v
python -m pytest backend/tests/test_resend_email_integration.py backend/tests/test_support_ticket_email.py -v
```

## Deployment

### Live services

| Service | URL |
|---|---|
| Frontend | [ai-interview-assistant-puce.vercel.app](https://ai-interview-assistant-puce.vercel.app/) |
| Backend health | [Render API health check](https://ai-interview-assistant-1-04fe.onrender.com/api/health) |
| Backend API docs | [FastAPI Swagger UI](https://ai-interview-assistant-1-04fe.onrender.com/docs) |

### Frontend — Vercel

The production frontend is deployed on Vercel.

- **Root directory:** `frontend`
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Environment variable:** `VITE_API_URL=https://ai-interview-assistant-1-04fe.onrender.com/api`

### Backend — Render

The backend is deployed on Render using the repository's `Dockerfile`. Configure production values in the Render service environment:

- `APP_ENV=production`
- `DATABASE_URL` — managed PostgreSQL connection string
- `JWT_SECRET_KEY` — strong, unique secret
- `CORS_ORIGINS` — the exact deployed Vercel origin
- LLM provider credentials and model settings
- Email provider settings

The Dockerfile starts Uvicorn with one worker and uses Render's assigned `PORT` when available. Check the Render service logs and the health endpoint after deployment.

## Email Delivery Note

The application currently uses the Resend API as its primary email delivery path and retains SMTP as a fallback.

For local or production deployments, set `RESEND_API_KEY` and `RESEND_FROM_EMAIL`. Resend's shared testing sender, `onboarding@resend.dev`, is restricted to the Resend account owner's recipient address. To send verification codes and notifications to arbitrary users, configure and verify a domain in Resend and use a sender address on that verified domain.

The current live deployment is configured with the Resend testing sender, so email registration for other recipients is restricted until a production sender is configured. Do not assume that successful login with an existing account means email delivery is available to every new user.

## Security and Privacy

- Passwords are hashed with bcrypt; authenticated API access uses signed JWTs.
- Email OTPs are time-limited and single-use, with verification-attempt limits and resend cooldowns.
- User-specific resume and interview records are scoped to the authenticated user.
- Camera face-presence verification runs in the browser. Camera frames are not sent to the backend for this check.
- Resume and job-description content is treated as untrusted input when used by AI services. Review the [Security Policy](SECURITY.md) before production use.

## Documentation

- [System Architecture](ARCHITECTURE.md)
- [API Reference](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Policy](SECURITY.md)
