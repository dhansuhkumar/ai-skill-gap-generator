
import sys
import os
import time
import pytest

# This is needed so that the test can find the `backend` module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_generator import generate_learning_path_for_skill
from backend.app.ai.router import _ensure_genai_configured

@pytest.fixture(autouse=True)
def ensure_genai_configured_for_tests():
    # Reset the configuration flag to ensure it runs for tests
    from backend.app.ai import router
    router._GENAI_CONFIGURED = False
    # The user must have GEMINI_API_KEY set in their environment
    _ensure_genai_configured()


def test_learning_path_generator_does_not_return_fallback():
    """
    Tests that the learning path generator returns a real response, not the fallback.
    This test requires a valid GEMINI_API_KEY to be set in the environment.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY is not set, skipping live API test.")

    skill = "React"
    result = generate_learning_path_for_skill(skill)
    time.sleep(5)  # Sleep to avoid hitting rate limits

    fallback = {
        "summary": f"Learn core concepts of {skill} and build a small project.",
        "steps": [
            f"Follow an introductory tutorial for {skill}",
            f"Build a tiny project using {skill}",
            "Refine by adding tests and reading official docs",
        ],
    }

    assert result != fallback, "The generator returned the fallback response. The API call might have failed."
    assert "summary" in result
    assert "steps" in result
    assert isinstance(result["summary"], str)
    assert isinstance(result["steps"], list)
    assert len(result["summary"]) > 0
    assert len(result["steps"]) > 0
