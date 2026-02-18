"""
Tests for system endpoints (health check, root).
"""

import pytest


def test_health_check(test_client):
    """Test the health check endpoint returns 200 OK."""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "environment" in data


def test_root_endpoint(test_client):
    """Test the root endpoint returns API information."""
    response = test_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
