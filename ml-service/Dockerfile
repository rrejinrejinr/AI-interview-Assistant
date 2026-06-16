FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8001

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8001}"]
