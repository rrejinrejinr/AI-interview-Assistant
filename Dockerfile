
# Production Dockerfile for AI Interview Assistant
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_PORT=8001

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and trained ML models
COPY backend/ /app/backend/
COPY trained_model/ /app/trained_model/

WORKDIR /app/backend

# Pre-ingest RAG knowledge base
RUN python -c "from rag.ingestion import ingest_knowledge_base; ingest_knowledge_base()" || true

# Default container port (Render supplies PORT at runtime)
EXPOSE 8001

# Health check using the runtime port
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8001}/api/health" || exit 1

# Start FastAPI on Render's assigned port
CMD sh -c 'export APP_PORT="${PORT:-8001}"; exec uvicorn app_fastapi:app --host 0.0.0.0 --port "$APP_PORT" --workers 2'
