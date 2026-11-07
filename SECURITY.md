# Security Policy & Architecture — AI Interview Assistant

This document outlines the security controls, data isolation guarantees, and privacy-preserving mechanisms implemented in the AI Interview Assistant.

---

## 1. Security Architecture & Threat Model

### 1.1 Authentication & Credential Protection
- **Password Hashing**: Direct `bcrypt` algorithm with salt rounds of 12. Plaintext passwords are never logged or stored.
- **JWT Authorization**: Cryptographically signed tokens (`HS256`) containing candidate subject claims and expiration boundaries.
- **OTP Hardening**:
  - 6-digit numeric codes generated via cryptographically secure random number generators (`random.SystemRandom`).
  - 5-minute strict expiration window (`OTP_EXPIRE_MINUTES = 5`).
  - Single-use consumption enforcement (`is_used = True`).
  - Attempt limitation (maximum 3 failed attempts per OTP code before lockout).
  - Rate limiting & cooldown (minimum 60-second cooldown between consecutive OTP requests).

### 1.2 User Data Isolation
- Every database query for resumes, ATS calculations, interview sessions, answers, and career recommendations extracts the candidate identifier directly from the authenticated JWT token (`current_user.id = Depends(get_current_user)`).
- `user_id` fields passed in request bodies are ignored.
- Access attempts to resources belonging to another user safely return HTTP `404 Not Found` without disclosing resource existence.

### 1.3 Prompt Injection Defense
- Candidate resumes, job descriptions, and mock interview answers are treated as **untrusted data**.
- All user text passed to LLM services is wrapped in `<untrusted_user_data>` and `<job_description>` XML encapsulation tags.
- System prompts instruct the model that content within these tags is user data and must not be interpreted as system instructions or prompt overrides.

### 1.4 PII & Privacy Redaction
- Before sending candidate text to third-party LLM providers, email addresses and phone numbers are scrubbed using regular expression sanitization (`strip_pii`).
- Public RAG Knowledge Base is strictly isolated from private user data. Candidate resumes are never added to the shared vector store.

### 1.5 Client-Side Computer Vision Privacy
- Camera face-presence verification runs **100% locally in the browser** using MediaPipe WebAssembly.
- **Zero camera video frames or photos are sent to the backend**.
- **No facial recognition, biometric templates, or face identification models** are implemented.

---

## 2. Reporting a Vulnerability

If you discover a potential security issue within this project, please report it responsibly by contacting the project maintainers directly rather than creating public issues.
