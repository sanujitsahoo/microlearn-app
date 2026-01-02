"""
Pytest configuration file.
Sets up environment variables for testing to prevent import errors.
"""
import os
import pytest

# Set test environment variables before any imports
# This prevents the ValueError from being raised when main.py imports
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key_for_testing")
os.environ.setdefault("YOUTUBE_API_KEY", "test_youtube_key_for_testing")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173,https://gomicrolearn.vercel.app")

@pytest.fixture(autouse=True)
def reset_env():
    """Ensure test environment variables are set for each test."""
    yield
    # Cleanup if needed (not required for this case)

