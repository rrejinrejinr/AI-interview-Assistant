import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_service import _normalize_priority, generate_skill_gap_explanation, generate_learning_roadmap
from unittest.mock import patch

def test_normalize_priority_strings():
    assert _normalize_priority("High") == "High"
    assert _normalize_priority("HIGH") == "High"
    assert _normalize_priority("high priority") == "High"
    assert _normalize_priority("urgent") == "High"
    assert _normalize_priority("critical") == "High"
    assert _normalize_priority("P1") == "High"
    
    assert _normalize_priority("Medium") == "Medium"
    assert _normalize_priority("medium priority") == "Medium"
    assert _normalize_priority("P2") == "Medium"
    assert _normalize_priority("Normal") == "Medium"
    
    assert _normalize_priority("Low") == "Low"
    assert _normalize_priority("low priority") == "Low"
    assert _normalize_priority("minor") == "Low"
    assert _normalize_priority("P3") == "Low"

def test_normalize_priority_objects():
    assert _normalize_priority({"level": "High"}) == "High"
    assert _normalize_priority({"priority": "Medium"}) == "Medium"
    assert _normalize_priority({"value": "Low"}) == "Low"
    assert _normalize_priority({"urgency": "High"}) == "High"
    assert _normalize_priority({"name": "Critical"}) == "High"
    assert _normalize_priority({"custom": "High"}) == "High"

def test_normalize_priority_numbers_and_lists():
    assert _normalize_priority(1) == "High"
    assert _normalize_priority(2) == "Medium"
    assert _normalize_priority(3) == "Low"
    assert _normalize_priority(["High"]) == "High"
    assert _normalize_priority([{"priority": "Low"}]) == "Low"

def test_normalize_priority_fallbacks():
    assert _normalize_priority(None) == "Medium"
    assert _normalize_priority("") == "Medium"
    assert _normalize_priority({}) == "Medium"
    assert _normalize_priority([]) == "Medium"
    assert _normalize_priority("unexpected_value") == "Medium"

def test_generate_skill_gap_explanation_with_object_priority():
    mock_llm_json = (
        '{"gaps": ['
        '  {"skill": "Docker", "priority": {"level": "High"}, "why_it_matters": "Containerization", "topics_to_learn": ["Images", "Compose"], "interview_relevance": "Key topic"},'
        '  {"skill": "Kubernetes", "priority": 1, "why_it_matters": "Orchestration", "topics_to_learn": "Pods, Deployments", "interview_relevance": "Advanced topic"},'
        '  {"skill": "Redis", "priority": null, "why_it_matters": "Caching", "topics_to_learn": [], "interview_relevance": "System design"}'
        '], "summary": "Identified 3 skill gaps."}'
    )
    with patch("services.llm_service._call_llm_api", return_value=mock_llm_json):
        result = generate_skill_gap_explanation(
            current_skills=["Python", "FastAPI"],
            target_role="Backend Developer",
            missing_skills=["Docker", "Kubernetes", "Redis"]
        )
        assert result["source"] == "llm"
        assert len(result["gaps"]) == 3
        assert result["gaps"][0]["priority"] == "High"
        assert result["gaps"][1]["priority"] == "High"
        assert result["gaps"][2]["priority"] == "Medium"
        assert isinstance(result["gaps"][0]["priority"], str)
        assert isinstance(result["gaps"][1]["priority"], str)
        assert isinstance(result["gaps"][2]["priority"], str)

def test_generate_learning_roadmap_with_object_priority():
    mock_llm_json = (
        '{"target_role": "Backend Developer", "current_level": "Intermediate", "roadmap": ['
        '  {"step_number": 1, "skill": "Docker", "priority": {"priority": "High"}, "timeframe": "Weeks 1-2", "reason": "Basics", "learning_milestones": ["Containers"]},'
        '  {"step_number": 2, "skill": "Redis", "priority": 2, "timeframe": "Weeks 3-4", "reason": "Caching", "learning_milestones": ["Key-Value"]}'
        ']}'
    )
    with patch("services.llm_service._call_llm_api", return_value=mock_llm_json):
        result = generate_learning_roadmap(
            current_skills=["Python", "FastAPI"],
            target_role="Backend Developer",
            gaps=[{"skill": "Docker"}, {"skill": "Redis"}]
        )
        assert result["source"] == "llm"
        assert len(result["roadmap"]) == 2
        assert result["roadmap"][0]["priority"] == "High"
        assert result["roadmap"][1]["priority"] == "Medium"
        assert isinstance(result["roadmap"][0]["priority"], str)
        assert isinstance(result["roadmap"][1]["priority"], str)
