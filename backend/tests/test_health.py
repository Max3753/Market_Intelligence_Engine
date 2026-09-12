"""Smoke tests — health check endpoint."""

from conftest import get_test_client


def test_health_returns_200():
    """GET /health should return 200 with status ok."""
    client = get_test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
