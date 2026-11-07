"""
backend/rag/interview_knowledge.py — Curated Software Engineering & HR Interview Knowledge Dataset

Source & Attribution:
  - Curated Software Engineering & Behavioral Interview Question Corpus
  - Topics: General CS, System Architecture, Web Development, Backend, Databases, DevOps, HR/Behavioral
  - Usage: Retrieval & reference augmentation for adaptive HR interview follow-up generation and evaluation
  - License: Open / Educational Reference
"""

INTERVIEW_DATASET = [
    {
        "category": "HR & Behavioral",
        "role": "Software Engineer",
        "experience": "Fresher / Junior",
        "topic": "Project Ownership",
        "question": "Can you describe a key technical project you built, the specific modules you developed, and what architectural decisions you made?",
        "follow_ups": [
            "What was the most challenging technical roadblock you encountered and how did you resolve it?",
            "If you had to redesign that application for 10x higher traffic today, what would you change?",
            "How did you measure the success or performance of that project?"
        ]
    },
    {
        "category": "Technical Architecture",
        "role": "Backend Engineer",
        "experience": "Fresher / Junior",
        "topic": "FastAPI & Async APIs",
        "question": "How do you design RESTful API endpoints using FastAPI, and how do you handle asynchronous request execution?",
        "follow_ups": [
            "What validation mechanisms (such as Pydantic models) do you use to enforce strict data contracts?",
            "How do you manage dependency injection for database sessions and authentication middleware?",
            "How do you optimize endpoint response times for heavy payloads?"
        ]
    },
    {
        "category": "Technical Security",
        "role": "Full Stack Developer",
        "experience": "Fresher / Junior",
        "topic": "JWT Authentication",
        "question": "Why is JWT commonly chosen for stateless authentication, and how does the token lifecycle work?",
        "follow_ups": [
            "How do you handle token revocation, expiry, and refresh token rotation securely?",
            "Where should tokens be stored on the client side to mitigate XSS and CSRF risks?",
            "What encryption/signing algorithms do you use for secret verification?"
        ]
    },
    {
        "category": "Frontend Engineering",
        "role": "Frontend Developer",
        "experience": "Fresher / Junior",
        "topic": "React State & Lifecycle",
        "question": "How do you manage application state across components in React, and how does the Virtual DOM reconciliation work?",
        "follow_ups": [
            "When do you choose local component state (useState) versus global state (Context API / Redux)?",
            "How do you use useEffect dependency arrays to prevent infinite re-render loops?",
            "How do you profile and optimize component rendering bottlenecks?"
        ]
    },
    {
        "category": "Database Engineering",
        "role": "Backend / Full Stack",
        "experience": "Fresher / Junior",
        "topic": "PostgreSQL & Relational Design",
        "question": "How do you structure database schemas, foreign key relationships, and transactions in PostgreSQL?",
        "follow_ups": [
            "When would you create B-Tree versus GIN indexes on specific columns?",
            "How do you diagnose and resolve slow queries using EXPLAIN ANALYZE?",
            "How do ACID guarantees protect financial or transactional data?"
        ]
    },
    {
        "category": "DevOps & Cloud",
        "role": "Software Engineer",
        "experience": "Fresher / Junior",
        "topic": "Docker Containerization",
        "question": "What are the main advantages of containerizing applications with Docker compared to standard virtual machines?",
        "follow_ups": [
            "How do multi-stage Docker builds help minimize final container image sizes?",
            "How do you handle persistent storage and volumes across container restarts?",
            "How do you securely inject environment variables and API secrets into containers?"
        ]
    },
    {
        "category": "HR & Behavioral",
        "role": "Software Engineer",
        "experience": "Fresher / Junior",
        "topic": "Team Collaboration & Conflict Resolution",
        "question": "Can you tell me about a time you had a difference of opinion with a team member on a technical design or deadline?",
        "follow_ups": [
            "How did you communicate your reasoning and listen to their perspective?",
            "What compromise or final decision was reached, and what was the outcome?",
            "What did you learn from that experience about collaborative problem-solving?"
        ]
    }
]

def retrieve_relevant_interview_guidance(user_answer: str, candidate_role: str = "") -> list:
    """Retrieves matching interview guidance and potential follow-up angles from curated dataset."""
    ans_low = user_answer.lower()
    matches = []
    for item in INTERVIEW_DATASET:
        topic_words = item["topic"].lower().split()
        if any(tw in ans_low for tw in topic_words) or (candidate_role and candidate_role.lower() in item["role"].lower()):
            matches.append(item)
    return matches or INTERVIEW_DATASET[:2]
