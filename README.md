# AI Interview Assistant

A full-stack application that analyzes resumes against job descriptions, extracts candidate details and skills using spaCy NLP, calculates ATS match scores via TF-IDF cosine similarity, and provides a mock interview question bank and interactive AI Coach (Claude Sonnet).

## Project Structure

- `ml-service/` — Python FastAPI microservice (port 8001) for text parsing and skill matching.
- `backend/` — Spring Boot 3.2 Java application (port 8080) for database persistence and client orchestration.
- `frontend/` — React + Vite web dashboard (port 5173) featuring dark mode aesthetics.

---

## Running the Application

There are two ways to run the complete stack: using Docker Compose (Recommended) or running each service locally.

### Method 1: Using Docker Compose (Single Command)

To build and run all 3 services together inside Docker containers, execute the following command in the root directory:

```bash
docker-compose up --build
```

- **React Frontend**: `http://localhost:5173` (Served by Nginx in production, mapped from port 80 in container)
- **Spring Boot Backend**: `http://localhost:8080`
- **FastAPI ML Service**: `http://localhost:8001`
- **H2 In-Memory DB Console**: `http://localhost:8080/h2-console` (JDBC URL: `jdbc:h2:mem:interviewdb`, Username: `sa`, Password: `[empty]`)

---

### Method 2: Running Locally

If running locally on your host machine, start each service in a separate terminal:

#### 1. Python FastAPI ML Service
Make sure you have Python 3.10+ installed.
```bash
cd ml-service
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app:app --reload --port 8001
```
- **Health Check**: `GET http://localhost:8001/health`

#### 2. Spring Boot Backend
Make sure you have Java 17+ installed.
```bash
cd backend
# On Linux/macOS
./mvnw spring-boot:run
# On Windows PowerShell
.\mvnw.cmd spring-boot:run
```
- **Health Check**: `GET http://localhost:8080/api/resume/health`

#### 3. React Frontend
Make sure you have Node.js (v18+) installed.
```bash
cd frontend
npm install
npm run dev
```
- **URL**: `http://localhost:5173`

---

## Features

1. **Upload Resume**: Supports PDF uploads (parsed via `pdfplumber`) and compares them against optional job descriptions.
2. **ATS Match Score**: Calculations are weighted 50/50 between:
   - **Semantic Fit**: Cosine similarity of TF-IDF vectors using a vectorizer trained on the Kaggle Resume Dataset.
   - **Skill Match Score**: Percent overlap of required skills.
3. **Candidate Information Extraction**: Automatically extracts email, phone, and years of experience using regexes.
4. **Skills Breakdown**: Categorizes candidate skills into Languages, Frameworks, Databases, Cloud & DevOps, ML/AI, and Tools.
5. **Interview Question Prep**: Displays 3+ technical questions per detected skill from a curated question bank.
6. **AI Coach (Claude)**: Chat interface that uses the candidate's detected skills as context. (Requires Anthropic API key, but includes a local simulator fallback if no key is entered).
7. **History**: Stores details of the last 10 analyzed resumes in H2 database.
