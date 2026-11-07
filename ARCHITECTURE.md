# System Architecture & Technical Specifications

## 1. High-Level Architecture

The AI Interview Assistant is built on a modular, decoupled architecture separating client-side presentation, API services, deterministic machine learning, generative intelligence, and relational persistence.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              React Frontend                            │
│  [Overview Dashboard] [Resume & Skills] [ATS Analyzer] [Mock Interview] [AI Hub]
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Axios (Bearer JWT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Gateway                     │
│  • OAuth2 JWT Authentication Guards                                    │
│  • PII Redaction & Rate Limiting                                       │
│  • Global Safe Exception Handlers                                      │
└───────┬──────────────┬──────────────┬──────────────────┬───────────────┘
        │              │              │                  │
        ▼              ▼              ▼                  ▼
┌──────────────┐ ┌────────────┐ ┌──────────────┐ ┌───────────────────────┐
│ PostgreSQL DB│ │     ML     │ │ RAG & Vector │ │      LLM Service      │
│ • Users/OTPs │ │ • Role Clf │ │ • Knowledge  │ │ • Dynamic Questions   │
│ • Resumes    │ │ • ATS Sim  │ │ • Chunks     │ │ • Follow-Up Inquiries │
│ • Interviews │ │ • Skills   │ │ • MiniLM-L6  │ │ • Roadmap Synthesis   │
│ • Recs       │ │ • MiniLM   │ │ • Cosine Sim │ │ • Deterministic Fallbk│
└──────────────┘ └────────────┘ └──────────────┘ └───────────────────────┘
```

---

## 2. Component Directory Structure

```text
ai-interview-assistant/
├── backend/
│   ├── app_fastapi.py            # Primary production FastAPI service
│   ├── app.py                    # [LEGACY] Early Flask prototype
│   ├── auth_utils.py             # Bcrypt hashing, JWT management, OTP handling
│   ├── database.py               # SQLAlchemy database session engine
│   ├── models_db.py              # PostgreSQL database schemas
│   ├── models/
│   │   ├── ats_score.py          # 50/50 TF-IDF + Skill Match ATS algorithm
│   │   ├── interview_engine.py   # Question distribution & answer evaluation
│   │   ├── question_bank.py      # Curated technical & role question bank
│   │   ├── resume_parser.py      # PDF/DOCX parser & info extractor
│   │   ├── role_predictor.py     # Calibrated 25-class role prediction pipeline
│   │   └── skill_extractor.py    # 7-category regex & dictionary skill extractor
│   ├── rag/
│   │   ├── embeddings.py         # SentenceTransformer embedder wrapper
│   │   ├── ingestion.py          # Markdown chunking & indexing engine
│   │   ├── retriever.py          # Cosine similarity vector search
│   │   ├── vector_store.py       # Dense vector index with serialization
│   │   ├── rag_service.py        # Knowledge query synthesis service
│   │   └── knowledge_base/       # Public curated technical markdown documentation
│   └── services/
│       └── llm_service.py        # Configurable LLM provider & fallback manager
├── frontend/
│   ├── index.html                # Frontend HTML entry point with MediaPipe CDN
│   └── src/
│       ├── App.jsx               # Master 5-tab application controller
│       ├── components/
│       │   ├── Auth.jsx          # Register, Login & OTP Verification UI
│       │   ├── Dashboard.jsx     # Overview metrics & quick launch cards
│       │   ├── uploadcard.jsx    # Resume file upload & parsing trigger
│       │   ├── skillcard.jsx     # Extracted skills & calibrated role badge
│       │   ├── atscard.jsx       # ATS score gauge & skill match analysis
│       │   ├── InterviewSetup.jsx    # Mock interview configuration
│       │   ├── CameraVerification.jsx# MediaPipe pre-flight face check
│       │   ├── InterviewSession.jsx  # Live Q&A, PiP monitor & AI follow-up
│       │   ├── InterviewReport.jsx   # Interview report & performance metrics
│       │   └── Recommendations.jsx   # Skill gaps, roadmap, & RAG assistant
│       └── services/
│           └── api.js            # Axios client with JWT interceptor
├── trained_model/
│   ├── role_prediction_pipeline.pkl # Calibrated LogisticRegression classifier
│   └── ats_ranking_model.pkl        # ATS machine learning model
├── Dockerfile                    # Production container specification
├── docker-compose.yml            # Multi-container full-stack orchestration
├── DEPLOYMENT.md                 # Cloud deployment instructions
├── SECURITY.md                   # Security & privacy policy
└── .env.example                  # Environment configuration template
```
