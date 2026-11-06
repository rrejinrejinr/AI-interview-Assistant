"""
mock_interview_engine.py — Formal 30-Question Resume-Only Mock Interview Engine

Responsibilities:
  1. Generate exactly 30 questions derived ONLY from the candidate's extracted resume
     (skills, projects, experience, education, certifications, and predicted role).
  2. Scale questions accurately based on difficulty (Easy, Medium, Hard) across diverse
     cognitive styles (conceptual, practical, project deep-dive, troubleshooting, architecture).
  3. Provide internal traceability category for every question (skill, project, experience, role, education, technology).
  4. Never expose ideal answers or keywords in frontend responses.
  5. Calculate comprehensive 30-question report using sentence-transformers scoring.
"""

import re
import random
import logging
from typing import List, Dict, Optional, Any

from models.interview_engine import get_model, evaluate_answer
from models.question_bank import normalize_keyword

logger = logging.getLogger(__name__)

# Template patterns grouped by difficulty and question cognitive style
DIFFICULTY_TEMPLATES = {
    "Easy": [
        {
            "style": "conceptual",
            "template": "What is the core purpose and foundational architecture of {item}, and where does it fit in modern development?",
            "ideal": "The fundamental concept of {item} involves core principles such as modular design, clear abstraction boundaries, and efficient state handling to solve domain challenges.",
            "keywords": ["{item_lower}", "purpose", "fundamentals", "architecture", "concepts", "basics"],
        },
        {
            "style": "syntax_usage",
            "template": "In basic usage of {item}, what are the key syntax constructs, standard conventions, or built-in functions you rely on?",
            "ideal": "Standard usage of {item} relies on idiomatic syntax, clean naming conventions, proper variable scoping, and adhering to established community coding standards.",
            "keywords": ["{item_lower}", "syntax", "conventions", "idiomatic", "functions", "constructs"],
        },
        {
            "style": "data_structures",
            "template": "How does {item} handle data structures, typing, or memory allocation at a basic conceptual level?",
            "ideal": "{item} manages data using structured schemas, typed variables or references, and standard memory management or garbage collection to ensure stability.",
            "keywords": ["{item_lower}", "data structures", "memory", "typing", "primitives", "allocation"],
        },
        {
            "style": "tooling",
            "template": "What standard package managers, CLI tools, or development environments do you use when working with {item}?",
            "ideal": "Development with {item} leverages official package managers, linters, debuggers, and IDE tooling for fast feedback and consistent build configurations.",
            "keywords": ["{item_lower}", "tooling", "package manager", "cli", "environment", "debugging"],
        },
        {
            "style": "error_handling",
            "template": "How do you perform basic exception handling and input validation when writing code in {item}?",
            "ideal": "Exception handling in {item} is achieved via try/catch/except blocks, specific error types, defensive assertions, and structured input validation.",
            "keywords": ["{item_lower}", "exception", "validation", "error handling", "try-catch", "defensive"],
        }
    ],
    "Medium": [
        {
            "style": "practical_application",
            "template": "In your practical experience with {item}, how do you structure an end-to-end feature or service for clean separation of concerns?",
            "ideal": "A structured implementation uses layered architecture (controllers, services, repositories), dependency injection, clear interface boundaries, and automated unit testing.",
            "keywords": ["{item_lower}", "architecture", "separation of concerns", "services", "layers", "dependency injection"],
        },
        {
            "style": "scenario",
            "template": "Suppose an API or pipeline built with {item} begins experiencing intermittent timeouts under moderate traffic. How do you diagnose and resolve the issue?",
            "ideal": "Diagnosis involves analyzing structured logs and APM telemetry, identifying slow database queries or blocking I/O, adding connection pooling or caching, and profiling hot execution paths.",
            "keywords": ["{item_lower}", "debugging", "timeouts", "telemetry", "profiling", "caching", "bottlenecks"],
        },
        {
            "style": "integration",
            "template": "How do you integrate {item} with external databases, message queues, or RESTful microservices reliably?",
            "ideal": "Reliable integration utilizes robust connection pooling, exponential backoff retries with jitter, circuit breakers, and transactional guarantees to maintain consistency.",
            "keywords": ["{item_lower}", "database", "message queue", "microservices", "retries", "circuit breaker", "integration"],
        },
        {
            "style": "testing",
            "template": "What is your strategy for writing unit, integration, and mocking tests for components built with {item}?",
            "ideal": "Testing strategy employs pytest/jest mocks for external I/O, fixture factories, test databases in containers, and CI pipeline automation with code coverage metrics.",
            "keywords": ["{item_lower}", "unit testing", "integration testing", "mocking", "fixtures", "ci/cd", "coverage"],
        },
        {
            "style": "project_deepdive",
            "template": "Reflecting on your implementation of {item}, what technical trade-offs did you make between development speed and maintainability?",
            "ideal": "The trade-offs involved choosing proven libraries over custom implementations, establishing strict typing boundaries, and ensuring test coverage before rapid iteration.",
            "keywords": ["{item_lower}", "trade-offs", "maintainability", "development speed", "libraries", "refactoring"],
        }
    ],
    "Hard": [
        {
            "style": "scalability",
            "template": "When scaling {item} to handle hundreds of thousands of concurrent requests, how do you mitigate resource contention, lock contention, and memory leaks?",
            "ideal": "Scaling at high concurrency requires asynchronous non-blocking event loops, stateless horizontal scaling, connection pool tuning, lock-free data structures, and heap profiling to prevent leaks.",
            "keywords": ["{item_lower}", "concurrency", "scalability", "memory leaks", "resource contention", "horizontal scaling", "async"],
        },
        {
            "style": "architecture",
            "template": "Design a resilient, distributed system around {item} that guarantees high availability, fault tolerance, and eventual consistency across regions.",
            "ideal": "The architecture incorporates multi-region deployment, read-replicas, distributed caching with Redis cluster, event-driven choreography via Kafka, and idempotent consumer workers.",
            "keywords": ["{item_lower}", "distributed systems", "fault tolerance", "eventual consistency", "high availability", "kafka", "caching"],
        },
        {
            "style": "optimization",
            "template": "How do you profile low-level execution latency, CPU cycles, and garbage collection pressure in performance-critical code using {item}?",
            "ideal": "Low-level optimization involves using CPU flamegraphs, memory allocation profilers, eliminating unnecessary serialization/deserialization overhead, and using zero-copy buffers.",
            "keywords": ["{item_lower}", "profiling", "latency", "flamegraph", "garbage collection", "cpu", "optimization", "serialization"],
        },
        {
            "style": "security_hardening",
            "template": "How do you harden {item} in an enterprise production environment against zero-day vulnerabilities, SSRF, injection, and privilege escalation?",
            "ideal": "Hardening includes least-privilege RBAC, automated SAST/DAST container scans, mutual TLS, parameterized query enforcement, content security policies, and encrypted secret management.",
            "keywords": ["{item_lower}", "security", "hardening", "rbac", "injection", "tls", "secrets", "vulnerabilities"],
        },
        {
            "style": "edge_case_troubleshooting",
            "template": "Describe how you would troubleshoot a complex distributed deadlock, race condition, or memory corruption scenario in a high-throughput {item} deployment.",
            "ideal": "Troubleshooting entails reproducing in staging with stress harnesses, analyzing thread and heap dumps, reviewing lock acquisition orders, utilizing atomic operations, and validating with telemetry.",
            "keywords": ["{item_lower}", "deadlock", "race condition", "memory dump", "thread dump", "distributed", "telemetry"],
        }
    ]
}


def _extract_resume_elements(resume_text: str, skills: List[str], predicted_role: str) -> Dict[str, List[str]]:
    """
    Extracts actual verifiable elements from the resume text:
    skills, projects, work experience snippets, technologies, education, role.
    """
    elements = {
        "role": [predicted_role] if predicted_role else ["Software Engineer"],
        "skills": [s.strip() for s in skills if s.strip()],
        "projects": [],
        "experience": [],
        "technologies": [],
        "education": []
    }

    # Extract projects from text
    project_matches = re.findall(r'(?:Project|Built|Developed|Created|Engineered|Designed)\s*:?\s*([A-Za-z0-9\s\-_.,]{6,60})', resume_text, re.IGNORECASE)
    for p in project_matches:
        p_clean = p.strip().strip(':.,-')
        if len(p_clean) > 5 and p_clean not in elements["projects"]:
            elements["projects"].append(p_clean)

    # Extract experience responsibilities
    exp_matches = re.findall(r'(?:Experience|Worked at|Role|Position|Responsibilities|Led|Architected)\s*:?\s*([A-Za-z0-9\s\-_.,]{8,80})', resume_text, re.IGNORECASE)
    for exp in exp_matches:
        exp_clean = exp.strip().strip(':.,-')
        if len(exp_clean) > 8 and exp_clean not in elements["experience"]:
            elements["experience"].append(exp_clean)

    # Extract education / certifications
    edu_matches = re.findall(r'(?:Bachelor|Master|B\.S\.|M\.S\.|B\.Tech|Degree|University|College|Certified|AWS Certified)\s*([A-Za-z0-9\s\-_.,]{4,60})', resume_text, re.IGNORECASE)
    for edu in edu_matches:
        edu_clean = edu.strip().strip(':.,-')
        if len(edu_clean) > 4 and edu_clean not in elements["education"]:
            elements["education"].append(edu_clean)

    # Ensure technologies include skills
    elements["technologies"] = list(elements["skills"])

    return elements


def generate_mock_interview_30_questions(
    resume_text: str,
    skills: List[str],
    predicted_role: str = "",
    difficulty: str = "Medium"
) -> List[Dict[str, Any]]:
    """
    Generates EXACTLY 30 unique, resume-derived questions customized to the
    candidate's actual background, scaling cleanly by difficulty.
    Every question is tagged with internal source category and metadata.
    """
    diff_key = "Medium"
    if difficulty.lower() in ["easy", "medium", "hard"]:
        diff_key = difficulty.capitalize()

    templates = DIFFICULTY_TEMPLATES.get(diff_key, DIFFICULTY_TEMPLATES["Medium"])
    elements = _extract_resume_elements(resume_text, skills, predicted_role)

    # Compile item pool with category tags
    item_pool = []
    for s in elements["skills"]:
        item_pool.append({"item": s, "category": "skill", "type": "Technical"})
    for p in elements["projects"]:
        item_pool.append({"item": p, "category": "project", "type": "Technical"})
    for exp in elements["experience"]:
        item_pool.append({"item": exp, "category": "experience", "type": "Technical"})
    for edu in elements["education"]:
        item_pool.append({"item": edu, "category": "education", "type": "Technical"})
    for r in elements["role"]:
        item_pool.append({"item": r, "category": "role", "type": "Technical"})

    # Fallback to general skills if pool is small
    if not item_pool:
        item_pool = [
            {"item": predicted_role or "Software Engineering", "category": "role", "type": "Technical"},
            {"item": "Data Structures & Algorithms", "category": "technology", "type": "Technical"},
            {"item": "REST API Architecture", "category": "technology", "type": "Technical"},
            {"item": "Database Design & SQL", "category": "technology", "type": "Technical"},
            {"item": "System Testing & CI/CD", "category": "technology", "type": "Technical"}
        ]

    questions = []
    seen_texts = set()

    # Generate 30 questions by pairing resume items with diverse template styles
    q_index = 1
    template_idx = 0
    item_idx = 0

    while len(questions) < 30:
        current_item_meta = item_pool[item_idx % len(item_pool)]
        current_tmpl = templates[template_idx % len(templates)]

        item_name = current_item_meta["item"]
        category = current_item_meta["category"]
        q_type = current_item_meta["type"]

        q_text = current_tmpl["template"].format(
            item=item_name,
            item_lower=item_name.lower()
        )

        ideal_text = current_tmpl["ideal"].format(
            item=item_name,
            item_lower=item_name.lower()
        )

        kw_list = [
            k.format(item_lower=item_name.lower())
            for k in current_tmpl["keywords"]
        ]
        # Add the item itself
        for w in item_name.lower().split():
            if len(w) > 2 and w not in kw_list:
                kw_list.append(w)

        if q_text not in seen_texts:
            seen_texts.add(q_text)
            questions.append({
                "order_index": q_index,
                "question": q_text,
                "question_type": q_type,
                "category": category,
                "difficulty": diff_key,
                "source_element": item_name,
                "ideal_answer": ideal_text,
                "keywords": kw_list
            })
            q_index += 1

        # Advance indices
        template_idx += 1
        item_idx += 1

        # Safety break to avoid infinite loop
        if template_idx > 300:
            break

    # If still below 30 due to deduplication, fill remainder with targeted situational variations
    while len(questions) < 30:
        target_item = item_pool[len(questions) % len(item_pool)]["item"]
        target_cat = item_pool[len(questions) % len(item_pool)]["category"]
        extra_q = f"In a high-availability production environment, how do you troubleshoot edge-case failure scenarios when using {target_item}?"
        if extra_q in seen_texts:
            extra_q = f"What are the best practices for logging, metrics, and alerting around {target_item} implementations?"

        seen_texts.add(extra_q)
        questions.append({
            "order_index": len(questions) + 1,
            "question": extra_q,
            "question_type": "Technical",
            "category": target_cat,
            "difficulty": diff_key,
            "source_element": target_item,
            "ideal_answer": f"Best practices for {target_item} include structured logging, distributed tracing, automated health checks, and alerting thresholds.",
            "keywords": [target_item.lower(), "logging", "monitoring", "alerting", "metrics", "production"]
        })

    return questions[:30]


def evaluate_mock_question(
    question_text: str,
    category: str,
    question_type: str,
    ideal_answer: str,
    keywords: List[str],
    user_answer: str,
    resume_text: str = ""
) -> Dict[str, Any]:
    """
    Evaluates a candidate's answer for Mock Interview with question-type specific logic:
      - Factual / technical questions: evaluated against the expected technical answer + keywords.
      - Resume / project / behavioral questions: evaluated whether candidate's answer correctly
        addresses the important expected points and is consistent with the active resume context.
    Returns:
      semantic_score, keyword_score, combined_score, is_correct (bool), result_status ("Correct" | "Incorrect"), feedback
    """
    if not user_answer or not user_answer.strip() or len(user_answer.strip().split()) < 3:
        return {
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "combined_score": 0.0,
            "is_correct": False,
            "result_status": "Incorrect",
            "matched_keywords": [],
            "missing_keywords": keywords,
            "feedback": "No substantive answer provided. Please provide a relevant technical response."
        }

    # Base evaluation with sentence transformers + keywords
    base_eval = evaluate_answer(user_answer, ideal_answer, keywords)
    sem_score = base_eval.get("semantic_score", 0.0)
    kw_score = base_eval.get("keyword_score", 0.0)
    comb_score = base_eval.get("combined_score", 0.0)

    category_lower = (category or "").lower()
    user_ans_lower = user_answer.lower()

    if category_lower in ["project", "experience", "behavioral", "role"]:
        # Resume / project question evaluation:
        # Check if candidate mentions meaningful technical details, architecture, trade-offs, tools
        has_substantive_length = len(user_answer.split()) >= 10
        # Check relevance to resume / domain
        has_relevant_terms = any(kw.lower() in user_ans_lower for kw in keywords) or sem_score >= 38.0
        is_correct = has_substantive_length and (comb_score >= 42.0 or sem_score >= 40.0 or has_relevant_terms)
    else:
        # Factual / technical questions: evaluated against expected technical answer
        is_correct = comb_score >= 48.0 or (sem_score >= 48.0 and kw_score >= 25.0)

    return {
        "semantic_score": sem_score,
        "keyword_score": kw_score,
        "combined_score": comb_score,
        "is_correct": bool(is_correct),
        "result_status": "Correct" if is_correct else "Incorrect",
        "matched_keywords": base_eval.get("matched_keywords", []),
        "missing_keywords": base_eval.get("missing_keywords", []),
        "feedback": base_eval.get("feedback", "")
    }


def calculate_mock_interview_report(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes aggregate performance statistics for a completed 30-question Mock Interview.
    """
    total_q = len(answers)
    if not answers:
        return {
            "correct_count": 0,
            "total_questions": 30,
            "percentage": 0.0,
            "overall_score": 0.0,
            "avg_semantic_score": 0.0,
            "avg_keyword_score": 0.0,
            "strengths": ["No answers recorded during the session."],
            "improvement_areas": ["Attempt questions with substantive technical details and examples."],
            "questions_answered": 0
        }

    correct_count = sum(1 for a in answers if a.get("is_correct") is True or a.get("result_status") == "Correct" or a.get("combined_score", 0.0) >= 48.0)
    percentage = round((correct_count / (total_q if total_q > 0 else 30)) * 100, 1)

    sem_scores = [a.get("semantic_score", 0.0) for a in answers]
    kw_scores = [a.get("keyword_score", 0.0) for a in answers]
    comb_scores = [a.get("combined_score", 0.0) for a in answers]

    avg_sem = float(sum(sem_scores) / len(sem_scores)) if sem_scores else 0.0
    avg_kw = float(sum(kw_scores) / len(kw_scores)) if kw_scores else 0.0

    strengths = []
    improvements = []

    if correct_count >= 24:
        strengths.append("High technical precision across fundamental and resume-derived architecture questions.")
    elif correct_count >= 15:
        strengths.append("Adequate foundational grasp of core technical principles.")
    else:
        improvements.append("Strengthen conceptual explanations by elaborating on underlying architectures and mechanisms.")

    if avg_kw >= 50:
        strengths.append("Good mention of key technical tools, syntax, and framework components.")
    else:
        improvements.append("Incorporate more standardized technical keywords, data structure terms, and system metrics in your answers.")

    if not strengths:
        strengths.append("Completed formal 30-question technical screen.")
    if not improvements:
        improvements.append("Continue fine-tuning optimization discussions and distributed system design trade-offs.")

    return {
        "correct_count": correct_count,
        "total_questions": total_q if total_q >= 30 else 30,
        "percentage": percentage,
        "overall_score": percentage,
        "avg_semantic_score": round(avg_sem, 1),
        "avg_keyword_score": round(avg_kw, 1),
        "strengths": strengths,
        "improvement_areas": improvements,
        "questions_answered": len(answers)
    }

generate_mock_interview_questions = generate_mock_interview_30_questions
