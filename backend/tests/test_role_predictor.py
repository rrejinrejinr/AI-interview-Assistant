"""
test_role_predictor.py
======================
Unit tests for backend/models/role_predictor.py.

Covers:
  1. Lazy loading behavior (model is not loaded on import).
  2. Successful prediction when model pipeline is available.
  3. Safe fallback when resume text is empty or whitespace.
  4. Safe fallback when pipeline model file is missing/unavailable.
  5. Safe handling when pipeline model file raises an error during unpickling/loading.
  6. Safe handling when model_pipeline.predict() raises an exception during inference.
  7. Fallback to legacy classifier when main pipeline is missing but legacy model is present.
  8. get_confidence_level categorization.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models.role_predictor as rp
from models.role_predictor import (
    predict_role,
    get_pipeline,
    reset_pipeline_cache,
    get_confidence_level,
)


@pytest.fixture(autouse=True)
def clean_pipeline_cache():
    """Ensure clean pipeline cache state before and after each test."""
    reset_pipeline_cache()
    yield
    reset_pipeline_cache()


# ---------------------------------------------------------------------------
# 1. Lazy Loading Verification
# ---------------------------------------------------------------------------

def test_lazy_loading_preserves_startup():
    """Verify the model pipeline is None after cache reset and not loaded eagerly."""
    reset_pipeline_cache()
    assert rp.pipeline is None
    assert rp._pipeline_loaded is False


# ---------------------------------------------------------------------------
# 2. Successful Prediction (Real or Mocked Pipeline)
# ---------------------------------------------------------------------------

def test_successful_role_prediction_with_mock():
    """Verify predict_role output schema and values when pipeline succeeds."""
    mock_pipe = MagicMock()
    mock_pipe.predict.return_value = ["Backend Developer"]
    mock_pipe.classes_ = ["Backend Developer", "Frontend Developer", "DevOps Engineer"]
    mock_pipe.predict_proba.return_value = [[0.75, 0.15, 0.10]]

    with patch.object(rp, "get_pipeline", return_value=mock_pipe):
        res = predict_role("Experienced Python, FastAPI, and PostgreSQL developer.")

        assert res["predicted_role"] == "Backend Developer"
        assert res["confidence_level"] == "High"
        assert len(res["top_predictions"]) == 3
        assert res["top_predictions"][0] == {"role": "Backend Developer", "probability": 0.75}
        assert res["top_predictions"][1] == {"role": "Frontend Developer", "probability": 0.15}


def test_successful_prediction_without_predict_proba():
    """Verify predict_role works even if pipeline lacks predict_proba."""
    mock_pipe = MagicMock(spec=["predict"])
    mock_pipe.predict.return_value = ["Data Scientist"]

    with patch.object(rp, "get_pipeline", return_value=mock_pipe):
        res = predict_role("Data Scientist with experience in PyTorch and Pandas.")

        assert res["predicted_role"] == "Data Scientist"
        assert res["confidence_level"] == "None"
        assert res["top_predictions"] == []


# ---------------------------------------------------------------------------
# 3. Empty or Whitespace-Only Resume Text
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("empty_input", ["", "   ", "\n\t\n", None])
def test_empty_resume_returns_default(empty_input):
    """Empty or whitespace text returns default fallback without calling pipeline."""
    with patch.object(rp, "get_pipeline") as mock_get_pipeline:
        res = predict_role(empty_input)
        assert res == {
            "predicted_role": "Software Engineer",
            "confidence_level": "None",
            "top_predictions": []
        }
        mock_get_pipeline.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Unavailable Model (File Not Found)
# ---------------------------------------------------------------------------

def test_unavailable_model_returns_safe_default():
    """When pipeline file and legacy files do not exist, returns safe default without crashing."""
    with patch("os.path.exists", return_value=False):
        res = predict_role("Software engineer with C++ knowledge.")

        assert res == {
            "predicted_role": "Software Engineer",
            "confidence_level": "None",
            "top_predictions": []
        }
        assert rp.pipeline is None


# ---------------------------------------------------------------------------
# 5. Model Loading Failure (Corrupted Pickle / Permission / Memory Error)
# ---------------------------------------------------------------------------

def test_model_loading_failure_handled_gracefully():
    """When pickle.load raises an exception, predict_role catches it and returns default."""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", MagicMock()), \
         patch("pickle.load", side_effect=Exception("Corrupted model file or unpickling error")):

        res = predict_role("Java Spring Boot Developer")

        assert res == {
            "predicted_role": "Software Engineer",
            "confidence_level": "None",
            "top_predictions": []
        }
        # Model should remain None and not crash
        assert rp.pipeline is None


def test_get_pipeline_catches_unpickling_exception():
    """Verify get_pipeline itself does not throw on pickle error."""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", MagicMock()), \
         patch("pickle.load", side_effect=OSError("Disk read error")):

        pipe = get_pipeline()
        assert pipe is None
        assert rp._pipeline_loaded is True


# ---------------------------------------------------------------------------
# 6. Inference Runtime Failure
# ---------------------------------------------------------------------------

def test_prediction_inference_error_handled_gracefully():
    """If model.predict() raises an exception during inference, safely falls back."""
    mock_pipe = MagicMock()
    mock_pipe.predict.side_effect = RuntimeError("Prediction inference matrix error")

    with patch.object(rp, "get_pipeline", return_value=mock_pipe), \
         patch("os.path.exists", return_value=False):

        res = predict_role("Software Engineer text")

        assert res == {
            "predicted_role": "Software Engineer",
            "confidence_level": "None",
            "top_predictions": []
        }


# ---------------------------------------------------------------------------
# 7. Fallback to Legacy Classifier
# ---------------------------------------------------------------------------

def test_fallback_to_legacy_classifier():
    """If main pipeline is None, but legacy classifier and tfidf exist, use them."""
    mock_clf = MagicMock()
    mock_clf.predict.return_value = ["DevOps Engineer"]

    mock_vec = MagicMock()
    mock_vec.transform.return_value = ["mock_vector"]

    def fake_exists(path):
        if path == rp.PIPELINE_PATH:
            return False
        if path in (rp.OLD_MODEL_PATH, rp.OLD_TFIDF_PATH):
            return True
        return False

    with patch.object(rp, "get_pipeline", return_value=None), \
         patch("os.path.exists", side_effect=fake_exists), \
         patch("builtins.open", MagicMock()), \
         patch("pickle.load", side_effect=[mock_clf, mock_vec]):

        res = predict_role("Docker Kubernetes CI/CD Ansible")

        assert res["predicted_role"] == "DevOps Engineer"
        assert res["confidence_level"] == "None"
        assert res["top_predictions"] == []


# ---------------------------------------------------------------------------
# 8. Confidence Level Function Tests
# ---------------------------------------------------------------------------

def test_get_confidence_level():
    """Verify confidence level tiers."""
    assert get_confidence_level(0.40, num_classes=25) == "High"
    assert get_confidence_level(0.16, num_classes=25) == "High"
    assert get_confidence_level(0.09, num_classes=25) == "Medium"
    assert get_confidence_level(0.02, num_classes=25) == "Low"
    # Zero / edge-case classes
    assert get_confidence_level(0.20, num_classes=0) == "High"
