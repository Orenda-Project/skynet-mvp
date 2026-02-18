"""
Pytest configuration and fixtures for testing.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI app.
    This fixture can be used by all tests.
    """
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """
    Mock settings for testing.
    Prevents loading from actual .env file during tests.
    """
    from src.config import Settings
    return Settings(
        environment="test",
        debug=True,
        postgres_url="sqlite:///:memory:",  # In-memory SQLite for tests
        openai_api_key="test_key",
        smtp_password="test_password"
    )
