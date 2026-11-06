# Deployment Guide — AI Interview Assistant

This guide covers deploying the AI Interview Assistant to modern cloud platforms with production hardening.

---

## 1. Architecture Overview

- **Frontend**: React + Vite $\to$ Deploy to **Vercel** or **Netlify**.
- **Backend**: FastAPI (Python 3.11) $\to$ Deploy to **Render**, **Railway**, or **AWS ECS/EC2**.
- **Database**: Managed PostgreSQL $\to$ **Neon**, **Supabase**, or **Railway Postgres**.
- **Local Vectors**: Embedded with local SentenceTransformer models $\to$ Runs directly within backend container without external vector database costs.

---

## 2. Managed Database Setup (PostgreSQL)

1. Provision a PostgreSQL 15+ database instance (e.g. on [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com)).
2. Obtain the standard connection URI:
   ```text
   postgresql://user:password@ep-sample-123456.us-east-2.aws.neon.tech/interview_db?sslmode=require
   ```
3. Set this as `DATABASE_URL` in your backend environment variables.

---

## 3. Backend Deployment (Render / Railway)

### Option A: Deploy via Docker (Recommended)
1. Link your Git repository to **Render** or **Railway**.
2. Select **Docker** deployment mode using the included `Dockerfile`.
3. Configure the following Environment Variables in the service settings:

| Variable | Recommended Value | Notes |
|---|---|---|
| `APP_ENV` | `production` | Enables strict security and production logging |
| `DATABASE_URL` | `postgresql://...` | Your managed PostgreSQL connection URI |
| `JWT_SECRET_KEY` | `$(openssl rand -hex 32)` | 64-character random cryptographic secret |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Exact domain of your deployed frontend |
| `LLM_PROVIDER` | `openai` or `gemini` | Configurable LLM provider |
| `LLM_API_KEY` | `sk-...` | Your LLM provider API key |
| `LLM_MODEL` | `gpt-4o-mini` | Cost-effective, high-speed LLM model |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP host for email OTP verification |
| `SMTP_PORT` | `587` | TLS port |
| `SMTP_USERNAME` | `your-email@gmail.com` | SMTP account email |
| `SMTP_PASSWORD` | `your-app-password` | Gmail 16-character App Password |

### Option B: Deploy via Native Python
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `uvicorn backend.app_fastapi:app --host 0.0.0.0 --port $PORT --workers 2`

---

## 4. Frontend Deployment (Vercel)

1. Import the Git repository into **Vercel**.
2. Configure Root Directory: `ai-dashboard` (or `frontend`).
3. Set Environment Variable:
   - `VITE_API_URL`: `https://your-backend-api.onrender.com/api`
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Deploy!

---

## 5. Health Check & Smoke Test

Verify the deployment by requesting the public health check endpoint:

```bash
curl -f https://your-backend-api.onrender.com/api/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "service": "AI Interview Assistant API",
  "port": 8001,
  "database": "connected",
  "sentence_transformer": {
    "status": "loaded",
    "model": "all-MiniLM-L6-v2",
    "available": true
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "has_api_key": true,
    "mode": "live"
  }
}
```
