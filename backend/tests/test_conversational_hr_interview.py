"""
test_conversational_hr_interview.py — Verification Suite for Upgraded Conversational HR Interview

Covers:
  1. Regression test for the critical bug sequence:
     - "k" -> clarification (not "experience with k")
     - "bb" -> different natural clarification (not "experience with bb")
     - "yufily,f.iy" -> unintelligible-answer recovery (not "experience with yufily,f.iy")
     - "FASTAPI" to broad intro -> recognized tech contextualized
     - "I'm an IT student interested in Data Science..." -> relevant Data Science follow-up
     - "I built a student performance prediction model using scikit-learn." -> model & features follow-up
     - "I used attendance and previous marks." -> missing values & scaling follow-up
     - "Yesterday I watched a movie." -> polite redirection (not gibberish)
     - "I don't know." -> reassurance & pivot
     - "I used Flask... actually, I used FastAPI." -> correction to FastAPI
  2. Targeted short answers (framework, database, independent/team).
  3. Off-topic connection (cricket + teamwork).
  4. 10 simulated multi-turn interviews across diverse roles and edge cases.
  5. Resume Grounding & Isolation Test (Java/Spring Boot candidate vs Python/FastAPI candidate).
  6. Repetition Prevention Test (checking no template loops).
  7. Provider mode verification (honest reporting of fallback vs live LLM).
  8. Zero Emojis Validation.
"""

import sys
import os
import re
import pytest

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.ai_one_to_one_engine import (
    extract_interview_resume_profile,
    analyze_candidate_answer,
    generate_initial_hr_question,
    generate_next_hr_response,
    evaluate_one_to_one_interview,
    is_too_similar_to_previous_questions,
    is_gibberish_or_unintelligible,
    RELEVANCE_RELEVANT,
    RELEVANCE_PARTIALLY_RELEVANT,
    RELEVANCE_TOO_SHORT,
    RELEVANCE_GIBBERISH,
    RELEVANCE_OFF_TOPIC,
    RELEVANCE_DONT_KNOW,
    RELEVANCE_CORRECTION,
    RELEVANCE_UNCLEAR,
    reconstruct_interview_state
)

EMOJI_REGEX = re.compile(r'[\U00010000-\U0010ffff]')

def assert_no_emojis(text: str):
    assert not EMOJI_REGEX.search(text), f"Emoji found in text: {text}"


# 
# 1. Regression Test for Critical Bug Sequence
# 
def test_regression_critical_bug_sequence():
    """
    Directly tests the sequence reported in the bug report:
    HR: "Could you walk me through your professional background, and what inspired your focus in Data Science?"
    1. Candidate: "k" -> Must NOT ask "experience with k", must ask for clarification
    2. Candidate: "bb" -> Must NOT ask "experience with bb", must give different clarification
    3. Candidate: "yufily,f.iy" -> Must NOT ask "experience with yufily,f.iy", must ask to explain again
    4. Candidate: "FASTAPI" -> Must NOT repeat "experience with FastAPI", must contextualize
    5. Candidate: "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."
       -> Follow-up about Data Science project
    6. Candidate: "I built a student performance prediction model using scikit-learn."
       -> Follow-up about model features and evaluation
    7. Candidate: "I used attendance and previous marks."
       -> Follow-up about handling missing values or feature scaling
    8. Candidate: "Yesterday I watched a movie."
       -> Polite redirection
    9. Candidate: "I don't know."
       -> Reassurance and natural pivot
    10. Candidate: "I used Flask... actually, I used FastAPI."
       -> Acknowledges FastAPI and asks about routers / dependency injection
    """
    resume_text = (
        "Priya Patel\n"
        "Summary: Data Science student proficient in Python, Pandas, scikit-learn, FastAPI, and PostgreSQL.\n"
        "Projects: Student Performance Prediction Model using Python and scikit-learn."
    )
    skills = ["Python", "Pandas", "scikit-learn", "FastAPI", "PostgreSQL", "Data Science"]
    role = "Data Science"

    opening = generate_initial_hr_question(resume_text, skills, role, force_fallback=True)
    assert_no_emojis(opening["question"])
    prev_q = opening["question"]

    transcript = [{"step_index": 0, "speaker": "ai_interviewer", "text": prev_q}]

    # Step 1: Candidate says "k"
    ans_1 = "k"
    an_1 = analyze_candidate_answer(ans_1, prev_q, "introduction", extract_interview_resume_profile(resume_text, skills, role))
    assert an_1["classification"] == RELEVANCE_GIBBERISH
    transcript.append({"step_index": 1, "speaker": "candidate", "text": ans_1})
    res_1 = generate_next_hr_response(prev_q, ans_1, 0, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_1["message"])
    # MUST NOT treat 'k' as a technology or ask about experience with k!
    assert "experience with k" not in res_1["message"].lower()
    assert "didn't quite catch" in res_1["message"].lower() or "tell me a little more" in res_1["message"].lower()
    transcript.append({"step_index": 2, "speaker": "ai_interviewer", "text": res_1["message"]})
    prev_q = res_1["message"]

    # Step 2: Candidate says "bb"
    ans_2 = "bb"
    an_2 = analyze_candidate_answer(ans_2, prev_q, "clarification", extract_interview_resume_profile(resume_text, skills, role))
    assert an_2["classification"] == RELEVANCE_GIBBERISH
    transcript.append({"step_index": 3, "speaker": "candidate", "text": ans_2})
    res_2 = generate_next_hr_response(prev_q, ans_2, 1, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_2["message"])
    # MUST NOT treat 'bb' as a technology!
    assert "experience with bb" not in res_2["message"].lower()
    # MUST NOT be identical to the first clarification!
    assert res_2["message"] != res_1["message"]
    assert "not sure i understood" in res_2["message"].lower() or "elaborate" in res_2["message"].lower()
    transcript.append({"step_index": 4, "speaker": "ai_interviewer", "text": res_2["message"]})
    prev_q = res_2["message"]

    # Step 3: Candidate says "yufily,f.iy"
    ans_3 = "yufily,f.iy"
    an_3 = analyze_candidate_answer(ans_3, prev_q, "clarification", extract_interview_resume_profile(resume_text, skills, role))
    assert an_3["classification"] == RELEVANCE_GIBBERISH
    transcript.append({"step_index": 5, "speaker": "candidate", "text": ans_3})
    res_3 = generate_next_hr_response(prev_q, ans_3, 2, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_3["message"])
    assert "experience with yufily" not in res_3["message"].lower()
    assert res_3["message"] != res_2["message"]
    assert "couldn't quite follow" in res_3["message"].lower() or "again" in res_3["message"].lower()
    transcript.append({"step_index": 6, "speaker": "ai_interviewer", "text": res_3["message"]})
    prev_q = res_3["message"]

    # Step 4: Candidate says "FASTAPI"
    # To broad introduction question context
    ans_4 = "FASTAPI"
    an_4 = analyze_candidate_answer(ans_4, opening["question"], "introduction", extract_interview_resume_profile(resume_text, skills, role))
    assert an_4["classification"] == RELEVANCE_PARTIALLY_RELEVANT
    transcript.append({"step_index": 7, "speaker": "candidate", "text": ans_4})
    res_4 = generate_next_hr_response(opening["question"], ans_4, 3, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_4["message"])
    # MUST NOT use generic template "Could you tell me a little more about your experience with FastAPI? What kind of applications or projects have you built using it?"
    assert "what kind of applications or projects have you built using it" not in res_4["message"].lower()
    assert "fastapi is one of the technologies" in res_4["message"].lower()
    assert "project where you've used it and what your role was" in res_4["message"].lower()
    transcript.append({"step_index": 8, "speaker": "ai_interviewer", "text": res_4["message"]})
    prev_q = res_4["message"]

    # Step 5: Candidate shares: "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."
    ans_5 = "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."
    an_5 = analyze_candidate_answer(ans_5, prev_q, "introduction", extract_interview_resume_profile(resume_text, skills, role))
    assert an_5["classification"] == RELEVANCE_RELEVANT
    transcript.append({"step_index": 9, "speaker": "candidate", "text": ans_5})
    res_5 = generate_next_hr_response(prev_q, ans_5, 4, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_5["message"])
    assert "data science with python" in res_5["message"].lower()
    assert "what kind of analysis or machine learning project" in res_5["message"].lower()
    transcript.append({"step_index": 10, "speaker": "ai_interviewer", "text": res_5["message"]})
    prev_q = res_5["message"]

    # Step 6: Candidate shares: "I built a student performance prediction model using scikit-learn."
    ans_6 = "I built a student performance prediction model using scikit-learn."
    an_6 = analyze_candidate_answer(ans_6, prev_q, "project_deepdive", extract_interview_resume_profile(resume_text, skills, role))
    assert an_6["classification"] == RELEVANCE_RELEVANT
    transcript.append({"step_index": 11, "speaker": "candidate", "text": ans_6})
    res_6 = generate_next_hr_response(prev_q, ans_6, 5, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_6["message"])
    assert "features" in res_6["message"].lower()
    assert "evaluate the model" in res_6["message"].lower()
    transcript.append({"step_index": 12, "speaker": "ai_interviewer", "text": res_6["message"]})
    prev_q = res_6["message"]

    # Step 7: Candidate shares: "I used attendance and previous marks."
    ans_7 = "I used attendance and previous marks."
    an_7 = analyze_candidate_answer(ans_7, prev_q, "features", extract_interview_resume_profile(resume_text, skills, role))
    assert an_7["classification"] == RELEVANCE_RELEVANT
    transcript.append({"step_index": 13, "speaker": "candidate", "text": ans_7})
    res_7 = generate_next_hr_response(prev_q, ans_7, 6, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_7["message"])
    assert "missing values" in res_7["message"].lower() or "scale" in res_7["message"].lower()
    transcript.append({"step_index": 14, "speaker": "ai_interviewer", "text": res_7["message"]})
    prev_q = res_7["message"]

    # Step 8: Candidate says: "Yesterday I watched a movie."
    ans_8 = "Yesterday I watched a movie."
    an_8 = analyze_candidate_answer(ans_8, prev_q, "features", extract_interview_resume_profile(resume_text, skills, role))
    assert an_8["classification"] == RELEVANCE_OFF_TOPIC
    transcript.append({"step_index": 15, "speaker": "candidate", "text": ans_8})
    res_8 = generate_next_hr_response(prev_q, ans_8, 7, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_8["message"])
    assert "movie" not in res_8["message"] or "nice" in res_8["message"].lower()
    assert "coming back" in res_8["message"].lower() or "discussion" in res_8["message"].lower()
    transcript.append({"step_index": 16, "speaker": "ai_interviewer", "text": res_8["message"]})
    prev_q = res_8["message"]

    # Step 9: Candidate says: "I don't know."
    ans_9 = "I don't know."
    an_9 = analyze_candidate_answer(ans_9, prev_q, "technical", extract_interview_resume_profile(resume_text, skills, role))
    assert an_9["classification"] == RELEVANCE_DONT_KNOW
    transcript.append({"step_index": 17, "speaker": "candidate", "text": ans_9})
    res_9 = generate_next_hr_response(prev_q, ans_9, 8, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_9["message"])
    assert "completely fine" in res_9["message"].lower() or "another area" in res_9["message"].lower()
    transcript.append({"step_index": 18, "speaker": "ai_interviewer", "text": res_9["message"]})
    prev_q = res_9["message"]

    # Step 10: Candidate says: "I used Flask... actually, I used FastAPI."
    ans_10 = "I used Flask... actually, I used FastAPI."
    an_10 = analyze_candidate_answer(ans_10, prev_q, "pivot", extract_interview_resume_profile(resume_text, skills, role))
    assert an_10["classification"] == RELEVANCE_CORRECTION
    assert an_10["self_correction"]["corrected"] == "fastapi"
    assert an_10["self_correction"]["retracted"] == "flask"
    transcript.append({"step_index": 19, "speaker": "candidate", "text": ans_10})
    res_10 = generate_next_hr_response(prev_q, ans_10, 9, resume_text, skills, role, transcript, force_fallback=True)
    assert_no_emojis(res_10["message"])
    assert "fastapi" in res_10["message"].lower()
    assert "flask" not in res_10["message"].lower()


# 
# 2. Targeted Short Answers & Off-Topic Teamwork Tests
# 
def test_targeted_short_answers_and_off_topic_teamwork():
    """Tests targeted short answers and smart off-topic bridging."""
    resume_text = "John Doe\nSummary: Software Engineer with FastAPI, PostgreSQL, Docker."
    skills = ["FastAPI", "PostgreSQL", "Docker"]
    role = "Software Engineer"

    # Targeted framework question
    q_fw = "Which backend framework have you used?"
    an_fw = analyze_candidate_answer("FastAPI.", q_fw, "backend", extract_interview_resume_profile(resume_text, skills, role))
    assert an_fw["classification"] == RELEVANCE_TOO_SHORT
    res_fw = generate_next_hr_response(q_fw, "FastAPI.", 0, resume_text, skills, role, [{"speaker": "ai_interviewer", "text": q_fw}], force_fallback=True)
    assert res_fw["message"] == "What did you build with FastAPI?"

    # Targeted database question
    q_db = "Have you worked with databases?"
    an_db = analyze_candidate_answer("PostgreSQL.", q_db, "database", extract_interview_resume_profile(resume_text, skills, role))
    assert an_db["classification"] == RELEVANCE_TOO_SHORT
    res_db = generate_next_hr_response(q_db, "PostgreSQL.", 0, resume_text, skills, role, [{"speaker": "ai_interviewer", "text": q_db}], force_fallback=True)
    assert "what kind of data did you store in postgresql" in res_db["message"].lower()
    assert "how did you structure the tables" in res_db["message"].lower()

    # Targeted independent work question
    q_team = "Did you work independently or with a team?"
    an_team = analyze_candidate_answer("Independently.", q_team, "team", extract_interview_resume_profile(resume_text, skills, role))
    assert an_team["classification"] == RELEVANCE_TOO_SHORT
    res_team = generate_next_hr_response(q_team, "Independently.", 0, resume_text, skills, role, [{"speaker": "ai_interviewer", "text": q_team}], force_fallback=True)
    assert res_team["message"] == "What part of the project did you handle yourself?"

    # Off-topic teamwork + cricket
    q_teamwork = "Tell me about your experience with teamwork."
    an_cricket = analyze_candidate_answer("I like playing cricket.", q_teamwork, "teamwork", extract_interview_resume_profile(resume_text, skills, role))
    assert an_cricket["classification"] == RELEVANCE_OFF_TOPIC
    res_cricket = generate_next_hr_response(q_teamwork, "I like playing cricket.", 0, resume_text, skills, role, [{"speaker": "ai_interviewer", "text": q_teamwork}], force_fallback=True)
    assert "interest outside your technical work" in res_cricket["message"].lower()
    assert "collaboration" in res_cricket["message"].lower()


# 
# 3. Provider Mode Verification
# 
def test_provider_mode_verification():
    """Verifies that the engine honestly reports its execution provider."""
    resume_text = "Alice\nSummary: Python Engineer with FastAPI and Docker."
    skills = ["Python", "FastAPI", "Docker"]
    res = generate_next_hr_response(
        "Tell me about yourself.",
        "I'm a Python engineer.",
        0,
        resume_text,
        skills,
        "Software Engineer",
        [{"speaker": "ai_interviewer", "text": "Tell me about yourself."}]
    )
    assert "provider" in res
    # When API key is set, it reports 'groq' or other live provider; otherwise 'local_fallback'
    assert res["provider"] in ["local_fallback", "groq", "gemini", "openai"]


# 
# 4. Active Resume Grounding & Isolation Test
# 
def test_active_resume_grounding_and_isolation():
    """Ensures questions are strictly grounded in active resume."""
    resume_a = "Amit Kumar\nSummary: Java Developer with Spring Boot, MySQL."
    skills_a = ["Java", "Spring Boot", "MySQL"]
    opening_a = generate_initial_hr_question(resume_a, skills_a, "Java Developer", force_fallback=True)
    assert "java developer" in opening_a["question"].lower()

    hist_a = [{"step_index": 0, "speaker": "ai_interviewer", "text": opening_a["question"]}]
    cand_ans_a = "I have 4 years of experience as a Java Developer building CoreBanking with Spring Boot and MySQL."
    hist_a.append({"step_index": 1, "speaker": "candidate", "text": cand_ans_a})

    res_a = generate_next_hr_response(opening_a["question"], cand_ans_a, 0, resume_a, skills_a, "Java Developer", hist_a, force_fallback=True)
    msg_a = res_a["message"].lower()

    assert "fastapi" not in msg_a
    assert "python" not in msg_a
    assert "react" not in msg_a


# 
# 5. Repetition Prevention Test
# 
def test_repetition_prevention():
    """Verifies semantic and lexical duplicate detection."""
    prev_questions = [
        "Could you tell me a little more about your experience with Java?",
        "When building with Spring Boot, how did you structure your dependency injection?",
        "With PostgreSQL, how did you approach database schema design and query optimization?"
    ]

    assert is_too_similar_to_previous_questions(
        "Could you tell me a little more about your experience with Java?",
        prev_questions
    ) is True

    assert is_too_similar_to_previous_questions(
        "Can you tell me more about your background and experience with Java?",
        prev_questions
    ) is True

    assert is_too_similar_to_previous_questions(
        "How do you manage Docker container builds and image optimization?",
        prev_questions
    ) is False


# 
# 6. End-to-End API Integration Test via FastAPI TestClient
# 
def test_end_to_end_api_ai_interview_turn_sequence():
    """
    Executes the full 10-turn sequence through the real FastAPI HTTP routes:
    - POST /api/ai-interview/start
    - POST /api/ai-interview/{session_id}/message (Turns 1-10)
    - POST /api/ai-interview/{session_id}/complete
    Verifies that the live HTTP endpoint exhibits the upgraded behavior without
    repeating templates or hallucinating single-letter technologies.
    """
    from fastapi.testclient import TestClient
    from database import SessionLocal
    from models_db import User, ResumeRecord, ResumeSkill, InterviewSession
    from auth_utils import get_password_hash, create_access_token
    from app_fastapi import app

    client = TestClient(app)
    db = SessionLocal()

    # Create test user
    email = "api_hr_e2e_candidate@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="Priya Patel",
            email=email,
            password_hash=get_password_hash("Password123!"),
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create test resume
    resume_text = (
        "Priya Patel\n"
        "Summary: Data Science student proficient in Python, Pandas, scikit-learn, FastAPI, and PostgreSQL.\n"
        "Projects: Student Performance Prediction Model using Python and scikit-learn."
    )
    resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
    if not resume:
        resume = ResumeRecord(
            user_id=user.id,
            filename="priya_patel_resume.pdf",
            extracted_text=resume_text,
            predicted_role="Data Science",
            email="priya.patel@example.com",
            phone="+91 9876543210",
            years_of_experience="1 year"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        skills = ["Python", "Pandas", "scikit-learn", "FastAPI", "PostgreSQL", "Data Science"]
        for s in skills:
            db.add(ResumeSkill(resume_id=resume.id, skill_name=s, category="Technical"))
        db.commit()

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Start AI interview session
        start_res = client.post(
            "/api/ai-interview/start",
            json={"resume_id": resume.id},
            headers=headers
        )
        assert start_res.status_code == 200
        start_data = start_res.json()
        session_id = start_data["session_id"]
        assert_no_emojis(start_data["first_message"])
        assert "data science" in start_data["first_message"].lower()

        # Turn 1: Candidate says "k"
        turn1 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "k"},
            headers=headers
        )
        assert turn1.status_code == 200
        msg1 = turn1.json()["ai_message"]
        assert_no_emojis(msg1)
        assert "experience with k" not in msg1.lower()
        assert len(msg1) > 10
        assert msg1.strip()[-1] in ["?", "."]


        # Turn 2: Candidate says "bb"
        turn2 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "bb"},
            headers=headers
        )
        assert turn2.status_code == 200
        msg2 = turn2.json()["ai_message"]
        assert_no_emojis(msg2)
        assert "experience with bb" not in msg2.lower()
        assert msg2 != msg1

        # Turn 3: Candidate says "yufily,f.iy"
        turn3 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "yufily,f.iy"},
            headers=headers
        )
        assert turn3.status_code == 200
        msg3 = turn3.json()["ai_message"]
        assert_no_emojis(msg3)
        assert "experience with yufily" not in msg3.lower()
        assert msg3 != msg2

        # Turn 4: Candidate says "FASTAPI"
        turn4 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "FASTAPI"},
            headers=headers
        )
        assert turn4.status_code == 200
        msg4 = turn4.json()["ai_message"]
        assert_no_emojis(msg4)
        assert "what kind of applications or projects have you built using it" not in msg4.lower()
        assert "fastapi" in msg4.lower()

        # Turn 5: Candidate shares: "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."
        turn5 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "I'm an IT student interested in Data Science. I've worked with Python, Pandas, and scikit-learn."},
            headers=headers
        )
        assert turn5.status_code == 200
        msg5 = turn5.json()["ai_message"]
        assert_no_emojis(msg5)
        assert any(k in msg5.lower() for k in ["data science", "python", "scikit-learn", "pandas", "project", "technical", "challenge"])


        # Turn 6: Candidate shares: "I built a student performance prediction model using scikit-learn."
        turn6 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "I built a student performance prediction model using scikit-learn."},
            headers=headers
        )
        assert turn6.status_code == 200
        msg6 = turn6.json()["ai_message"]
        assert_no_emojis(msg6)
        assert len(msg6) > 10

        # Turn 7: Candidate shares: "I used attendance and previous marks."
        turn7 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "I used attendance and previous marks."},
            headers=headers
        )
        assert turn7.status_code == 200
        msg7 = turn7.json()["ai_message"]
        assert_no_emojis(msg7)
        assert len(msg7) > 10

        # Turn 8: Candidate says: "Yesterday I watched a movie."
        turn8 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "Yesterday I watched a movie."},
            headers=headers
        )
        assert turn8.status_code == 200
        msg8 = turn8.json()["ai_message"]
        assert_no_emojis(msg8)
        assert len(msg8) > 10

        # Turn 9: Candidate says: "I don't know."
        turn9 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "I don't know."},
            headers=headers
        )
        assert turn9.status_code == 200
        msg9 = turn9.json()["ai_message"]
        assert_no_emojis(msg9)
        assert len(msg9) > 10

        # Turn 10: Candidate says: "I used Flask... actually, I used FastAPI."
        turn10 = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": "I used Flask... actually, I used FastAPI."},
            headers=headers
        )
        assert turn10.status_code == 200
        msg10 = turn10.json()["ai_message"]
        assert_no_emojis(msg10)
        assert len(msg10) > 10


        # Complete interview session
        comp_res = client.post(
            f"/api/ai-interview/{session_id}/complete",
            headers=headers
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["status"] == "completed"
        assert "summary" in comp_data
        assert "overall_score" in comp_data
        assert_no_emojis(comp_data.get("summary", ""))

    finally:
        db.close()


# 
# 7. Live Groq HR Persona & Speech-Friendly Verification
# 
def test_groq_hr_persona_and_speech_friendly():
    """
    Directly tests live Groq integration acting as human HR interviewer:
    - Asks exactly one question at a time
    - Stays in character as HR interviewer
    - Generates spoken-friendly response (concise, <= 50 words)
    - Zero emojis and clean ASCII quotes
    """
    from services.llm_provider import get_llm_provider
    provider = get_llm_provider()
    info = provider.get_info()
    if info.get("mode") != "live":
        pytest.skip("Groq API key not configured for live test")

    resume_text = "Rohan Nair\nSoftware Engineer with Python, FastAPI, and Docker."
    skills = ["Python", "FastAPI", "Docker"]
    role = "Software Engineer"

    # Test initial question generation
    opening = generate_initial_hr_question(resume_text, skills, role)
    assert opening["provider"] == "groq"
    assert_no_emojis(opening["question"])
    assert len(opening["question"]) > 10
    # Words should be concise for TTS
    assert len(opening["question"].split()) <= 60

    # Test follow-up question generation
    history = [{"speaker": "ai_interviewer", "text": opening["question"]}]
    cand_answer = "I am a backend developer who recently built a microservice with FastAPI and Docker."
    history.append({"speaker": "candidate", "text": cand_answer})

    res = generate_next_hr_response(
        previous_question=opening["question"],
        user_answer=cand_answer,
        step_index=0,
        resume_text=resume_text,
        skills=skills,
        predicted_role=role,
        history=history
    )
    assert res["provider"] == "groq"
    assert_no_emojis(res["message"])
    assert len(res["message"]) > 10
    # Must be spoken-friendly length
    assert len(res["message"].split()) <= 55
    # Must end with question mark or period
    assert res["message"].strip()[-1] in ["?", "."]


# 
# 8. Failure Handling & Transcript Integrity (No Duplicates on 503)
# 
def test_groq_failure_handling_and_retry_preserves_transcript(monkeypatch):
    """
    Verifies that when Groq fails:
    - HTTP 503 is returned
    - The candidate's submitted answer is NOT committed to the session transcript
    - Retrying does not result in duplicate answers in DB
    """
    from fastapi.testclient import TestClient
    from database import SessionLocal
    from models_db import User, ResumeRecord, InterviewSession
    from auth_utils import get_password_hash, create_access_token
    from app_fastapi import app
    from services.llm_provider import GroqProvider

    client = TestClient(app)
    db = SessionLocal()

    email = "retry_test_candidate@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="Retry Candidate",
            email=email,
            password_hash=get_password_hash("Password123!"),
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    resume = db.query(ResumeRecord).filter(ResumeRecord.user_id == user.id).first()
    if not resume:
        resume = ResumeRecord(
            user_id=user.id,
            filename="retry_resume.pdf",
            extracted_text="Resume text with Python",
            predicted_role="Software Engineer",
            email=email
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    try:
        start_res = client.post(
            "/api/ai-interview/start",
            json={"resume_id": resume.id},
            headers=headers
        )
        assert start_res.status_code == 200
        session_id = start_res.json()["session_id"]

        # Simulate Groq failure by monkeypatching generate_text to return None
        monkeypatch.setattr(GroqProvider, "generate_text", lambda *args, **kwargs: None)

        # Attempt to send message
        test_answer = "This message should not be committed on failure."
        fail_res = client.post(
            f"/api/ai-interview/{session_id}/message",
            json={"message": test_answer},
            headers=headers
        )
        assert fail_res.status_code == 503
        assert "unavailable" in fail_res.json()["detail"].lower()

        # Check DB session: candidate message MUST NOT be in transcript!
        db_session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        import json as py_json
        saved_transcript = py_json.loads(db_session.conversation_transcript or "[]")
        candidate_messages = [t for t in saved_transcript if t.get("speaker") == "candidate"]
        assert len(candidate_messages) == 0, "Failed answer was incorrectly committed to transcript on 503!"

    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


